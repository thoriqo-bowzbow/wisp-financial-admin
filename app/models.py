from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(200), nullable=False)
    telepon = db.Column(db.String(20), nullable=False, unique=True)
    package_id = db.Column(db.Integer, db.ForeignKey('service_package.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Aktif')
    tanggal_bergabung = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    package = db.relationship('ServicePackage', backref=db.backref('customers', lazy=True))
    # --- PERBAIKAN PENTING DI SINI ---
    # Aturan ini memberitahu database: "Jika customer ini dihapus, hapus juga semua tagihannya"
    invoices = db.relationship('Invoice', backref='customer', lazy=True, cascade="all, delete-orphan")

class ServicePackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_paket = db.Column(db.String(100), nullable=False)
    kecepatan = db.Column(db.Integer, nullable=False)
    harga = db.Column(db.Integer, nullable=False)
        
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # --- PERBAIKAN KECIL DI SINI ---
    # backref='customer' sudah didefinisikan di model Customer, jadi tidak perlu ada di sini lagi.
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    bulan = db.Column(db.Integer, nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Belum Lunas')
    tanggal_buat = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tanggal_lunas = db.Column(db.DateTime, nullable=True)
        
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deskripsi = db.Column(db.String(200), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    kategori = db.Column(db.String(50), nullable=False, default='Operasional')
    tanggal = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(200), nullable=False)