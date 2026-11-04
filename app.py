"""Prototype sistem administrasi persediaan ATK."""
import sqlite3
import streamlit as st
import database as db

st.set_page_config(page_title="Administrasi ATK", layout="wide")
db.init_db()


def selesai(pesan):
    st.session_state["pesan_sukses"] = pesan
    st.rerun()


def tampil_error(exc):
    if isinstance(exc, ValueError):
        st.error(str(exc))
    elif "FOREIGN KEY" in str(exc):
        st.error("Kategori masih digunakan atau pilihan kategori tidak valid.")
    else:
        st.error("Data tidak tersimpan. Periksa kode atau nama yang duplikat.")


def beranda():
    st.title("Administrasi Persediaan ATK")
    st.write("Kelola kategori dan pendataan persediaan alat tulis kantor.")
    jenis, rendah = db.ringkasan()
    kiri, kanan = st.columns(2)
    kiri.metric("Jenis barang", jenis)
    kanan.metric("Barang perlu ditambah", rendah)
    st.info("Mulai dari menu Kategori, kemudian masukkan data pada menu Barang.")
    st.caption("Stok adalah jumlah saat pendataan, bukan riwayat transaksi.")
    rows = [r for r in db.daftar_barang() if r["status"] == "Perlu ditambah"]
    st.subheader("Barang dengan stok rendah")
    tabel_barang(rows)


def tabel_barang(rows):
    if not rows:
        st.info("Tidak ada barang untuk ditampilkan.")
        return
    tampilan = [{
        "Kode": r["kode_barang"], "Nama": r["nama_barang"],
        "Kategori": r["nama_kategori"], "Satuan": r["satuan"],
        "Stok": r["stok"], "Minimum": r["stok_minimum"],
        "Status": r["status"],
    } for r in rows]
    st.dataframe(tampilan, hide_index=True, width="stretch")


def halaman_kategori():
    st.title("Kategori ATK")
    aksi = st.radio("Tindakan", ["Tambah", "Edit", "Hapus"],
                    horizontal=True, key="aksi_kategori")
    rows = db.daftar_kategori()
    if aksi == "Tambah":
        with st.form("form_kategori_baru", clear_on_submit=False):
            nama = st.text_input("Nama kategori", key="kategori_baru")
            simpan = st.form_submit_button("Simpan Kategori")
        if simpan:
            try:
                db.tambah_kategori(nama)
                selesai("Kategori berhasil ditambahkan.")
            except (ValueError, sqlite3.IntegrityError) as exc:
                tampil_error(exc)
    elif not rows:
        st.info("Belum ada kategori. Tambahkan kategori terlebih dahulu.")
    else:
        pilihan = {r["id_kategori"]: r for r in rows}
        identitas = st.selectbox("Pilih kategori", list(pilihan),
            format_func=lambda i: pilihan[i]["nama_kategori"],
            key=f"pilih_kategori_{aksi}")
        row = pilihan[identitas]
        if aksi == "Edit":
            with st.form(f"edit_kategori_{identitas}"):
                nama = st.text_input("Nama kategori",
                    value=row["nama_kategori"],
                    key=f"nama_kategori_{identitas}")
                simpan = st.form_submit_button("Simpan Perubahan")
            if simpan:
                try:
                    db.ubah_kategori(identitas, nama)
                    selesai("Kategori berhasil diperbarui.")
                except (ValueError, sqlite3.IntegrityError) as exc:
                    tampil_error(exc)
        else:
            st.warning(f"Kategori yang akan dihapus: {row['nama_kategori']}")
            yakin = st.checkbox("Saya mengonfirmasi penghapusan kategori",
                                key=f"konfirmasi_kategori_{identitas}")
            if st.button("Hapus Kategori", disabled=not yakin):
                try:
                    db.hapus_kategori(identitas)
                    selesai("Kategori berhasil dihapus.")
                except sqlite3.IntegrityError as exc:
                    tampil_error(exc)
    st.subheader("Daftar kategori")
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.info("Daftar kategori masih kosong.")


def form_barang(kategori, row=None):
    identitas = row["id_barang"] if row else "baru"
    prefix = f"edit_{identitas}" if row else "tambah"
    pilihan = {k["id_kategori"]: k["nama_kategori"] for k in kategori}
    ids = list(pilihan)
    satuan_opsi = ["buah", "rim", "pak", "kotak"]
    nilai = row or {"kode_barang": "", "nama_barang": "",
        "id_kategori": ids[0], "satuan": "buah", "stok": 0,
        "stok_minimum": 0}
    if nilai["satuan"] not in satuan_opsi:
        satuan_opsi.append(nilai["satuan"])
    with st.form(f"form_barang_{identitas}"):
        c1, c2 = st.columns(2)
        kode = c1.text_input("Kode barang", value=nilai["kode_barang"],
                             key=f"{prefix}_kode")
        nama = c2.text_input("Nama barang", value=nilai["nama_barang"],
                             key=f"{prefix}_nama")
        kat = c1.selectbox("Kategori", ids,
            index=ids.index(nilai["id_kategori"]),
            format_func=lambda i: pilihan[i], key=f"{prefix}_kategori")
        satuan = c2.selectbox("Satuan", satuan_opsi,
            index=satuan_opsi.index(nilai["satuan"]),
            key=f"{prefix}_satuan")
        stok = c1.number_input("Stok", min_value=0,
            value=nilai["stok"], step=1, key=f"{prefix}_stok")
        minimum = c2.number_input("Stok minimum", min_value=0,
            value=nilai["stok_minimum"], step=1,
            key=f"{prefix}_minimum")
        simpan = st.form_submit_button(
            "Simpan Perubahan" if row else "Simpan Barang")
    if simpan:
        try:
            args = (kode, nama, kat, satuan, int(stok), int(minimum))
            if row:
                db.ubah_barang(row["id_barang"], *args)
            else:
                db.tambah_barang(*args)
            selesai("Data barang berhasil disimpan.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            tampil_error(exc)


def halaman_barang():
    st.title("Data Barang ATK")
    kategori = db.daftar_kategori()
    if not kategori:
        st.info("Isi kategori terlebih dahulu melalui menu Kategori.")
        return
    aksi = st.radio("Tindakan", ["Tambah", "Edit", "Hapus"],
                    horizontal=True, key="aksi_barang")
    rows = db.daftar_barang()
    if aksi == "Tambah":
        form_barang(kategori)
    elif not rows:
        st.info("Belum ada barang yang dapat diedit atau dihapus.")
    else:
        pilihan = {r["id_barang"]: r for r in rows}
        identitas = st.selectbox("Pilih barang", list(pilihan),
            format_func=lambda i: (
                f"{pilihan[i]['kode_barang']} | {pilihan[i]['nama_barang']}"),
            key=f"pilih_barang_{aksi}")
        row = pilihan[identitas]
        if aksi == "Edit":
            form_barang(kategori, row)
        else:
            st.warning(f"Barang yang akan dihapus: {row['nama_barang']}")
            yakin = st.checkbox("Saya mengonfirmasi penghapusan barang",
                                key=f"konfirmasi_barang_{identitas}")
            if st.button("Hapus Barang", disabled=not yakin):
                db.hapus_barang(identitas)
                selesai("Barang berhasil dihapus.")
    st.subheader("Daftar persediaan")
    label = {None: "Semua kategori"}
    label.update({k["id_kategori"]: k["nama_kategori"] for k in kategori})
    filter_id = st.selectbox("Filter kategori", list(label),
        format_func=lambda i: label[i], key="filter_kategori")
    tabel_barang(db.daftar_barang(filter_id))


st.sidebar.title("Menu ATK")
menu = st.sidebar.radio("Halaman", ["Beranda", "Kategori", "Barang"])
if "pesan_sukses" in st.session_state:
    st.success(st.session_state.pop("pesan_sukses"))
if menu == "Beranda":
    beranda()
elif menu == "Kategori":
    halaman_kategori()
else:
    halaman_barang()
