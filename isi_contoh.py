"""Jalankan sekali pada database latihan kosong untuk mengisi data contoh."""
import database as db

db.init_db()
if db.daftar_kategori() or db.daftar_barang():
    print("Database sudah berisi data. Tidak ada data yang diubah.")
else:
    alat = db.tambah_kategori("Alat Tulis")
    kertas = db.tambah_kategori("Kertas")
    arsip = db.tambah_kategori("Perlengkapan Arsip")
    db.tambah_barang("ATK001", "Pulpen hitam", alat, "buah", 25, 10)
    db.tambah_barang("ATK002", "Kertas A4", kertas, "rim", 3, 5)
    db.tambah_barang("ATK003", "Map arsip", arsip, "buah", 15, 5)
    print("Tiga kategori dan tiga barang contoh berhasil ditambahkan.")
