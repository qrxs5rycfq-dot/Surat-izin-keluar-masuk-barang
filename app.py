import io
import json
import os
import uuid
from datetime import datetime, date
from functools import wraps

import bcrypt
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, jsonify, g, abort,
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user,
)
from werkzeug.utils import secure_filename

from config import Config
from db import get_db, init_db

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login terlebih dahulu.'
login_manager.login_message_category = 'warning'

ALLOWED_EXT = Config.ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*a, **kw):
            if current_user.role not in roles:
                abort(403)
            return f(*a, **kw)
        return wrapper
    return decorator


def _q(conn, sql, params=None, one=False):
    """Execute a query and return results as list of dicts (or single dict)."""
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        if one:
            return cur.fetchone()
        return cur.fetchall()


def _exec(conn, sql, params=None):
    """Execute a write query, commit, and return lastrowid."""
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
    conn.commit()
    return cur.lastrowid


class User(UserMixin):
    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.nama_lengkap = row['nama_lengkap']
        self.role = row['role']
        self.divisi = row['divisi']

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(uid):
    try:
        conn = get_db()
        row = _q(conn, "SELECT * FROM users WHERE id=%s AND is_active=1", (uid,), one=True)
        conn.close()
        return User(row) if row else None
    except Exception:
        return None


@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.context_processor
def inject_globals():
    return dict(
        app_name=Config.APP_NAME,
        company_name=Config.COMPANY_NAME,
        company_sub=Config.COMPANY_SUB,
        now=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        conn = get_db()
        row = _q(conn, "SELECT * FROM users WHERE username=%s AND is_active=1",
                 (username,), one=True)
        conn.close()
        if row and bcrypt.checkpw(password.encode(), row['password'].encode()):
            login_user(User(row))
            _log(row['id'], 'LOGIN', f'{username} logged in')
            flash('Login berhasil!', 'success')
            nxt = request.args.get('next')
            return redirect(nxt or url_for('dashboard'))
        flash('Username atau password salah.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        nama = request.form.get('nama_lengkap', '').strip()
        divisi = request.form.get('divisi', '').strip()
        if not all([username, password, nama]):
            flash('Semua field wajib diisi.', 'danger')
            return redirect(url_for('register'))
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_db()
        try:
            _exec(conn,
                  "INSERT INTO users (username,password,nama_lengkap,role,divisi) VALUES (%s,%s,%s,%s,%s)",
                  (username, hashed, nama, 'staff', divisi))
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Username sudah digunakan.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    _log(current_user.id, 'LOGOUT', f'{current_user.username} logged out')
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route('/')
@login_required
def dashboard():
    conn = get_db()
    total_keluar = _q(conn,
        "SELECT COUNT(*) AS c FROM surat_izin WHERE jenis='keluar'", one=True)['c']
    total_masuk = _q(conn,
        "SELECT COUNT(*) AS c FROM surat_izin WHERE jenis='masuk'", one=True)['c']
    total_pending = _q(conn,
        "SELECT COUNT(*) AS c FROM surat_izin WHERE status='pending'", one=True)['c']
    total_approved = _q(conn,
        "SELECT COUNT(*) AS c FROM surat_izin WHERE status='approved'", one=True)['c']

    recent = _q(conn,
        "SELECT * FROM surat_izin ORDER BY created_at DESC LIMIT 5")

    monthly = _q(conn, """
        SELECT DATE_FORMAT(tanggal, '%%Y-%%m') AS bulan,
               SUM(CASE WHEN jenis='keluar' THEN 1 ELSE 0 END) AS keluar,
               SUM(CASE WHEN jenis='masuk' THEN 1 ELSE 0 END) AS masuk
        FROM surat_izin
        GROUP BY bulan ORDER BY bulan DESC LIMIT 6
    """)

    divisi_stats = _q(conn, """
        SELECT divisi, COUNT(*) AS total FROM surat_izin GROUP BY divisi ORDER BY total DESC
    """)

    conn.close()
    return render_template('dashboard.html',
                           total_keluar=total_keluar,
                           total_masuk=total_masuk,
                           total_pending=total_pending,
                           total_approved=total_approved,
                           recent=recent,
                           monthly=list(reversed(monthly)),
                           divisi_stats=divisi_stats)


# ---------------------------------------------------------------------------
# Surat CRUD
# ---------------------------------------------------------------------------
@app.route('/surat')
@login_required
def surat_list():
    jenis = request.args.get('jenis', '')
    status = request.args.get('status', '')
    search = request.args.get('q', '')

    q = "SELECT * FROM surat_izin WHERE 1=1"
    params = []
    if jenis:
        q += " AND jenis=%s"
        params.append(jenis)
    if status:
        q += " AND status=%s"
        params.append(status)
    if search:
        q += " AND (no_surat LIKE %s OR nama LIKE %s OR perusahaan LIKE %s)"
        params.extend([f'%{search}%'] * 3)
    q += " ORDER BY created_at DESC"

    conn = get_db()
    rows = _q(conn, q, params)
    conn.close()
    return render_template('surat_list.html', surat_list=rows,
                           jenis=jenis, status=status, search=search)


@app.route('/surat/add', methods=['GET', 'POST'])
@login_required
def add_surat():
    if request.method == 'POST':
        jenis = request.form.get('jenis', 'keluar')
        required = ['no_surat', 'tanggal', 'tgl_terbit', 'divisi', 'nama',
                     'badge', 'no_kendaraan', 'perusahaan', 'no_spk',
                     'pemohon', 'diperiksa_oleh', 'disetujui_oleh']
        for f in required:
            if not request.form.get(f):
                flash(f'Field {f} harus diisi!', 'danger')
                return redirect(url_for('add_surat'))

        foto_filename = None
        foto = request.files.get('lampiran_foto')
        if foto and foto.filename and allowed_file(foto.filename):
            ext = foto.filename.rsplit('.', 1)[1].lower()
            foto_filename = f"{uuid.uuid4().hex}.{ext}"
            foto.save(os.path.join(Config.UPLOAD_DIR, foto_filename))

        try:
            barang = json.loads(request.form.get('barang_items', '[]'))
        except json.JSONDecodeError:
            flash('Format data barang tidak valid!', 'danger')
            return redirect(url_for('add_surat'))

        conn = get_db()
        sid = _exec(conn, """
            INSERT INTO surat_izin
            (jenis,no_surat,tanggal,tgl_terbit,divisi,nama,badge,no_kendaraan,
             perusahaan,no_spk,pemohon,diperiksa_oleh,disetujui_oleh,
             barang_items,lampiran_foto,status,created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            jenis,
            request.form['no_surat'].strip(),
            request.form['tanggal'],
            request.form['tgl_terbit'],
            request.form['divisi'],
            request.form['nama'].strip(),
            request.form['badge'].strip(),
            request.form['no_kendaraan'].strip(),
            request.form['perusahaan'].strip(),
            request.form['no_spk'].strip(),
            request.form['pemohon'].strip(),
            request.form['diperiksa_oleh'].strip(),
            request.form['disetujui_oleh'].strip(),
            json.dumps(barang, ensure_ascii=False),
            foto_filename,
            'pending',
            current_user.id,
        ))
        conn.close()
        _log(current_user.id, 'CREATE',
             f'Surat {jenis} {request.form["no_surat"]} dibuat')
        flash('Surat berhasil dibuat!', 'success')
        return redirect(url_for('view_surat', id=sid))

    today = date.today().isoformat()
    jenis = request.args.get('jenis', 'keluar')
    return render_template('add_surat.html', date_now=today, jenis=jenis)


@app.route('/surat/<int:id>')
@login_required
def view_surat(id):
    conn = get_db()
    surat = _q(conn, "SELECT * FROM surat_izin WHERE id=%s", (id,), one=True)
    conn.close()
    if not surat:
        flash('Surat tidak ditemukan.', 'danger')
        return redirect(url_for('surat_list'))
    surat = dict(surat)
    try:
        surat['barang_items'] = json.loads(surat['barang_items'])
    except Exception:
        surat['barang_items'] = []
    return render_template('view_surat.html', surat=surat)


@app.route('/surat/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_surat(id):
    conn = get_db()
    surat = _q(conn, "SELECT * FROM surat_izin WHERE id=%s", (id,), one=True)
    if not surat:
        conn.close()
        flash('Surat tidak ditemukan.', 'danger')
        return redirect(url_for('surat_list'))
    if request.method == 'POST':
        foto_filename = surat['lampiran_foto']
        foto = request.files.get('lampiran_foto')
        if foto and foto.filename and allowed_file(foto.filename):
            ext = foto.filename.rsplit('.', 1)[1].lower()
            foto_filename = f"{uuid.uuid4().hex}.{ext}"
            foto.save(os.path.join(Config.UPLOAD_DIR, foto_filename))

        try:
            barang = json.loads(request.form.get('barang_items', '[]'))
        except json.JSONDecodeError:
            flash('Format data barang tidak valid!', 'danger')
            return redirect(url_for('edit_surat', id=id))

        _exec(conn, """
            UPDATE surat_izin SET
              jenis=%s,no_surat=%s,tanggal=%s,tgl_terbit=%s,divisi=%s,nama=%s,badge=%s,
              no_kendaraan=%s,perusahaan=%s,no_spk=%s,pemohon=%s,diperiksa_oleh=%s,
              disetujui_oleh=%s,barang_items=%s,lampiran_foto=%s
            WHERE id=%s
        """, (
            request.form.get('jenis', surat['jenis']),
            request.form['no_surat'].strip(),
            request.form['tanggal'],
            request.form['tgl_terbit'],
            request.form['divisi'],
            request.form['nama'].strip(),
            request.form['badge'].strip(),
            request.form['no_kendaraan'].strip(),
            request.form['perusahaan'].strip(),
            request.form['no_spk'].strip(),
            request.form['pemohon'].strip(),
            request.form['diperiksa_oleh'].strip(),
            request.form['disetujui_oleh'].strip(),
            json.dumps(barang, ensure_ascii=False),
            foto_filename,
            id,
        ))
        conn.close()
        _log(current_user.id, 'UPDATE', f'Surat #{id} diperbarui')
        flash('Surat berhasil diperbarui!', 'success')
        return redirect(url_for('view_surat', id=id))

    conn.close()
    surat = dict(surat)
    try:
        surat['barang_items'] = json.loads(surat['barang_items'])
    except Exception:
        surat['barang_items'] = []
    return render_template('edit_surat.html', surat=surat)


@app.route('/surat/<int:id>/status', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def update_status(id):
    new_status = request.form.get('status')
    catatan = request.form.get('catatan', '')
    if new_status not in ('approved', 'rejected', 'pending'):
        flash('Status tidak valid.', 'danger')
        return redirect(url_for('view_surat', id=id))
    conn = get_db()
    _exec(conn, "UPDATE surat_izin SET status=%s, catatan=%s WHERE id=%s",
          (new_status, catatan, id))
    conn.close()
    _log(current_user.id, 'STATUS', f'Surat #{id} status → {new_status}')
    flash(f'Status surat diubah menjadi {new_status}.', 'success')
    return redirect(url_for('view_surat', id=id))


@app.route('/surat/<int:id>/delete')
@login_required
@role_required('admin', 'manager')
def delete_surat(id):
    conn = get_db()
    s = _q(conn, "SELECT no_surat FROM surat_izin WHERE id=%s", (id,), one=True)
    if s:
        _exec(conn, "DELETE FROM surat_izin WHERE id=%s", (id,))
        _log(current_user.id, 'DELETE', f'Surat {s["no_surat"]} dihapus')
        flash('Surat berhasil dihapus.', 'success')
    else:
        flash('Surat tidak ditemukan.', 'danger')
    conn.close()
    return redirect(url_for('surat_list'))


# ---------------------------------------------------------------------------
# Export PDF (single surat)
# ---------------------------------------------------------------------------
@app.route('/surat/<int:id>/pdf')
@login_required
def export_pdf(id):
    conn = get_db()
    surat = _q(conn, "SELECT * FROM surat_izin WHERE id=%s", (id,), one=True)
    conn.close()
    if not surat:
        flash('Surat tidak ditemukan.', 'danger')
        return redirect(url_for('surat_list'))
    surat = dict(surat)
    try:
        surat['barang_items'] = json.loads(surat['barang_items'])
    except Exception:
        surat['barang_items'] = []

    html = render_template('pdf_template.html', surat=surat)
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html, base_url=request.host_url).write_pdf()
        clean = ''.join(c for c in surat['no_surat'] if c.isalnum() or c in '-_.')
        filename = f"surat_izin_{clean}.pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        flash(f'Gagal membuat PDF: {e}', 'danger')
        return redirect(url_for('view_surat', id=id))


# ---------------------------------------------------------------------------
# Export Excel report
# ---------------------------------------------------------------------------
@app.route('/report/excel')
@login_required
def export_excel():
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    conn = get_db()
    rows = _q(conn, "SELECT * FROM surat_izin ORDER BY tanggal DESC")
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Laporan Surat Izin"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )

    ws.merge_cells('A1:I1')
    ws['A1'] = f'LAPORAN SURAT IZIN KELUAR MASUK BARANG - {Config.COMPANY_NAME}'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.merge_cells('A2:I2')
    ws['A2'] = f'Dicetak: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    ws['A2'].alignment = Alignment(horizontal='center')

    headers = ['No', 'Jenis', 'No. Surat', 'Tanggal', 'Divisi',
               'Nama', 'Perusahaan', 'Status', 'Dibuat']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    for i, r in enumerate(rows, 5):
        vals = [i - 4, r['jenis'].upper(), r['no_surat'], str(r['tanggal']),
                r['divisi'], r['nama'], r['perusahaan'],
                r['status'].upper(), str(r['created_at'])]
        for col, v in enumerate(vals, 1):
            cell = ws.cell(row=i, column=col, value=v)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center' if col in (1, 2, 8) else 'left')

    for col in ws.columns:
        max_len = max((len(str(c.value or '')) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=f'laporan_surat_{datetime.now().strftime("%Y%m%d")}.xlsx')


# ---------------------------------------------------------------------------
# Export PDF report
# ---------------------------------------------------------------------------
@app.route('/report/pdf')
@login_required
def export_report_pdf():
    conn = get_db()
    rows = _q(conn, "SELECT * FROM surat_izin ORDER BY tanggal DESC")
    total_keluar = _q(conn, "SELECT COUNT(*) AS c FROM surat_izin WHERE jenis='keluar'", one=True)['c']
    total_masuk = _q(conn, "SELECT COUNT(*) AS c FROM surat_izin WHERE jenis='masuk'", one=True)['c']
    conn.close()

    html = render_template('report_pdf.html', rows=rows,
                           total_keluar=total_keluar, total_masuk=total_masuk)
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf', as_attachment=True,
            download_name=f'laporan_{datetime.now().strftime("%Y%m%d")}.pdf',
        )
    except Exception as e:
        flash(f'Gagal membuat PDF: {e}', 'danger')
        return redirect(url_for('dashboard'))


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------
@app.route('/users')
@login_required
@role_required('admin')
def user_list():
    conn = get_db()
    users = _q(conn, "SELECT * FROM users ORDER BY created_at DESC")
    conn.close()
    return render_template('users.html', users=users)


@app.route('/users/<int:uid>/toggle')
@login_required
@role_required('admin')
def toggle_user(uid):
    if uid == current_user.id:
        flash('Tidak bisa menonaktifkan diri sendiri.', 'danger')
        return redirect(url_for('user_list'))
    conn = get_db()
    u = _q(conn, "SELECT is_active FROM users WHERE id=%s", (uid,), one=True)
    if u:
        _exec(conn, "UPDATE users SET is_active=%s WHERE id=%s",
              (0 if u['is_active'] else 1, uid))
        flash('Status user diperbarui.', 'success')
    conn.close()
    return redirect(url_for('user_list'))


@app.route('/users/<int:uid>/role', methods=['POST'])
@login_required
@role_required('admin')
def change_role(uid):
    new_role = request.form.get('role')
    if new_role not in ('admin', 'staff', 'manager'):
        flash('Role tidak valid.', 'danger')
        return redirect(url_for('user_list'))
    conn = get_db()
    _exec(conn, "UPDATE users SET role=%s WHERE id=%s", (new_role, uid))
    conn.close()
    flash('Role user diperbarui.', 'success')
    return redirect(url_for('user_list'))


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route('/api/surat/<int:id>')
@login_required
def api_surat(id):
    conn = get_db()
    s = _q(conn, "SELECT * FROM surat_izin WHERE id=%s", (id,), one=True)
    conn.close()
    if not s:
        return jsonify(success=False, error='Tidak ditemukan'), 404
    d = dict(s)
    d['barang_items'] = json.loads(d['barang_items'])
    d['tanggal'] = str(d['tanggal'])
    d['tgl_terbit'] = str(d['tgl_terbit'])
    d['created_at'] = str(d['created_at']) if d['created_at'] else None
    d['updated_at'] = str(d['updated_at']) if d['updated_at'] else None
    return jsonify(success=True, data=d)


@app.route('/api/stats')
@login_required
def api_stats():
    conn = get_db()
    monthly = _q(conn, """
        SELECT DATE_FORMAT(tanggal, '%%Y-%%m') AS bulan,
               SUM(CASE WHEN jenis='keluar' THEN 1 ELSE 0 END) AS keluar,
               SUM(CASE WHEN jenis='masuk' THEN 1 ELSE 0 END) AS masuk
        FROM surat_izin GROUP BY bulan ORDER BY bulan DESC LIMIT 12
    """)
    conn.close()
    return jsonify(monthly)


# ---------------------------------------------------------------------------
# Activity log
# ---------------------------------------------------------------------------
@app.route('/activity')
@login_required
@role_required('admin')
def activity_log():
    conn = get_db()
    logs = _q(conn, """
        SELECT l.*, u.username FROM log_activity l
        LEFT JOIN users u ON l.user_id=u.id
        ORDER BY l.created_at DESC LIMIT 100
    """)
    conn.close()
    return render_template('activity.html', logs=logs)


def _log(user_id, action, desc):
    try:
        conn = get_db()
        _exec(conn,
              "INSERT INTO log_activity (user_id,action,description,ip_address) VALUES (%s,%s,%s,%s)",
              (user_id, action, desc, request.remote_addr))
        conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403,
                           message='Anda tidak memiliki akses ke halaman ini.'), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404,
                           message='Halaman tidak ditemukan.'), 404


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    Config.init_app(app)
    init_db()
    print(f"🚀 {Config.APP_NAME}")
    print("📄 Open http://localhost:8000")
    app.run(debug=True, host='0.0.0.0', port=8000)