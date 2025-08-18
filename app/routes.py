import os
import secrets
from flask import render_template, url_for, flash, redirect, request, Response, jsonify
from app import app, db, bcrypt
from app.models import User, Customer, ServicePackage, Invoice, Expense, Setting
from app.forms import (LoginForm, CustomerForm, ServicePackageForm, 
                       GenerateInvoicesForm, PaymentForm, ExpenseForm, SettingsForm)
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, extract, or_
from flask_login import login_user, current_user, logout_user, login_required
import openpyxl
from io import BytesIO

# --- FUNGSI HELPER BARU UNTUK SIMPAN GAMBAR ---
def save_receipt_picture(form_picture, customer_name, invoice):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)

    # Membuat nama folder berdasarkan tahun dan bulan
    folder_name = f"{invoice.tahun}_{invoice.bulan:02d}"
    upload_folder = os.path.join(app.root_path, 'static/uploads', folder_name)

    # Membuat folder jika belum ada
    os.makedirs(upload_folder, exist_ok=True)

    # Membuat nama file yang deskriptif dan unik
    picture_fn = f"{customer_name.replace(' ', '_')}_{random_hex}{f_ext}"
    picture_path = os.path.join(upload_folder, picture_fn)

    # Simpan gambar
    form_picture.save(picture_path)

    # Return path relatif untuk disimpan di database
    return os.path.join(folder_name, picture_fn)

# ... (Sisa rute tidak berubah sampai 'pay_invoice') ...
def get_settings():
    settings_db = Setting.query.all()
    settings = {s.key: s.value for s in settings_db}
    defaults = {'target_pendapatan': '6500000', 'alokasi_belanja': '3000000', 'setoran_balik_modal': '2500000', 'persen_anda': '80.0', 'persen_investor': '20.0'}
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
    return settings

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Gagal. Silakan periksa email dan password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    now = datetime.utcnow()
    current_month, current_year = now.month, now.year
    revenue_this_month = db.session.query(func.sum(Invoice.jumlah)).filter(Invoice.bulan == current_month, Invoice.tahun == current_year, Invoice.status == 'Lunas').scalar() or 0
    unpaid_this_month = db.session.query(func.sum(Invoice.jumlah)).filter(Invoice.bulan == current_month, Invoice.tahun == current_year, Invoice.status == 'Belum Lunas').scalar() or 0
    expense_this_month = db.session.query(func.sum(Expense.jumlah)).filter(extract('month', Expense.tanggal) == current_month, extract('year', Expense.tanggal) == current_year).scalar() or 0
    active_customers = db.session.query(func.count(Customer.id)).filter_by(status='Aktif').scalar()
    stats = {'revenue_current_month': revenue_this_month, 'unpaid_current_month': unpaid_this_month, 'expense_current_month': expense_this_month, 'active_customers': active_customers}
    recent_invoices = Invoice.query.order_by(Invoice.tanggal_buat.desc()).limit(5).all()
    return render_template('dashboard.html', stats=stats, recent_invoices=recent_invoices, current_month_name=now.strftime('%B'), current_year=current_year)

@app.route("/api/financial_summary")
@login_required
def api_financial_summary():
    labels, revenue_data, expense_data = [], [], []
    today = datetime.utcnow()
    for i in range(5, -1, -1):
        target_date = today - relativedelta(months=i)
        month, year = target_date.month, target_date.year
        labels.append(target_date.strftime("%b %Y"))
        revenue = db.session.query(func.sum(Invoice.jumlah)).filter(Invoice.bulan == month, Invoice.tahun == year, Invoice.status == 'Lunas').scalar() or 0
        revenue_data.append(revenue)
        expense = db.session.query(func.sum(Expense.jumlah)).filter(extract('month', Expense.tanggal) == month, extract('year', Expense.tanggal) == year).scalar() or 0
        expense_data.append(expense)
    return jsonify({'labels': labels, 'revenue': revenue_data, 'expenses': expense_data})

@app.route('/customers')
@login_required
def customers():
    query = Customer.query
    search = request.args.get('search')
    if search:
        query = query.filter(or_(Customer.nama.ilike(f'%{search}%'), Customer.alamat.ilike(f'%{search}%')))
    all_customers = query.order_by(Customer.nama).all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customer/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    form = CustomerForm()
    form.package_id.choices = [(0, "--- Pilih Paket (Opsional) ---")] + [(p.id, p.nama_paket) for p in ServicePackage.query.order_by('nama_paket').all()]
    if form.validate_on_submit():
        pkg_id = form.package_id.data if form.package_id.data != 0 else None
        new_customer = Customer(
            nama=form.nama.data, 
            alamat=form.alamat.data, 
            telepon=form.telepon.data, 
            package_id=pkg_id,
            status=form.status.data,
            tanggal_bergabung=form.tanggal_bergabung.data
        )
        db.session.add(new_customer)
        db.session.commit()
        flash('Pelanggan baru berhasil ditambahkan!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', title='Tambah Pelanggan', form=form)

@app.route('/customer/<int:customer_id>/update', methods=['GET', 'POST'])
@login_required
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm()
    form.package_id.choices = [(0, "--- Pilih Paket (Opsional) ---")] + [(p.id, p.nama_paket) for p in ServicePackage.query.order_by('nama_paket').all()]
    if form.validate_on_submit():
        pkg_id = form.package_id.data if form.package_id.data != 0 else None
        customer.nama = form.nama.data
        customer.alamat = form.alamat.data
        customer.telepon = form.telepon.data
        customer.package_id = pkg_id
        customer.status = form.status.data
        customer.tanggal_bergabung = form.tanggal_bergabung.data
        db.session.commit()
        flash('Data pelanggan berhasil diperbarui!', 'success')
        return redirect(url_for('customers'))
    elif request.method == 'GET':
        form.nama.data = customer.nama
        form.alamat.data = customer.alamat
        form.telepon.data = customer.telepon
        form.package_id.data = customer.package_id or 0
        form.status.data = customer.status
        form.tanggal_bergabung.data = customer.tanggal_bergabung
    return render_template('customer_form.html', title='Edit Pelanggan', form=form)

@app.route('/customer/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Pelanggan berhasil dihapus.', 'info')
    return redirect(url_for('customers'))

@app.route('/invoices', methods=['GET'])
@login_required
def invoices():
    gen_form = GenerateInvoicesForm()
    payment_form = PaymentForm()
    gen_form.bulan.data = datetime.utcnow().month
    all_invoices = Invoice.query.order_by(Invoice.tahun.desc(), Invoice.bulan.desc(), Invoice.id.desc()).all()
    return render_template('invoices.html', invoices=all_invoices, gen_form=gen_form, payment_form=payment_form)

# --- RUTE PEMBAYARAN (DIPERBARUI) ---
@app.route('/invoice/<int:invoice_id>/pay', methods=['POST'])
@login_required
def pay_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    form = PaymentForm()
    if form.validate_on_submit():
        if form.nota.data:
            # Mengirim objek invoice ke fungsi save
            picture_file = save_receipt_picture(form.nota.data, invoice.customer.nama, invoice)
            invoice.bukti_pembayaran = picture_file

        invoice.status = 'Lunas'
        invoice.tanggal_lunas = form.tanggal_lunas.data
        db.session.commit()
        flash(f'Tagihan untuk {invoice.customer.nama} telah ditandai lunas.', 'success')
    else:
        # Loop melalui error dan tampilkan
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error di field '{getattr(form, field).label.text}': {error}", 'danger')
    return redirect(url_for('invoices'))

# ... (Sisa rute tidak berubah) ...
@app.route('/invoices/generate', methods=['POST'])
@login_required
def generate_invoices():
    form = GenerateInvoicesForm()
    if form.validate_on_submit():
        bulan, tahun = form.bulan.data, form.tahun.data
        periode_tagihan = date(tahun, bulan, 1)
        customers_to_bill = Customer.query.filter(Customer.status == 'Aktif', func.date(Customer.tanggal_bergabung) <= periode_tagihan).all()
        count = 0
        for cust in customers_to_bill:
            existing_invoice = Invoice.query.filter_by(customer_id=cust.id, bulan=bulan, tahun=tahun).first()
            if not existing_invoice and cust.package:
                invoice = Invoice(customer_id=cust.id, bulan=bulan, tahun=tahun, jumlah=cust.package.harga, status='Belum Lunas')
                db.session.add(invoice)
                count += 1
        db.session.commit()
        if count > 0: flash(f'{count} tagihan baru untuk periode {bulan}/{tahun} berhasil dibuat!', 'success')
        else: flash(f'Tidak ada tagihan baru yang dibuat. Semua pelanggan yang valid sudah punya tagihan untuk periode ini.', 'info')
    else: flash('Data formulir tidak valid.', 'danger')
    return redirect(url_for('invoices'))
@app.route('/financial-report', methods=['GET', 'POST'])
@login_required
def financial_report():
    form = GenerateInvoicesForm()
    report_data = None
    if request.method == 'POST' and form.validate_on_submit():
        bulan, tahun = form.bulan.data, form.tahun.data
        settings = get_settings()
        pendapatan_kotor = db.session.query(func.sum(Invoice.jumlah)).filter(Invoice.bulan == bulan, Invoice.tahun == tahun, Invoice.status == 'Lunas').scalar() or 0
        total_pengeluaran = db.session.query(func.sum(Expense.jumlah)).filter(extract('month', Expense.tanggal) == bulan, extract('year', Expense.tanggal) == tahun).scalar() or 0
        rincian_pendapatan = Invoice.query.filter(Invoice.bulan == bulan, Invoice.tahun == tahun, Invoice.status == 'Lunas').all()
        rincian_pengeluaran = Expense.query.filter(extract('month', Expense.tanggal) == bulan, extract('year', Expense.tanggal) == tahun).all()
        report_data = {'period': f"{form.bulan.choices[bulan-1][1]} {tahun}", 'bulan': bulan, 'tahun': tahun, 'pendapatan_kotor': pendapatan_kotor, 'total_pengeluaran': total_pengeluaran, 'rincian_pendapatan': rincian_pendapatan, 'rincian_pengeluaran': rincian_pengeluaran, 'target_pendapatan': int(settings['target_pendapatan']), 'laba_bersih': None}
        if pendapatan_kotor >= int(settings['target_pendapatan']):
            alokasi_belanja, setoran_balik_modal, persen_anda, persen_investor = int(settings['alokasi_belanja']), int(settings['setoran_balik_modal']), float(settings['persen_anda']), float(settings['persen_investor'])
            dana_siap_bagi = pendapatan_kotor - alokasi_belanja - setoran_balik_modal
            report_data.update({'alokasi_belanja': alokasi_belanja, 'setoran_balik_modal': setoran_balik_modal, 'dana_siap_bagi': dana_siap_bagi, 'persen_anda': persen_anda, 'persen_investor': persen_investor, 'bagian_anda': dana_siap_bagi * (persen_anda / 100), 'bagian_investor': dana_siap_bagi * (persen_investor / 100), 'laba_bersih': dana_siap_bagi})
    return render_template('financial_report.html', form=form, report_data=report_data)
@app.route('/export/financial-report')
@login_required
def export_financial_report():
    bulan = request.args.get('bulan', type=int)
    tahun = request.args.get('tahun', type=int)
    if not bulan or not tahun:
        flash('Periode tidak valid untuk export.', 'danger')
        return redirect(url_for('financial_report'))
    settings = get_settings()
    pendapatan_kotor = db.session.query(func.sum(Invoice.jumlah)).filter(Invoice.bulan == bulan, Invoice.tahun == tahun, Invoice.status == 'Lunas').scalar() or 0
    total_pengeluaran = db.session.query(func.sum(Expense.jumlah)).filter(extract('month', Expense.tanggal) == bulan, extract('year', Expense.tanggal) == tahun).scalar() or 0
    rincian_pendapatan = Invoice.query.filter(Invoice.bulan == bulan, Invoice.tahun == tahun, Invoice.status == 'Lunas').all()
    rincian_pengeluaran = Expense.query.filter(extract('month', Expense.tanggal) == bulan, extract('year', Expense.tanggal) == tahun).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Laporan {bulan}-{tahun}"
    ws.append(['Laporan Keuangan', f"Periode: {datetime(2000, bulan, 1).strftime('%B')} {tahun}"])
    ws.append([])
    ws.append(['', 'Pendapatan Kotor', pendapatan_kotor])
    ws.append(['', 'Total Pengeluaran', total_pengeluaran])
    ws.append([])
    if pendapatan_kotor >= int(settings['target_pendapatan']):
        alokasi_belanja, setoran_balik_modal, persen_anda, persen_investor = int(settings['alokasi_belanja']), int(settings['setoran_balik_modal']), float(settings['persen_anda']), float(settings['persen_investor'])
        dana_siap_bagi = pendapatan_kotor - alokasi_belanja - setoran_balik_modal
        ws.append(['Kalkulasi Bagi Hasil'])
        ws.append(['', 'Alokasi Belanja', alokasi_belanja])
        ws.append(['', 'Setoran Balik Modal', setoran_balik_modal])
        ws.append(['', 'Dana Siap Bagi', dana_siap_bagi])
        ws.append(['', f'Bagian Anda ({persen_anda}%)', dana_siap_bagi * (persen_anda / 100)])
        ws.append(['', f'Bagian Investor ({persen_investor}%)', dana_siap_bagi * (persen_investor / 100)])
    ws.append([]); ws.append(['Rincian Pendapatan']); ws.append(['Tanggal Lunas', 'Pelanggan', 'Jumlah'])
    for inv in rincian_pendapatan:
        ws.append([inv.tanggal_lunas.strftime('%Y-%m-%d'), inv.customer.nama, inv.jumlah])
    ws.append([]); ws.append(['Rincian Pengeluaran']); ws.append(['Tanggal', 'Deskripsi', 'Kategori', 'Jumlah'])
    for exp in rincian_pengeluaran:
        ws.append([exp.tanggal.strftime('%Y-%m-%d'), exp.deskripsi, exp.kategori, exp.jumlah])
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return Response(excel_file, headers={'Content-Disposition': f'attachment; filename=laporan_{bulan}_{tahun}.xlsx', 'Content-type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    if form.validate_on_submit():
        for key, value in form.data.items():
            if key not in ['csrf_token', 'submit']:
                setting = Setting.query.get(key)
                if setting: setting.value = str(value)
                else: db.session.add(Setting(key=key, value=str(value)))
        db.session.commit()
        flash('Pengaturan berhasil disimpan!', 'success')
        return redirect(url_for('settings'))
    elif request.method == 'GET':
        settings_data = get_settings()
        form.target_pendapatan.data = int(settings_data['target_pendapatan'])
        form.alokasi_belanja.data = int(settings_data['alokasi_belanja'])
        form.setoran_balik_modal.data = int(settings_data['setoran_balik_modal'])
        form.persen_anda.data = float(settings_data['persen_anda'])
        form.persen_investor.data = float(settings_data['persen_investor'])
    return render_template('settings.html', form=form)
@app.route('/expense/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    form = ExpenseForm()
    if form.validate_on_submit():
        expense.tanggal, expense.deskripsi, expense.kategori, expense.jumlah = form.tanggal.data, form.deskripsi.data, form.kategori.data, form.jumlah.data
        db.session.commit()
        flash('Data pengeluaran berhasil diperbarui!', 'success')
        return redirect(url_for('expenses'))
    elif request.method == 'GET':
        form.tanggal.data, form.deskripsi.data, form.kategori.data, form.jumlah.data = expense.tanggal, expense.deskripsi, expense.kategori, expense.jumlah
    return render_template('edit_expense.html', form=form)
@app.route('/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Pengeluaran berhasil dihapus.', 'info')
    return redirect(url_for('expenses'))
@app.route('/service-packages')
@login_required
def service_packages():
    packages = ServicePackage.query.all()
    return render_template('service_packages.html', packages=packages)
@app.route('/service-package/add', methods=['GET', 'POST'])
@login_required
def add_service_package():
    form = ServicePackageForm()
    if form.validate_on_submit():
        package = ServicePackage(nama_paket=form.nama_paket.data, kecepatan=form.kecepatan.data, harga=form.harga.data)
        db.session.add(package)
        db.session.commit()
        flash('Paket layanan baru berhasil ditambahkan!', 'success')
        return redirect(url_for('service_packages'))
    return render_template('service_package_form.html', title='Tambah Paket Layanan', form=form)
@app.route('/service-package/<int:package_id>/update', methods=['GET', 'POST'])
@login_required
def update_service_package(package_id):
    package = ServicePackage.query.get_or_404(package_id)
    form = ServicePackageForm()
    if form.validate_on_submit():
        package.nama_paket, package.kecepatan, package.harga = form.nama_paket.data, form.kecepatan.data, form.harga.data
        db.session.commit()
        flash('Paket layanan berhasil diperbarui!', 'success')
        return redirect(url_for('service_packages'))
    elif request.method == 'GET':
        form.nama_paket.data, form.kecepatan.data, form.harga.data = package.nama_paket, package.kecepatan, package.harga
    return render_template('service_package_form.html', title='Edit Paket Layanan', form=form)
@app.route('/service-package/<int:package_id>/delete', methods=['POST'])
@login_required
def delete_service_package(package_id):
    package = ServicePackage.query.get_or_404(package_id)
    db.session.delete(package)
    db.session.commit()
    flash('Paket layanan berhasil dihapus.', 'info')
    return redirect(url_for('service_packages'))
@app.route('/expenses', methods=['GET'])
@login_required
def expenses():
    form = ExpenseForm()
    all_expenses = Expense.query.order_by(Expense.tanggal.desc()).all()
    return render_template('expenses.html', expenses=all_expenses, form=form)
@app.route('/expense/add', methods=['POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(deskripsi=form.deskripsi.data, jumlah=form.jumlah.data, kategori=form.kategori.data, tanggal=form.tanggal.data)
        db.session.add(expense)
        db.session.commit()
        flash('Pengeluaran baru berhasil ditambahkan!', 'success')
    else:
        flash('Gagal menambahkan pengeluaran. Periksa kembali data Anda.', 'danger')
    return redirect(url_for('expenses'))
