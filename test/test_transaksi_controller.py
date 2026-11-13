"""Tes aturan pemesanan di TransaksiController.
Model diganti tiruan, jadi tidak ada database yang tersentuh."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from controllers.transaksi_controller import TransaksiController as TC

BESOK = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
KEMARIN = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
STUDIO = {"id_studio": 1, "nama_studio": "Studio A", "harga_per_jam": 50000,
          "status_ketersediaan": "Tersedia"}


# ---------- validasi tanggal ----------
def test_tanggal_valid():
    hasil, err = TC._tanggal(BESOK, BESOK)
    assert err is None
    assert hasil[0] == hasil[1]


def test_tanggal_format_salah():
    hasil, err = TC._tanggal("20-11-2026", "20-11-2026")
    assert hasil is None and "YYYY-MM-DD" in err


def test_tanggal_masa_lalu_ditolak():
    hasil, err = TC._tanggal(KEMARIN, BESOK)
    assert hasil is None and "masa lalu" in err


def test_tanggal_kembali_sebelum_sewa_ditolak():
    hasil, err = TC._tanggal(BESOK, KEMARIN)
    assert hasil is None


# ---------- validasi jam (toko tutup 22.00) ----------
def test_jam_valid():
    hasil, err = TC._jam(9, 2)
    assert err is None
    assert hasil == ("09:00", "11:00", 2)


def test_jam_tepat_sampai_tutup_boleh():
    hasil, err = TC._jam(20, 2)  # 20.00 + 2 jam = 22.00
    assert err is None and hasil[1] == "22:00"


@pytest.mark.parametrize("mulai, durasi", [(21, 2), (22, 1), (23, 1)])
def test_jam_melewati_jam_tutup_ditolak(mulai, durasi):
    hasil, err = TC._jam(mulai, durasi)
    assert hasil is None and "tutup" in err.lower()


@pytest.mark.parametrize("mulai, durasi", [(9, 0), (9, -1), ("abc", 1), (9, "x"), (-1, 1)])
def test_jam_input_tidak_valid_ditolak(mulai, durasi):
    hasil, err = TC._jam(mulai, durasi)
    assert hasil is None and err


# ---------- pemesanan studio ----------
@patch("controllers.transaksi_controller.TransaksiModel")
@patch("controllers.transaksi_controller.StudioModel")
def test_pesan_studio_berhasil_mencatat_detail_dengan_jam(studio_model, trx_model):
    studio_model.getById.return_value = STUDIO
    studio_model.cekJadwal.return_value = True
    trx_model.hitungTotal.side_effect = lambda a, b: a * b
    trx_model.buatPesanan.return_value = 77
    trx_model.catatDetail.return_value = True

    ok, pesan = TC.proses_pesan_studio(5, 1, BESOK, 10, 3)

    assert ok is True
    assert "77" in pesan
    trx_model.buatPesanan.assert_called_once_with(5, BESOK, BESOK, 150000)
    _, kwargs = trx_model.catatDetail.call_args
    assert kwargs["id_studio"] == 1
    assert kwargs["jam_mulai"] == "10:00" and kwargs["jam_selesai"] == "13:00"


@patch("controllers.transaksi_controller.TransaksiModel")
@patch("controllers.transaksi_controller.StudioModel")
def test_pesan_studio_bentrok_jadwal_ditolak_tanpa_menyimpan(studio_model, trx_model):
    studio_model.getById.return_value = STUDIO
    studio_model.cekJadwal.return_value = False  # slot sudah Lunas milik orang lain

    ok, pesan = TC.proses_pesan_studio(5, 1, BESOK, 10, 2)

    assert ok is False and "penuh" in pesan.lower()
    trx_model.buatPesanan.assert_not_called()


@pytest.mark.parametrize("status", ["Maintenance", "Dibooking"])
@patch("controllers.transaksi_controller.TransaksiModel")
@patch("controllers.transaksi_controller.StudioModel")
def test_pesan_studio_tutup_ditolak(studio_model, trx_model, status):
    studio_model.getById.return_value = {**STUDIO, "status_ketersediaan": status}

    ok, _ = TC.proses_pesan_studio(5, 1, BESOK, 10, 2)

    assert ok is False
    trx_model.buatPesanan.assert_not_called()


@patch("controllers.transaksi_controller.TransaksiModel")
@patch("controllers.transaksi_controller.StudioModel")
def test_pesan_studio_gagal_catat_detail_membatalkan_transaksi(studio_model, trx_model):
    studio_model.getById.return_value = STUDIO
    studio_model.cekJadwal.return_value = True
    trx_model.hitungTotal.side_effect = lambda a, b: a * b
    trx_model.buatPesanan.return_value = 88
    trx_model.catatDetail.return_value = False

    ok, _ = TC.proses_pesan_studio(5, 1, BESOK, 10, 2)

    assert ok is False
    trx_model.hapusTransaksi.assert_called_once_with(88)  # tidak ada pesanan setengah jadi


# ---------- pemesanan alat ----------
@patch("controllers.transaksi_controller.AlatModel")
@patch("controllers.transaksi_controller.TransaksiModel")
def test_pesan_alat_keranjang_kosong_ditolak(trx_model, alat_model):
    ok, pesan = TC.proses_pesan_alat(5, BESOK, BESOK, [])
    assert ok is False and "minimal satu" in pesan.lower()


@patch("controllers.transaksi_controller.AlatModel")
@patch("controllers.transaksi_controller.TransaksiModel")
def test_pesan_alat_stok_kurang_ditolak(trx_model, alat_model):
    alat_model.cekKetersediaan.return_value = {
        "id_alat": 1, "nama_alat": "Easel", "stok": 1, "harga_per_hari": 25000}

    ok, pesan = TC.proses_pesan_alat(5, BESOK, BESOK, [(1, 3)])

    assert ok is False and "stok" in pesan.lower()
    trx_model.buatPesanan.assert_not_called()
    alat_model.ubahStok.assert_not_called()


@patch("controllers.transaksi_controller.AlatModel")
@patch("controllers.transaksi_controller.TransaksiModel")
def test_pesan_alat_berhasil_hitung_total_dan_kurangi_stok(trx_model, alat_model):
    alat_model.cekKetersediaan.return_value = {
        "id_alat": 1, "nama_alat": "Easel", "stok": 10, "harga_per_hari": 25000}
    alat_model.ubahStok.return_value = True
    trx_model.hitungTotal.side_effect = lambda a, b: a * b
    trx_model.buatPesanan.return_value = 99
    trx_model.catatDetail.return_value = True
    lusa = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")

    ok, _ = TC.proses_pesan_alat(5, BESOK, lusa, [(1, 2)])

    assert ok is True
    # 25.000 x 2 buah x 2 hari = 100.000
    assert trx_model.buatPesanan.call_args[0][3] == 100000
    alat_model.ubahStok.assert_called_once_with(1, -2)


@patch("controllers.transaksi_controller.AlatModel")
@patch("controllers.transaksi_controller.TransaksiModel")
def test_pesan_alat_gagal_di_tengah_mengembalikan_stok(trx_model, alat_model):
    alat_model.cekKetersediaan.return_value = {
        "id_alat": 1, "nama_alat": "Easel", "stok": 10, "harga_per_hari": 25000}
    alat_model.ubahStok.return_value = True
    trx_model.hitungTotal.side_effect = lambda a, b: a * b
    trx_model.buatPesanan.return_value = 99
    trx_model.catatDetail.return_value = False  # gagal catat detail

    ok, pesan = TC.proses_pesan_alat(5, BESOK, BESOK, [(1, 2)])

    assert ok is False and "dibatalkan" in pesan.lower()
    alat_model.ubahStok.assert_any_call(1, -2)  # stok dikurangi...
    alat_model.ubahStok.assert_any_call(1, 2)   # ...lalu dikembalikan
    trx_model.hapusTransaksi.assert_called_once_with(99)
