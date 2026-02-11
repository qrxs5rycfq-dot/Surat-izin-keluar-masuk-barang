-- ============================================
-- DATABASE: surat_izin_db
-- Untuk Aplikasi Surat Izin Keluar Barang
-- PT PLN Indonesia Power
-- ============================================

-- Buat database jika belum ada
CREATE DATABASE IF NOT EXISTS surat_izin_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Gunakan database
USE surat_izin_db;

-- ============================================
-- TABEL: surat_izin
-- Menyimpan data surat izin keluar barang
-- ============================================
CREATE TABLE IF NOT EXISTS surat_izin (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Informasi Surat
    no_surat VARCHAR(100) NOT NULL,
    tanggal DATE NOT NULL,
    tgl_terbit DATE NOT NULL,
    divisi VARCHAR(50) NOT NULL,
    
    -- Data Pemohon
    nama VARCHAR(100) NOT NULL,
    badge VARCHAR(50) NOT NULL,
    no_kendaraan VARCHAR(50) NOT NULL,
    perusahaan VARCHAR(100) NOT NULL,
    no_spk VARCHAR(100) NOT NULL,
    
    -- Tanda Tangan
    pemohon VARCHAR(100) NOT NULL,
    diperiksa_oleh VARCHAR(100) NOT NULL,
    disetujui_oleh VARCHAR(100) NOT NULL,
    
    -- Data Barang (disimpan sebagai JSON)
    barang_items TEXT NOT NULL,
    
    -- Lampiran
    lampiran_foto TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes untuk performa query
    INDEX idx_no_surat (no_surat),
    INDEX idx_tanggal (tanggal),
    INDEX idx_divisi (divisi),
    INDEX idx_nama (nama),
    INDEX idx_perusahaan (perusahaan)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- DATA CONTOH (Sample Data)
-- ============================================
INSERT INTO surat_izin (
    no_surat, 
    tanggal, 
    tgl_terbit, 
    divisi, 
    nama, 
    badge, 
    no_kendaraan, 
    perusahaan, 
    no_spk, 
    pemohon, 
    diperiksa_oleh, 
    disetujui_oleh, 
    barang_items, 
    lampiran_foto
) VALUES 
(
    '3783.SJ/07/ADPPGU/2023',
    '2023-07-15',
    '2023-07-01',
    'PEMELIHARAAN',
    'BUDI SANTOSO',
    'EMP-12345',
    'B 1234 XYZ',
    'PT MITRA SEJAHTERA',
    'SPK/2023/07/001',
    'BUDI SANTOSO',
    'KOMANDAN REGU',
    'MANAGER ADMINISTRASI',
    '[{"no": 1, "nama_barang": "Kabel Listrik 4x2.5mm", "jumlah": 10, "satuan": "Roll", "keterangan": "Merah, panjang 100m"}, {"no": 2, "nama_barang": "MCB 3 Phase", "jumlah": 5, "satuan": "Unit", "keterangan": "32A Schneider"}, {"no": 3, "nama_barang": "Stop Kontak Outdoor", "jumlah": 20, "satuan": "Pcs", "keterangan": "Tahan Air IP67"}]',
    'Foto barang sebelum packing dan loading ke truk'
),
(
    '3784.SJ/07/ADPPGU/2023',
    '2023-07-16',
    '2023-07-01',
    'OPERASI',
    'SARI DEWI',
    'EMP-67890',
    'B 5678 ABC',
    'PT JAYA ABADI',
    'SPK/2023/07/002',
    'SARI DEWI',
    'SUPERVISOR OPERASI',
    'MANAGER ADMINISTRASI',
    '[{"no": 1, "nama_barang": "Transformator 500 kVA", "jumlah": 1, "satuan": "Unit", "keterangan": "Baru, belum dipakai"}, {"no": 2, "nama_barang": "Panel Listrik", "jumlah": 2, "satuan": "Unit", "keterangan": "Control panel MCCB"}, {"no": 3, "nama_barang": "Kabel NYY 4x50mm", "jumlah": 5, "satuan": "Roll", "keterangan": "Panjang 50m/roll"}]',
    'Dokumentasi lengkap dengan nomor seri'
),
(
    '3785.SJ/07/ADPPGU/2023',
    '2023-07-17',
    '2023-07-01',
    'TEKNIK',
    'AGUS PRASETYA',
    'EMP-24680',
    'B 9012 DEF',
    'CV TEKNIK MANDIRI',
    'MEMO/TEK/07/2023',
    'AGUS PRASETYA',
    'KEPALA TEKNIK',
    'MANAGER ADMINISTRASI',
    '[{"no": 1, "nama_barang": "Multimeter Digital", "jumlah": 3, "satuan": "Unit", "keterangan": "Fluke 87V"}, {"no": 2, "nama_barang": "Tang Ampere", "jumlah": 2, "satuan": "Pcs", "keterangan": "AC/DC clamp meter"}, {"no": 3, "nama_barang": "Toolkit Elektrik", "jumlah": 1, "satuan": "Set", "keterangan": "Lengkap 32pcs"}]',
    'Kondisi barang baik, sudah diperiksa'
);

-- ============================================
-- TABEL: users (Optional - untuk autentikasi)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nama_lengkap VARCHAR(100) NOT NULL,
    role ENUM('admin', 'staff', 'manager') DEFAULT 'staff',
    divisi VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data contoh users (password: password123)
INSERT INTO users (username, password, nama_lengkap, role, divisi) VALUES
('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Administrator System', 'admin', 'IT'),
('staff01', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Budi Santoso', 'staff', 'PEMELIHARAAN'),
('manager01', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Manager Administrasi', 'manager', 'ADMINISTRASI');

-- ============================================
-- TABEL: settings (untuk konfigurasi sistem)
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data default settings
INSERT INTO settings (setting_key, setting_value, description) VALUES
('company_name', 'PT PLN INDONESIA POWER', 'Nama Perusahaan'),
('company_address', 'UBP Jawa Tengah 2 Adipala', 'Alamat Perusahaan'),
('system_name', 'Indonesia Power Integrated Management System', 'Nama Sistem'),
('document_no', 'ADP.17.01.015', 'Nomor Dokumen'),
('revision', '2', 'Revisi Dokumen'),
('default_divisi', 'PEMELIHARAAN', 'Divisi Default'),
('pdf_footer', 'Sistem Surat Izin Keluar Barang - © 2023 PT PLN Indonesia Power', 'Footer PDF');

-- ============================================
-- TABEL: log_activity (log aktivitas sistem)
-- ============================================
CREATE TABLE IF NOT EXISTS log_activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- STORED PROCEDURES
-- ============================================

-- Procedure untuk mendapatkan statistik surat per bulan
DELIMITER //
CREATE PROCEDURE GetMonthlyStats(IN year_param INT)
BEGIN
    SELECT 
        MONTH(tanggal) as bulan,
        COUNT(*) as total_surat,
        GROUP_CONCAT(DISTINCT divisi) as divisi_aktif
    FROM surat_izin
    WHERE YEAR(tanggal) = year_param
    GROUP BY MONTH(tanggal)
    ORDER BY bulan;
END //
DELIMITER ;

-- Procedure untuk mendapatkan rekap surat per divisi
DELIMITER //
CREATE PROCEDURE GetDivisiStats(IN start_date DATE, IN end_date DATE)
BEGIN
    SELECT 
        divisi,
        COUNT(*) as total_surat,
        GROUP_CONCAT(DISTINCT perusahaan) as perusahaan_list
    FROM surat_izin
    WHERE tanggal BETWEEN start_date AND end_date
    GROUP BY divisi
    ORDER BY total_surat DESC;
END //
DELIMITER ;

-- ============================================
-- VIEWS
-- ============================================

-- View untuk laporan harian
CREATE VIEW v_daily_report AS
SELECT 
    DATE(tanggal) as tanggal,
    COUNT(*) as jumlah_surat,
    GROUP_CONCAT(no_surat SEPARATOR ', ') as list_surat,
    GROUP_CONCAT(DISTINCT divisi) as divisi_hari_ini
FROM surat_izin
GROUP BY DATE(tanggal)
ORDER BY tanggal DESC;

-- View untuk laporan per perusahaan
CREATE VIEW v_perusahaan_report AS
SELECT 
    perusahaan,
    COUNT(*) as total_surat,
    MIN(tanggal) as pertama_kali,
    MAX(tanggal) as terakhir_kali,
    GROUP_CONCAT(DISTINCT divisi) as divisi_terkait
FROM surat_izin
GROUP BY perusahaan
ORDER BY total_surat DESC;

-- ============================================
-- TRIGGERS
-- ============================================

-- Trigger untuk log ketika surat dibuat
DELIMITER //
CREATE TRIGGER tr_surat_izin_after_insert
AFTER INSERT ON surat_izin
FOR EACH ROW
BEGIN
    INSERT INTO log_activity (action, description, table_name, record_id)
    VALUES ('INSERT', CONCAT('Surat baru dibuat: ', NEW.no_surat), 'surat_izin', NEW.id);
END //
DELIMITER ;

-- Trigger untuk log ketika surat diupdate
DELIMITER //
CREATE TRIGGER tr_surat_izin_after_update
AFTER UPDATE ON surat_izin
FOR EACH ROW
BEGIN
    INSERT INTO log_activity (action, description, table_name, record_id)
    VALUES ('UPDATE', CONCAT('Surat diupdate: ', NEW.no_surat), 'surat_izin', NEW.id);
END //
DELIMITER ;

-- Trigger untuk log ketika surat dihapus
DELIMITER //
CREATE TRIGGER tr_surat_izin_after_delete
AFTER DELETE ON surat_izin
FOR EACH ROW
BEGIN
    INSERT INTO log_activity (action, description, table_name, record_id)
    VALUES ('DELETE', CONCAT('Surat dihapus: ', OLD.no_surat), 'surat_izin', OLD.id);
END //
DELIMITER ;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function untuk generate nomor surat otomatis
DELIMITER //
CREATE FUNCTION GenerateNomorSurat(divisi_code VARCHAR(10), bulan INT, tahun INT)
RETURNS VARCHAR(50)
DETERMINISTIC
BEGIN
    DECLARE nomor_urut INT;
    DECLARE bulan_romawi VARCHAR(10);
    DECLARE nomor_surat VARCHAR(50);
    
    -- Konversi bulan ke romawi
    SET bulan_romawi = CASE bulan
        WHEN 1 THEN 'I'
        WHEN 2 THEN 'II'
        WHEN 3 THEN 'III'
        WHEN 4 THEN 'IV'
        WHEN 5 THEN 'V'
        WHEN 6 THEN 'VI'
        WHEN 7 THEN 'VII'
        WHEN 8 THEN 'VIII'
        WHEN 9 THEN 'IX'
        WHEN 10 THEN 'X'
        WHEN 11 THEN 'XI'
        WHEN 12 THEN 'XII'
        ELSE ''
    END;
    
    -- Hitung nomor urut bulan ini
    SELECT COUNT(*) + 1 INTO nomor_urut 
    FROM surat_izin 
    WHERE MONTH(tanggal) = bulan 
    AND YEAR(tanggal) = tahun;
    
    -- Format nomor surat
    SET nomor_surat = CONCAT(
        nomor_urut, '.SJ/',
        LPAD(bulan, 2, '0'), '/',
        divisi_code, '/',
        tahun
    );
    
    RETURN nomor_surat;
END //
DELIMITER ;

-- Function untuk menghitung total item barang
DELIMITER //
CREATE FUNCTION GetTotalBarang(surat_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total INT DEFAULT 0;
    DECLARE barang_json TEXT;
    
    -- Ambil data barang
    SELECT barang_items INTO barang_json
    FROM surat_izin 
    WHERE id = surat_id;
    
    -- Hitung total item (sederhana)
    IF barang_json IS NOT NULL THEN
        SET total = (LENGTH(barang_json) - LENGTH(REPLACE(barang_json, '"nama_barang"', ''))) / LENGTH('"nama_barang"');
    END IF;
    
    RETURN total;
END //
DELIMITER ;

-- ============================================
-- QUERY UNTUK VALIDASI
-- ============================================

-- Tampilkan semua tabel yang dibuat
SHOW TABLES;

-- Tampilkan struktur tabel surat_izin
DESCRIBE surat_izin;

-- Tampilkan data contoh
SELECT 
    id,
    no_surat,
    tanggal,
    divisi,
    nama,
    perusahaan,
    created_at
FROM surat_izin 
ORDER BY tanggal DESC;

-- Test function GenerateNomorSurat
SELECT GenerateNomorSurat('ADPPGU', 7, 2023) as nomor_surat_baru;

-- Test procedure GetMonthlyStats
CALL GetMonthlyStats(2023);

-- Test view
SELECT * FROM v_daily_report LIMIT 5;

-- ============================================
-- GRANT PERMISSIONS (Opsional - untuk user aplikasi)
-- ============================================
/*
-- Buat user khusus untuk aplikasi
CREATE USER IF NOT EXISTS 'app_user'@'localhost' IDENTIFIED BY 'password123';
GRANT SELECT, INSERT, UPDATE, DELETE ON surat_izin_db.* TO 'app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE surat_izin_db.GetMonthlyStats TO 'app_user'@'localhost';
GRANT EXECUTE ON PROCEDURE surat_izin_db.GetDivisiStats TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
*/

-- ============================================
-- BACKUP COMMAND (Untuk referensi)
-- ============================================
/*
-- Untuk backup database:
-- mysqldump -u root -p surat_izin_db > backup_$(date +%Y%m%d).sql

-- Untuk restore database:
-- mysql -u root -p surat_izin_db < database.sql
*/

-- ============================================
-- INFORMASI DATABASE
-- ============================================
SELECT 
    'surat_izin_db' as database_name,
    'UTF8MB4' as character_set,
    'utf8mb4_unicode_ci' as collation,
    'InnoDB' as storage_engine,
    CURRENT_TIMESTAMP as created_at,
    'PT PLN Indonesia Power - Sistem Surat Izin Keluar Barang' as description;

-- Tampilkan informasi versi
SELECT VERSION() as mysql_version;