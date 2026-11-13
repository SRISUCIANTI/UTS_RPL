"""FR-05: Manajemen Pengembalian & Denda (PengembalianController)."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from controllers.pengembalian_controller import PengembalianController as PC
from models.pengembalian_model import PengembalianModel as RealPM

PM = "controllers.pengembalian_controller.PengembalianModel"
TM = "controllers.pengembalian_controller.TransaksiModel"
AM = "controllers.pengembalian_controller.AlatModel"


def trx(status="Lunas", sewa=date(2026, 11, 8), rencana=date(2026, 11, 10)):
    return {"status_transaksi": status, "tgl_sewa": sewa,
            "tgl_kembali_rencana": rencana, "nama_lengkap": "Kila"}


def pasang_model(pm, data):
    pm.getTransaksi.return_value = data
    pm.hitungDenda.side_effect = RealPM.hitungDenda  # pakai aturan denda asli
    pm.prosesPengembalian.return_value = True


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_tepat_waktu_tanpa_denda(pm, tm, am):
    pasang_model(pm, trx())
    tm.lihatDetail.return_value = []

    ok, pesan = PC.proses_kembali(1, "2026-11-10")

    assert ok is True and "Tidak ada denda" in pesan
    pm.prosesPengembalian.assert_called_once_with(1, "2026-11-10", 0)


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_terlambat_3_hari_denda_60000(pm, tm, am):
    pasang_model(pm, trx())
    tm.lihatDetail.return_value = []

    ok, pesan = PC.proses_kembali(1, "2026-11-13")

    assert ok is True
    assert "Terlambat 3 hari" in pesan and "60,000" in pesan
    pm.prosesPengembalian.assert_called_once_with(1, "2026-11-13", 60000)


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_lebih_awal_tanpa_denda(pm, tm, am):
    pasang_model(pm, trx())
    tm.lihatDetail.return_value = []

    ok, _ = PC.proses_kembali(1, "2026-11-09")

    assert ok is True
    assert pm.prosesPengembalian.call_args[0][2] == 0


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_tanggal_kosong_memakai_hari_ini(pm, tm, am):
    hari_ini = date.today()
    pasang_model(pm, trx(sewa=hari_ini - timedelta(days=2), rencana=hari_ini))
    tm.lihatDetail.return_value = []

    ok, _ = PC.proses_kembali(1, "")

    assert ok is True
    pm.prosesPengembalian.assert_called_once_with(1, hari_ini.strftime("%Y-%m-%d"), 0)


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_memulihkan_stok_alat_tetapi_bukan_studio(pm, tm, am):
    pasang_model(pm, trx())
    tm.lihatDetail.return_value = [
        {"id_alat": 3, "nama_alat": "Easel", "jumlah": 2, "subtotal": 50000},
        {"id_alat": None, "id_studio": 1, "nama_alat": None, "jumlah": 2, "subtotal": 100000},
    ]
    am.ubahStok.return_value = True

    ok, pesan = PC.proses_kembali(1, "2026-11-10")

    assert ok is True and "Easel x2" in pesan
    am.ubahStok.assert_called_once_with(3, 2)


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_id_bukan_angka(pm, tm, am):
    ok, pesan = PC.proses_kembali("abc")
    assert ok is False and "angka" in pesan


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_transaksi_tidak_ditemukan(pm, tm, am):
    pm.getTransaksi.return_value = None
    ok, pesan = PC.proses_kembali(99)
    assert ok is False and "tidak ditemukan" in pesan


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_transaksi_sudah_selesai_tidak_bisa_diulang(pm, tm, am):
    pm.getTransaksi.return_value = trx(status="Selesai")

    ok, pesan = PC.proses_kembali(1, "2026-11-10")

    assert ok is False and "sudah Selesai" in pesan
    pm.prosesPengembalian.assert_not_called()
    am.ubahStok.assert_not_called()


@pytest.mark.parametrize("status", ["Pending", "Batal", "Tuntas"])
@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_hanya_status_lunas(pm, tm, am, status):
    pm.getTransaksi.return_value = trx(status=status)

    ok, _ = PC.proses_kembali(1, "2026-11-10")

    assert ok is False
    pm.prosesPengembalian.assert_not_called()


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_format_tanggal_salah(pm, tm, am):
    pm.getTransaksi.return_value = trx()
    ok, pesan = PC.proses_kembali(1, "10-11-2026")
    assert ok is False and "YYYY-MM-DD" in pesan


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_sebelum_tanggal_sewa_ditolak(pm, tm, am):
    pm.getTransaksi.return_value = trx()

    ok, pesan = PC.proses_kembali(1, "2026-11-01")

    assert ok is False and "sebelum tanggal sewa" in pesan
    pm.prosesPengembalian.assert_not_called()


@patch(AM)
@patch(TM)
@patch(PM)
def test_kembali_gagal_simpan_tidak_memulihkan_stok(pm, tm, am):
    pasang_model(pm, trx())
    pm.prosesPengembalian.return_value = False

    ok, _ = PC.proses_kembali(1, "2026-11-10")

    assert ok is False
    am.ubahStok.assert_not_called()


@patch(PM)
def test_daftar_belum_kembali_diurutkan_dari_yang_paling_terlambat(pm):
    hari_ini = date.today()
    pm.lihatBelumKembali.return_value = [
        {"id_transaksi": 1, "tgl_kembali_rencana": hari_ini},                       # tepat waktu
        {"id_transaksi": 2, "tgl_kembali_rencana": hari_ini - timedelta(days=3)},   # telat 3 hari
        {"id_transaksi": 3, "tgl_kembali_rencana": hari_ini - timedelta(days=1)},   # telat 1 hari
    ]
    pm.hitungDenda.side_effect = RealPM.hitungDenda

    hasil = PC.lihat_belum_kembali()

    assert [r["id_transaksi"] for r in hasil] == [2, 3, 1]
    assert hasil[0]["estimasi_terlambat_hari"] == 3
    assert hasil[0]["estimasi_denda"] == 60000
    assert hasil[2]["estimasi_denda"] == 0
