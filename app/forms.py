from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, TextAreaField, FloatField, PasswordField, BooleanField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, NumberRange, Email, EqualTo, ValidationError
from datetime import datetime
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class CustomerForm(FlaskForm):
    nama = StringField('Nama Pelanggan', validators=[DataRequired(), Length(min=3, max=100)])
    alamat = StringField('Alamat', validators=[DataRequired(), Length(min=5, max=200)])
    telepon = StringField('Nomor Telepon', validators=[DataRequired(), Length(min=8, max=20)])
    package_id = SelectField('Paket Layanan', coerce=int, validators=[DataRequired()])
    status = SelectField('Status Pelanggan', choices=[('Aktif', 'Aktif'), ('Nonaktif', 'Nonaktif'), ('Isolir', 'Isolir')], validators=[DataRequired()])
    submit = SubmitField('Simpan')

class ServicePackageForm(FlaskForm):
    nama_paket = StringField('Nama Paket', validators=[DataRequired(), Length(min=3, max=100)])
    kecepatan = IntegerField('Kecepatan (Mbps)', validators=[DataRequired(), NumberRange(min=1)])
    harga = IntegerField('Harga (Rp)', validators=[DataRequired(), NumberRange(min=1000)])
    submit = SubmitField('Simpan Paket')

class GenerateInvoicesForm(FlaskForm):
    bulan = SelectField('Bulan', coerce=int, choices=[(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)])
    tahun = IntegerField('Tahun', default=datetime.utcnow().year, validators=[DataRequired()])
    submit = SubmitField('Generate Tagihan untuk Periode Ini')

class PaymentForm(FlaskForm):
    tanggal_lunas = DateField('Tanggal Pembayaran', format='%Y-%m-%d', default=datetime.utcnow, validators=[DataRequired()])
    submit = SubmitField('Simpan Pembayaran')

class ExpenseForm(FlaskForm):
    deskripsi = TextAreaField('Deskripsi', validators=[DataRequired(), Length(min=3, max=200)])
    jumlah = IntegerField('Jumlah (Rp)', validators=[DataRequired(), NumberRange(min=1)])
    kategori = SelectField('Kategori', choices=[('Operasional', 'Operasional'), ('Perangkat', 'Perangkat'), ('Gaji', 'Gaji'), ('Lainnya', 'Lainnya')], validators=[DataRequired()])
    tanggal = DateField('Tanggal Pengeluaran', format='%Y-%m-%d', default=datetime.utcnow, validators=[DataRequired()])
    submit = SubmitField('Simpan Pengeluaran')

class SettingsForm(FlaskForm):
    target_pendapatan = IntegerField('Target Pendapatan Kotor Minimum (Rp)', validators=[DataRequired()])
    alokasi_belanja = IntegerField('Alokasi Belanja Bulanan (Rp)', validators=[DataRequired()])
    setoran_balik_modal = IntegerField('Setoran Balik Modal per Bulan (Rp)', validators=[DataRequired()])
    persen_anda = FloatField('Persentase Bagi Hasil Anda (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    persen_investor = FloatField('Persentase Bagi Hasil Investor (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Simpan Pengaturan')
