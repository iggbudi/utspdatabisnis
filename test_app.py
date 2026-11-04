"""Uji alur UI memakai AppTest dan database yang terisolasi."""
from pathlib import Path
import tempfile
import unittest
from streamlit.testing.v1 import AppTest
import database as db


class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent)
        self.original = db.DB_PATH
        db.DB_PATH = Path(self.tmp.name) / "uji.db"
        self.app = AppTest.from_file(
            str(Path(__file__).with_name("app.py")), default_timeout=15).run()

    def tearDown(self):
        db.DB_PATH = self.original
        self.tmp.cleanup()

    def test_kategori_barang_edit_dan_hapus(self):
        a = self.app
        self.assertEqual(len(a.exception), 0)
        a.sidebar.radio[0].set_value("Kategori").run()
        a.text_input(key="kategori_baru").set_value("Kertas")
        a.button[0].click().run()
        self.assertEqual(db.daftar_kategori()[0]["nama_kategori"], "Kertas")
        a.sidebar.radio[0].set_value("Barang").run()
        a.text_input(key="tambah_kode").set_value("atk001")
        a.text_input(key="tambah_nama").set_value("Kertas A4")
        a.selectbox(key="tambah_satuan").set_value("rim")
        a.number_input(key="tambah_stok").set_value(3)
        a.number_input(key="tambah_minimum").set_value(5)
        a.button[0].click().run()
        self.assertEqual(db.ringkasan(), (1, 1))
        a.radio(key="aksi_barang").set_value("Edit").run()
        a.number_input[0].set_value(8)
        a.button[0].click().run()
        self.assertEqual(db.ringkasan(), (1, 0))
        a.radio(key="aksi_barang").set_value("Hapus").run()
        a.checkbox[0].check().run()
        a.button[0].click().run()
        self.assertEqual(db.daftar_barang(), [])
        self.assertEqual(len(a.exception), 0)

    def test_barang_tanpa_kategori(self):
        a = self.app
        a.sidebar.radio[0].set_value("Barang").run()
        self.assertEqual(len(a.exception), 0)
        self.assertIn("kategori", a.info[0].value.lower())
        self.assertEqual(len(a.text_input), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
