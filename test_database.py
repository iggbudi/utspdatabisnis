"""Pengujian aturan bisnis dengan database sementara, bukan data mahasiswa."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent)
        spec = importlib.util.spec_from_file_location(
            "db_uji", Path(__file__).with_name("database.py"))
        self.db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.db)
        self.db.DB_PATH = Path(self.tmp.name) / "uji.db"
        self.db.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_crud_dan_persistensi(self):
        d = self.db
        k = d.tambah_kategori("Kertas")
        b = d.tambah_barang("atk001", "Kertas A4", k, "rim", 3, 5)
        row = d.daftar_barang()[0]
        self.assertEqual((row["kode_barang"], row["nama_kategori"]),
                         ("ATK001", "Kertas"))
        self.assertEqual(row["status"], "Perlu ditambah")
        d.ubah_barang(b, "ATK001", "Kertas A4", k, "rim", 8, 5)
        self.assertEqual(d.ringkasan(), (1, 0))
        d.init_db()
        self.assertEqual(d.daftar_barang()[0]["stok"], 8)
        d.hapus_barang(b)
        d.hapus_kategori(k)
        self.assertEqual(d.daftar_kategori(), [])

    def test_duplikasi_dan_input_kosong(self):
        d = self.db
        k = d.tambah_kategori("Alat Tulis")
        with self.assertRaises(sqlite3.IntegrityError):
            d.tambah_kategori("alat tulis")
        with self.assertRaises(ValueError):
            d.tambah_kategori("   ")
        d.tambah_barang("ATK001", "Pulpen", k, "buah", 25, 10)
        with self.assertRaises(sqlite3.IntegrityError):
            d.tambah_barang("atk001", "Pensil", k, "buah", 4, 2)
        with self.assertRaises(ValueError):
            d.tambah_barang("ATK002", " ", k, "buah", 4, 2)
        self.assertEqual(d.ringkasan()[0], 1)

    def test_foreign_key_dan_stok(self):
        d = self.db
        k = d.tambah_kategori("Kertas")
        for stok in (-1, 1.5):
            with self.assertRaises(ValueError):
                d.tambah_barang("ATK001", "A4", k, "rim", stok, 5)
        with self.assertRaises(sqlite3.IntegrityError):
            d.tambah_barang("ATK001", "A4", 999, "rim", 3, 5)
        d.tambah_barang("ATK001", "A4", k, "rim", 5, 5)
        with self.assertRaises(sqlite3.IntegrityError):
            d.hapus_kategori(k)
        self.assertEqual(len(d.daftar_kategori()), 1)
        self.assertEqual(d.ringkasan(), (1, 1))

    def test_filter_edit_kategori_dan_parameter(self):
        d = self.db
        k1 = d.tambah_kategori("Kertas")
        k2 = d.tambah_kategori("Arsip")
        d.tambah_barang("ATK001", "Kertas O'Neil", k1, "rim", 3, 5)
        d.tambah_barang("ATK002", "Map", k2, "buah", 15, 5)
        self.assertEqual(len(d.daftar_barang(k1)), 1)
        d.ubah_kategori(k1, "Kertas kantor")
        self.assertEqual(d.daftar_barang(k1)[0]["nama_kategori"],
                         "Kertas kantor")


if __name__ == "__main__":
    unittest.main(verbosity=2)
