"""Fungsi murni di file GUI (tanpa membuka jendela):
FR-01 validasi form alat, FR-02 format katalog & jadwal, FR-06 format dashboard."""
from datetime import date, time, timedelta

import pytest

import views.gui.operator_gui as operator_gui
import views.gui.owner_gui as owner_gui
import views.gui.penyewa_gui as penyewa_gui


# ---------- FR-01: parse_nominal & validasi_alat (operator) ----------
@pytest.mark.parametrize(
    "teks, harapan",
    [
        ("25000", 25000), ("25.000", 25000), ("1.250.000", 1250000),
        ("25.000,50", 25000.5), ("25,5", 25.5), ("Rp 25.000", 25000),
        ("25.5", 25.5), ("  50  ", 50),
    ],
)
def test_parse_nominal_format_indonesia(teks, harapan):
    assert operator_gui.parse_nominal(teks) == harapan


@pytest.mark.parametrize("teks", ["", "abc", "-5", "nan", "inf", "1e5", "25.00.0", "Rp"])
def test_parse_nominal_menolak_input_tidak_valid(teks):
    with pytest.raises(ValueError):
        operator_gui.parse_nominal(teks)


def test_validasi_alat_valid_mengembalikan_nilai_bersih():
    ok, hasil = operator_gui.validasi_alat("  Easel  ", "25.000,50", "3")

    assert ok is True
    assert hasil == ("Easel", 25000.5, 3)


@pytest.mark.parametrize(
    "nama, harga, stok",
    [
        ("", "25.000", "10"),        # nama kosong
        ("   ", "25.000", "10"),     # nama spasi saja
        ("Easel", "0", "10"),        # harga nol
        ("Easel", "abc", "10"),      # harga huruf
        ("Easel", "25.000", "-5"),   # stok negatif
        ("Easel", "25.000", "2.5"),  # stok desimal
        ("Easel", "25.000", ""),     # stok kosong
    ],
)
def test_validasi_alat_menolak(nama, harga, stok):
    ok, pesan = operator_gui.validasi_alat(nama, harga, stok)

    assert ok is False and isinstance(pesan, str) and pesan


def test_validasi_alat_stok_nol_boleh():
    ok, hasil = operator_gui.validasi_alat("Easel", "25.000", "0")
    assert ok is True and hasil[2] == 0


# ---------- format rupiah (tiga GUI memakai aturan yang sama) ----------
@pytest.mark.parametrize("modul", [operator_gui, penyewa_gui, owner_gui])
@pytest.mark.parametrize(
    "nilai, harapan",
    [(25000, "Rp 25.000"), (1250000, "Rp 1.250.000"), (25000.5, "Rp 25.000,50"),
     (0, "Rp 0"), (None, "Rp 0")],
)
def test_format_rupiah(modul, nilai, harapan):
    assert modul.format_rupiah(nilai) == harapan


# ---------- FR-02: format jam & jadwal (penyewa) ----------
@pytest.mark.parametrize(
    "nilai, harapan",
    [
        (timedelta(hours=10), "10.00"), (timedelta(hours=24), "24.00"),
        (time(9, 5), "09.05"), ("14:00:00", "14.00"), (None, None),
    ],
)
def test_format_jam(nilai, harapan):
    assert penyewa_gui.format_jam(nilai) == harapan


def test_format_tanggal():
    assert penyewa_gui.format_tanggal(date(2026, 11, 14)) == "14-11-2026"
    assert penyewa_gui.format_tanggal("2026-11-14") == "2026-11-14"


def test_slot_jadwal_satu_hari_dengan_jam():
    d = date(2026, 11, 14)
    assert penyewa_gui.format_slot_jadwal(
        d, d, timedelta(hours=10), timedelta(hours=12)) == ("14-11-2026", "10.00 - 12.00")


def test_slot_jadwal_beberapa_hari_tanpa_jam_dianggap_seharian():
    hasil = penyewa_gui.format_slot_jadwal(date(2026, 11, 14), date(2026, 11, 15), None, None)

    assert hasil == ("14-11-2026 s/d 15-11-2026", "Seharian")


def test_slot_jadwal_sampai_jam_24():
    d = date(2026, 11, 14)
    _, jam = penyewa_gui.format_slot_jadwal(d, d, timedelta(hours=20), timedelta(hours=24))
    assert jam == "20.00 - 24.00"


def test_daftar_tanggal_mulai_hari_ini_dan_berurutan():
    daftar = penyewa_gui.daftar_tanggal(5)

    assert len(daftar) == 5
    assert daftar[0] == date.today().isoformat()  # tanggal lampau tidak ditawarkan
    assert daftar[1] == (date.today() + timedelta(days=1)).isoformat()


def test_daftar_tanggal_bawaan_60_hari():
    assert len(penyewa_gui.daftar_tanggal()) == 60


def test_jam_tutup_gui_sama_dengan_controller():
    from controllers.transaksi_controller import TransaksiController

    assert penyewa_gui.JAM_TUTUP == TransaksiController.JAM_TUTUP == 22


# ---------- FR-06: owner ----------
def test_bulan_dari_tanggal_dan_teks():
    assert owner_gui._bulan_dari(date(2026, 11, 14)) == "2026-11"
    assert owner_gui._bulan_dari("2026-11-14") == "2026-11"
    assert owner_gui._bulan_dari(None) == ""
