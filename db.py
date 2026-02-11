import pymysql
import pymysql.cursors
from config import Config


def get_db():
    """Get a MySQL database connection returning dict rows."""
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    return conn


def _execute(conn, sql, params=None):
    """Helper: execute and return cursor."""
    cur = conn.cursor()
    cur.execute(sql, params or ())
    return cur


def init_db():
    """Create tables if needed and seed initial data."""
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()

    cur.execute(
        "CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        % Config.MYSQL_DB
    )
    cur.execute("USE `%s`" % Config.MYSQL_DB)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        nama_lengkap VARCHAR(100) NOT NULL,
        role ENUM('admin','staff','manager') NOT NULL DEFAULT 'staff',
        divisi VARCHAR(50),
        is_active TINYINT(1) DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS surat_izin (
        id INT AUTO_INCREMENT PRIMARY KEY,
        jenis ENUM('keluar','masuk') NOT NULL DEFAULT 'keluar',
        no_surat VARCHAR(100) NOT NULL,
        tanggal DATE NOT NULL,
        tgl_terbit DATE NOT NULL,
        divisi VARCHAR(50) NOT NULL,
        nama VARCHAR(100) NOT NULL,
        badge VARCHAR(50) NOT NULL,
        no_kendaraan VARCHAR(50) NOT NULL,
        perusahaan VARCHAR(100) NOT NULL,
        no_spk VARCHAR(100) NOT NULL,
        pemohon VARCHAR(100) NOT NULL,
        diperiksa_oleh VARCHAR(100) NOT NULL,
        disetujui_oleh VARCHAR(100) NOT NULL,
        barang_items TEXT NOT NULL,
        lampiran_foto TEXT,
        status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
        catatan TEXT,
        created_by INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_jenis (jenis),
        INDEX idx_no_surat (no_surat),
        INDEX idx_tanggal (tanggal),
        INDEX idx_status (status),
        INDEX idx_divisi (divisi)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS log_activity (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        action VARCHAR(50) NOT NULL,
        description TEXT NOT NULL,
        ip_address VARCHAR(45),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_action (action),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Seed default users if table is empty
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()['c'] == 0:
        import bcrypt
        pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (username,password,nama_lengkap,role,divisi) VALUES (%s,%s,%s,%s,%s)",
            ('admin', pw, 'Administrator', 'admin', 'IT'),
        )
        pw2 = bcrypt.hashpw(b'staff123', bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (username,password,nama_lengkap,role,divisi) VALUES (%s,%s,%s,%s,%s)",
            ('staff01', pw2, 'Budi Santoso', 'staff', 'PEMELIHARAAN'),
        )
        pw3 = bcrypt.hashpw(b'manager123', bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (username,password,nama_lengkap,role,divisi) VALUES (%s,%s,%s,%s,%s)",
            ('manager01', pw3, 'Manager Administrasi', 'manager', 'ADMINISTRASI'),
        )

    # Seed sample surat if empty
    cur.execute("SELECT COUNT(*) AS c FROM surat_izin")
    if cur.fetchone()['c'] == 0:
        import json
        samples = [
            ('keluar', '3783.SJ/07/ADPPGU/2023', '2023-07-15', '2023-07-01',
             'PEMELIHARAAN', 'BUDI SANTOSO', 'EMP-12345', 'B 1234 XYZ',
             'PT MITRA SEJAHTERA', 'SPK/2023/07/001', 'BUDI SANTOSO',
             'KOMANDAN REGU', 'MANAGER ADMINISTRASI',
             json.dumps([
                 {"nama_barang": "Kabel Listrik 4x2.5mm", "jumlah": 10,
                  "satuan": "Roll", "keterangan": "Merah, panjang 100m"},
                 {"nama_barang": "MCB 3 Phase", "jumlah": 5,
                  "satuan": "Unit", "keterangan": "32A Schneider"},
             ]), None, 'approved', 1),
            ('masuk', '3784.SM/07/ADPPGU/2023', '2023-07-16', '2023-07-01',
             'OPERASI', 'SARI DEWI', 'EMP-67890', 'B 5678 ABC',
             'PT JAYA ABADI', 'SPK/2023/07/002', 'SARI DEWI',
             'SUPERVISOR OPERASI', 'MANAGER ADMINISTRASI',
             json.dumps([
                 {"nama_barang": "Transformator 500 kVA", "jumlah": 1,
                  "satuan": "Unit", "keterangan": "Baru"},
             ]), None, 'pending', 1),
            ('keluar', '3785.SJ/08/ADPPGU/2023', '2023-08-10', '2023-08-01',
             'TEKNIK', 'AGUS PRASETYA', 'EMP-24680', 'B 9012 DEF',
             'CV TEKNIK MANDIRI', 'MEMO/TEK/08/2023', 'AGUS PRASETYA',
             'KEPALA TEKNIK', 'MANAGER ADMINISTRASI',
             json.dumps([
                 {"nama_barang": "Multimeter Digital", "jumlah": 3,
                  "satuan": "Unit", "keterangan": "Fluke 87V"},
             ]), None, 'approved', 1),
        ]
        for s in samples:
            cur.execute("""
                INSERT INTO surat_izin
                (jenis,no_surat,tanggal,tgl_terbit,divisi,nama,badge,
                 no_kendaraan,perusahaan,no_spk,pemohon,diperiksa_oleh,
                 disetujui_oleh,barang_items,lampiran_foto,status,created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, s)

    conn.commit()
    cur.close()
    conn.close()
