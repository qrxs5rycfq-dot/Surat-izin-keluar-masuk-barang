from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import pymysql
pymysql.install_as_MySQLdb()  # WAJIB untuk Mac
from flask_mysqldb import MySQL
from config import config
import pdfkit
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config.from_object(config)

# Initialize MySQL
mysql = MySQL(app)

# Initialize PDFKit configuration untuk Mac
wkhtml_paths = [
    '/opt/homebrew/bin/wkhtmltopdf',  # Untuk Mac Apple Silicon (M1/M2)
    '/usr/local/bin/wkhtmltopdf',     # Untuk Mac Intel
    '/usr/bin/wkhtmltopdf'            # Default Linux/Mac
]

config_pdf = None
for path in wkhtml_paths:
    if os.path.exists(path):
        config_pdf = pdfkit.configuration(wkhtmltopdf=path)
        print(f"✅ Found wkhtmltopdf at: {path}")
        break

if config_pdf is None:
    print("⚠️ Warning: wkhtmltopdf not found. PDF export will not work.")
    print("Install with: brew install --cask wkhtmltopdf")

# Routes
@app.route('/')
def index():
    """Halaman utama untuk menampilkan daftar surat izin"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, no_surat, tanggal, divisi, nama, perusahaan, created_at 
            FROM surat_izin 
            ORDER BY tanggal DESC, id DESC
        """)
        surat_list = cur.fetchall()
        cur.close()
        return render_template('index.html', surat_list=surat_list)
    except Exception as e:
        flash(f'Error connecting to database: {str(e)}', 'danger')
        return render_template('index.html', surat_list=[])

@app.route('/add', methods=['GET', 'POST'])
def add_surat():
    """Form untuk menambahkan surat izin baru"""
    if request.method == 'POST':
        try:
            # Validasi required fields
            required_fields = ['no_surat', 'tanggal', 'tgl_terbit', 'divisi', 'nama', 
                              'badge', 'no_kendaraan', 'perusahaan', 'no_spk', 
                              'pemohon', 'diperiksa_oleh', 'disetujui_oleh']
            
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Field {field} harus diisi!', 'danger')
                    return redirect(url_for('add_surat'))
            
            # Collect form data
            data = {
                'no_surat': request.form['no_surat'].strip(),
                'tanggal': request.form['tanggal'],
                'tgl_terbit': request.form['tgl_terbit'],
                'divisi': request.form['divisi'],
                'nama': request.form['nama'].strip(),
                'badge': request.form['badge'].strip(),
                'no_kendaraan': request.form['no_kendaraan'].strip(),
                'perusahaan': request.form['perusahaan'].strip(),
                'no_spk': request.form['no_spk'].strip(),
                'pemohon': request.form['pemohon'].strip(),
                'diperiksa_oleh': request.form['diperiksa_oleh'].strip(),
                'disetujui_oleh': request.form['disetujui_oleh'].strip(),
                'barang_items': json.loads(request.form['barang_items']),
                'lampiran_foto': request.form.get('lampiran_foto', '').strip()
            }
            
            # Insert to database
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO surat_izin (
                    no_surat, tanggal, tgl_terbit, divisi, nama, badge, 
                    no_kendaraan, perusahaan, no_spk, pemohon, diperiksa_oleh, 
                    disetujui_oleh, barang_items, lampiran_foto
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['no_surat'], data['tanggal'], data['tgl_terbit'],
                data['divisi'], data['nama'], data['badge'], data['no_kendaraan'],
                data['perusahaan'], data['no_spk'], data['pemohon'], 
                data['diperiksa_oleh'], data['disetujui_oleh'],
                json.dumps(data['barang_items'], ensure_ascii=False), data['lampiran_foto']
            ))
            
            mysql.connection.commit()
            surat_id = cur.lastrowid
            cur.close()
            
            flash('Surat izin berhasil ditambahkan!', 'success')
            return redirect(url_for('view_surat', id=surat_id))
            
        except json.JSONDecodeError:
            flash('Format data barang tidak valid!', 'danger')
            return redirect(url_for('add_surat'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('add_surat'))
    
    # GET request - tampilkan form
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_surat.html', date_now=today)

@app.route('/view/<int:id>')
def view_surat(id):
    """Menampilkan detail surat izin"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM surat_izin WHERE id = %s", (id,))
        surat = cur.fetchone()
        cur.close()
        
        if surat:
            # Parse JSON items
            try:
                surat['barang_items'] = json.loads(surat['barang_items'])
            except:
                surat['barang_items'] = []
            
            return render_template('view_surat.html', surat=surat)
        else:
            flash('Surat izin tidak ditemukan', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/export_pdf/<int:id>')
def export_pdf(id):
    """Export surat izin ke PDF"""
    try:
        # Get surat data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM surat_izin WHERE id = %s", (id,))
        surat = cur.fetchone()
        cur.close()
        
        if not surat:
            flash('Surat izin tidak ditemukan', 'danger')
            return redirect(url_for('index'))
        
        # Parse JSON items
        try:
            surat['barang_items'] = json.loads(surat['barang_items'])
        except:
            surat['barang_items'] = []
        
        # Generate HTML for PDF
        html_content = render_template('pdf_template.html', surat=surat)
        
        # Configure PDF options
        options = {
            'page-size': 'A4',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'quiet': ''
        }
        
        # Generate PDF filename
        # Bersihkan nama file dari karakter yang tidak valid
        clean_no_surat = ''.join(c for c in surat['no_surat'] if c.isalnum() or c in ('-', '_', '.'))
        pdf_filename = f"surat_izin_{clean_no_surat}.pdf"
        pdf_path = os.path.join(app.config['PDF_DIR'], pdf_filename)
        
        # Create PDF directory if not exists
        os.makedirs(app.config['PDF_DIR'], exist_ok=True)
        
        # Generate PDF
        if config_pdf:
            pdfkit.from_string(html_content, pdf_path, 
                              configuration=config_pdf, 
                              options=options)
        else:
            # Try without configuration
            pdfkit.from_string(html_content, pdf_path, options=options)
        
        return send_file(pdf_path, as_attachment=True, 
                        download_name=pdf_filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        # Debug info
        print(f"PDF Generation Error: {e}")
        return redirect(url_for('view_surat', id=id))

@app.route('/delete/<int:id>')
def delete_surat(id):
    """Hapus surat izin"""
    try:
        # Ambil nomor surat untuk pesan konfirmasi
        cur = mysql.connection.cursor()
        cur.execute("SELECT no_surat FROM surat_izin WHERE id = %s", (id,))
        result = cur.fetchone()
        
        if result:
            no_surat = result['no_surat']
            # Hapus surat
            cur.execute("DELETE FROM surat_izin WHERE id = %s", (id,))
            mysql.connection.commit()
            cur.close()
            
            flash(f'Surat izin {no_surat} berhasil dihapus!', 'success')
        else:
            flash('Surat izin tidak ditemukan', 'danger')
            
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/api/surat/<int:id>', methods=['GET'])
def get_surat_json(id):
    """API untuk mendapatkan data surat dalam format JSON"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM surat_izin WHERE id = %s", (id,))
        surat = cur.fetchone()
        cur.close()
        
        if surat:
            # Parse JSON items
            surat['barang_items'] = json.loads(surat['barang_items'])
            # Convert datetime to string
            surat['created_at'] = surat['created_at'].strftime('%Y-%m-%d %H:%M:%S') if surat['created_at'] else None
            surat['updated_at'] = surat['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if surat['updated_at'] else None
            
            return jsonify({
                'success': True,
                'data': surat
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Surat izin tidak ditemukan'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('error.html', error='Halaman tidak ditemukan'), 404

# @app.errorhandler(500)
# def internal_server_error(e):
#     return render_template('error.html', error='Terjadi kesalahan server'), 500

if __name__ == '__main__':
    # Initialize app
    config.init_app(app)
    
    # Check database connection
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check:")
        print("1. MySQL service is running: brew services start mysql")
        print("2. Database 'surat_izin_db' exists")
        print("3. User credentials in config.py are correct")
    
    # Run app
    print("🚀 Starting Flask application...")
    print("📄 Open http://localhost:8000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=8000)