#!/bin/bash
# Script untuk memulai aplikasi WISP Financial Admin
# dan menyimpan perubahan ke GitHub saat dihentikan.

# Fungsi cleanup_and_push tetap sama...
cleanup_and_push() {
    echo ""
    echo "========================================="
    echo "Server dihentikan."
    read -p "Simpan semua perubahan ke GitHub? (y/n): " choice
    echo "========================================="

    case "$choice" in 
      y|Y ) 
        echo "--> Menambahkan semua perubahan..."
        git add .
        commit_message="Update otomatis pada $(date +'%Y-%m-%d %H:%M:%S')"
        echo "--> Membuat commit dengan pesan: '$commit_message'"
        git commit -m "$commit_message"
        echo "--> Mengunggah ke GitHub..."
        git push
        echo "--> Selesai! Perubahan berhasil disimpan."
        ;;
      * ) 
        echo "--> Keluar tanpa menyimpan ke GitHub."
        ;;
    esac

    echo "========================================="
    exit 0
}

# Menjebak sinyal Ctrl+C (SIGINT)
trap cleanup_and_push SIGINT

# =======================================================
# BAGIAN BARU YANG DIPERBARUI
# =======================================================

echo "========================================="
echo "Menyiapkan lingkungan aplikasi..."
echo "========================================="

# 1. Pindah ke direktori proyek
cd ~/wisp-financial-admin

# 2. Cek apakah virtual environment (venv) sudah ada. Jika tidak, buat baru.
if [ ! -d "venv" ]; then
    echo "--> Virtual environment tidak ditemukan. Membuat venv baru..."
    python3 -m venv venv
fi

# 3. Aktifkan virtual environment
echo "--> Mengaktifkan virtual environment..."
source venv/bin/activate

# 4. Install/update paket dari requirements.txt
echo "--> Memeriksa dan menginstal dependensi paket..."
pip install -r requirements.txt

# =======================================================
# BAGIAN LAMA YANG TETAP SAMA
# =======================================================

echo ""
echo "========================================="
echo "Memulai WISP Financial Admin..."
echo "Tekan Ctrl+C untuk menghentikan server."
echo "========================================="

# 5. Jalankan server aplikasi Flask
export FLASK_APP=run.py
python3 run.py
