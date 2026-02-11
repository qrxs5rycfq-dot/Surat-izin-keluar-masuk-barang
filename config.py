import os
from datetime import datetime

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-123-change-this-in-production'
    
    # Database configuration for Mac - PASTIKAN INI BENAR!
    MYSQL_HOST = '127.0.0.1'  # Gunakan IP, bukan 'localhost' untuk menghindari socket issues
    MYSQL_USER = 'root'        # atau user lain yang sudah dibuat
    MYSQL_PASSWORD = 'password123'  # Password MySQL Anda
    MYSQL_DB = 'surat_izin_db'
    MYSQL_CURSORCLASS = 'DictCursor'
    MYSQL_PORT = 3306  # Tambahkan port secara eksplisit
    
    # PDF configuration
    PDF_DIR = 'static/pdfs'
    
    # Application settings
    APP_NAME = 'Sistem Surat Izin Keluar Barang'
    COMPANY_NAME = 'PT PLN INDONESIA POWER'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        directories = [Config.PDF_DIR, 'static/uploads', 'logs']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"📁 Created directory: {directory}")
        
        # Log initialization
        print(f"🚀 {Config.APP_NAME}")
        print(f"🏢 {Config.COMPANY_NAME}")
        print(f"📊 Database: {Config.MYSQL_DB}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
        print(f"📁 PDF Directory: {Config.PDF_DIR}")

config = Config()