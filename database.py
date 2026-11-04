"""Operasi database untuk studi kasus persediaan ATK."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().with_name("atk.db")


@contextmanager
def koneksi():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with koneksi() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kategori (
                id_kategori INTEGER PRIMARY KEY,
                nama_kategori TEXT NOT NULL COLLATE NOCASE UNIQUE,
                CHECK (length(trim(nama_kategori)) > 0)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS barang (
                id_barang INTEGER PRIMARY KEY,
                kode_barang TEXT NOT NULL COLLATE NOCASE UNIQUE,
                nama_barang TEXT NOT NULL,
                id_kategori INTEGER NOT NULL,
                satuan TEXT NOT NULL,
                stok INTEGER NOT NULL DEFAULT 0,
                stok_minimum INTEGER NOT NULL DEFAULT 0,
                CHECK (length(trim(kode_barang)) > 0),
                CHECK (length(trim(nama_barang)) > 0),
                CHECK (length(trim(satuan)) > 0),
                CHECK (typeof(stok) = 'integer' AND stok >= 0),
                CHECK (typeof(stok_minimum) = 'integer'
                       AND stok_minimum >= 0),
                FOREIGN KEY (id_kategori)
                    REFERENCES kategori(id_kategori)
                    ON DELETE RESTRICT
            )
        """)


def teks_wajib(nilai, label):
    hasil = str(nilai).strip() if nilai is not None else ""
    if not hasil:
        raise ValueError(f"{label} wajib diisi.")
    return hasil


def daftar_kategori():
    with koneksi() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM kategori ORDER BY nama_kategori")]


def tambah_kategori(nama):
    nama = teks_wajib(nama, "Nama kategori")
    with koneksi() as conn:
        cur = conn.execute(
            "INSERT INTO kategori (nama_kategori) VALUES (?)", (nama,))
        return cur.lastrowid


def ubah_kategori(id_kategori, nama):
    nama = teks_wajib(nama, "Nama kategori")
    with koneksi() as conn:
        conn.execute("""
            UPDATE kategori SET nama_kategori = ?
            WHERE id_kategori = ?
        """, (nama, id_kategori))


def hapus_kategori(id_kategori):
    with koneksi() as conn:
        conn.execute("DELETE FROM kategori WHERE id_kategori = ?",
                     (id_kategori,))


def validasi_barang(kode, nama, satuan, stok, minimum):
    kode = teks_wajib(kode, "Kode barang").upper()
    nama = teks_wajib(nama, "Nama barang")
    satuan = teks_wajib(satuan, "Satuan")
    for label, nilai in (("Stok", stok), ("Stok minimum", minimum)):
        if type(nilai) is not int or nilai < 0:
            raise ValueError(f"{label} harus bilangan bulat minimal 0.")
    return kode, nama, satuan


def tambah_barang(kode, nama, kategori, satuan, stok, minimum):
    kode, nama, satuan = validasi_barang(
        kode, nama, satuan, stok, minimum)
    with koneksi() as conn:
        cur = conn.execute("""
            INSERT INTO barang
                (kode_barang, nama_barang, id_kategori,
                 satuan, stok, stok_minimum)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (kode, nama, kategori, satuan, stok, minimum))
        return cur.lastrowid


def ubah_barang(id_barang, kode, nama, kategori, satuan, stok, minimum):
    kode, nama, satuan = validasi_barang(
        kode, nama, satuan, stok, minimum)
    with koneksi() as conn:
        conn.execute("""
            UPDATE barang SET kode_barang = ?, nama_barang = ?,
                id_kategori = ?, satuan = ?, stok = ?, stok_minimum = ?
            WHERE id_barang = ?
        """, (kode, nama, kategori, satuan, stok, minimum, id_barang))


def hapus_barang(id_barang):
    with koneksi() as conn:
        conn.execute("DELETE FROM barang WHERE id_barang = ?",
                     (id_barang,))


def daftar_barang(id_kategori=None):
    sql = """
        SELECT b.*, k.nama_kategori,
            CASE WHEN b.stok <= b.stok_minimum
                 THEN 'Perlu ditambah' ELSE 'Cukup' END AS status
        FROM barang AS b
        JOIN kategori AS k ON b.id_kategori = k.id_kategori
    """
    params = ()
    if id_kategori is not None:
        sql += " WHERE b.id_kategori = ?"
        params = (id_kategori,)
    sql += " ORDER BY b.kode_barang"
    with koneksi() as conn:
        return [dict(r) for r in conn.execute(sql, params)]


def ringkasan():
    with koneksi() as conn:
        r = conn.execute("""
            SELECT COUNT(*) AS jenis,
                COALESCE(SUM(CASE WHEN stok <= stok_minimum
                    THEN 1 ELSE 0 END), 0) AS rendah
            FROM barang
        """).fetchone()
        return r["jenis"], r["rendah"]


if __name__ == "__main__":
    init_db()
    print(f"Database siap di {DB_PATH}")
