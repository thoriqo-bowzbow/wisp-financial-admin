# Venous Financial

Aplikasi web administrasi keuangan untuk usaha WiFi (WISP), dibangun dengan Python Flask dan SQLite.

---

## Cara Menjalankan Aplikasi (Lokal)

1.  **Buka Terminal** dan masuk ke direktori proyek:
    ```bash
    cd ~/wisp-financial-admin
    ```

2.  **Aktifkan Virtual Environment**:
    ```bash
    source venv/bin/activate
    ```

3.  **Jalankan Server**:
    ```bash
    python3 run.py
    ```
    Aplikasi akan berjalan di `http://192.168.x.x:5000`.

---

## Manajemen Pengguna (Admin)

Untuk membuat akun admin baru, jalankan perintah berikut dari terminal di dalam direktori proyek (dengan venv aktif):

```bash
export FLASK_APP=run.py
flask create-user <username> <email> <password>

## Manajemen Database (Migrasi)
Setiap kali ada perubahan pada file app/models.py, jalankan dua perintah berikut untuk memperbarui database tanpa menghapus data:

Buat file migrasi:

flask db migrate -m "Pesan singkat tentang perubahan"

Terapkan perubahan:

flask db upgrade

Simpan file tersebut. Sekarang, siapa pun (termasuk dirimu di masa depan) akan tahu persis cara menggunakan dan mengelola aplikasi ini.