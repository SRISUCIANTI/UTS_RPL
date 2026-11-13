"""FR-07: Cetak Bukti Sewa (BuktiController)."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from controllers.bukti_controller import BuktiController as BC

TM = "controllers.bukti_controller.TransaksiModel"
PM = "controllers.bukti_controller.PembayaranModel"


def trx(status="Lunas", id_user=5, total=100000, denda=0):
    return {"id_transaksi": 1, "id_user": id_user, "nama_lengkap": "Kila Sari",
            "username": "kila", "status_transaksi": status,
            "tgl_sewa": date(2026, 11, 14), "tgl_kembali_rencana": date(2026, 11, 16),
            "tgl_kembali_aktual": None, "total_biaya": total, "denda": denda}


DETAIL_STUDIO = {"id_studio": 1, "nama_studio": "Studio A", "id_alat": None, "nama_alat": None,
                 "jumlah": 2, "subtotal": 100000, "harga_per_hari": None,
                 "jam_mulai": timedelta(hours=10), "jam_selesai": timedelta(hours=12)}
DETAIL_ALAT = {"id_studio": None, "nama_studio": None, "id_alat": 3, "nama_alat": "Easel",
               "jumlah": 2, "subtotal": 100000, "harga_per_hari": 25000,
               "jam_mulai": None, "jam_selesai": None}
BAYAR = [{"metode_bayar": "Transfer", "tgl_bayar": date(2026, 11, 13),
          "status_konfirmasi": "Diterima", "jumlah_bayar": 100000}]


def teks(hasil):
    ok, baris = hasil
    assert ok is True
    return "\n".join(baris)


# ---------- aturan siapa & kapan boleh cetak ----------
@pytest.mark.parametrize("status", ["Lunas", "Selesai", "Tuntas"])
@patch(PM)
@patch(TM)
def test_bukti_bisa_dicetak_setelah_pembayaran_diterima(tm, pm, status):
    tm.getById.return_value = trx(status=status)
    tm.lihatDetail.return_value = [DETAIL_STUDIO]
    pm.lihatByTransaksi.return_value = BAYAR

    ok, baris = BC.susun_bukti(5, 1)

    assert ok is True and isinstance(baris, list)


@pytest.mark.parametrize("status", ["Pending", "Batal"])
@patch(PM)
@patch(TM)
def test_bukti_pending_dan_batal_ditolak(tm, pm, status):
    tm.getById.return_value = trx(status=status)

    ok, pesan = BC.susun_bukti(5, 1)

    assert ok is False and status in pesan


@patch(PM)
@patch(TM)
def test_bukti_milik_orang_lain_ditolak(tm, pm):
    tm.getById.return_value = trx(id_user=7)

    ok, pesan = BC.susun_bukti(5, 1)

    assert ok is False and "bukan milik" in pesan


@patch(PM)
@patch(TM)
def test_bukti_transaksi_tidak_ditemukan(tm, pm):
    tm.getById.return_value = None
    ok, pesan = BC.susun_bukti(5, 99)
    assert ok is False and "tidak ditemukan" in pesan


@patch(PM)
@patch(TM)
def test_bukti_id_bukan_angka(tm, pm):
    ok, pesan = BC.susun_bukti(5, "abc")
    assert ok is False and "angka" in pesan


# ---------- isi bukti ----------
@patch(PM)
@patch(TM)
def test_isi_bukti_studio_memuat_jam_dan_total(tm, pm):
    tm.getById.return_value = trx()
    tm.lihatDetail.return_value = [DETAIL_STUDIO]
    pm.lihatByTransaksi.return_value = BAYAR

    t = teks(BC.susun_bukti(5, 1))

    assert "BUKTI SEWA / TANDA TERIMA" in t
    assert "No. Transaksi    : 1" in t
    assert "Kila Sari (kila)" in t
    assert "Studio Studio A" in t and "jam 10.00-12.00 (2 jam)" in t
    assert "TOTAL" in t and "Rp100.000" in t
    assert "Sewa | Transfer | 2026-11-13 | Diterima" in t


@patch(PM)
@patch(TM)
def test_isi_bukti_alat_menghitung_hari_sewa(tm, pm):
    tm.getById.return_value = trx()
    tm.lihatDetail.return_value = [DETAIL_ALAT]
    pm.lihatByTransaksi.return_value = BAYAR

    t = teks(BC.susun_bukti(5, 1))

    assert "Alat Easel" in t
    assert "2 buah x Rp25.000 x 2 hari" in t  # 14 -> 16 November = 2 hari


@patch(PM)
@patch(TM)
def test_isi_bukti_dengan_denda_belum_lunas(tm, pm):
    tm.getById.return_value = trx(status="Selesai", denda=40000)
    tm.lihatDetail.return_value = [DETAIL_ALAT]
    pm.lihatByTransaksi.return_value = BAYAR

    t = teks(BC.susun_bukti(5, 1))

    assert "Denda keterlambatan" in t and "Rp40.000" in t
    assert "TOTAL KESELURUHAN" in t and "Rp140.000" in t
    assert "belum lunas" in t


@patch(PM)
@patch(TM)
def test_isi_bukti_tuntas_menyatakan_semua_lunas(tm, pm):
    tm.getById.return_value = trx(status="Tuntas", denda=40000)
    tm.lihatDetail.return_value = [DETAIL_ALAT]
    pm.lihatByTransaksi.return_value = BAYAR + [
        {"metode_bayar": "Tunai", "tgl_bayar": date(2026, 11, 18),
         "status_konfirmasi": "Diterima", "jumlah_bayar": 40000}]

    t = teks(BC.susun_bukti(5, 1))

    assert "telah lunas" in t
    assert "Denda | Tunai" in t  # pembayaran kedua dianggap denda


@patch(PM)
@patch(TM)
def test_isi_bukti_tanpa_rincian_dan_pembayaran_tidak_crash(tm, pm):
    tm.getById.return_value = trx()
    tm.lihatDetail.return_value = []
    pm.lihatByTransaksi.return_value = []

    t = teks(BC.susun_bukti(5, 1))

    assert "rincian item tidak ditemukan" in t
    assert "data pembayaran tidak ditemukan" in t


@patch(PM)
@patch(TM)
def test_semua_baris_bukti_tidak_melebihi_lebar_kertas(tm, pm):
    tm.getById.return_value = trx()
    tm.lihatDetail.return_value = [DETAIL_STUDIO, DETAIL_ALAT]
    pm.lihatByTransaksi.return_value = BAYAR

    ok, baris = BC.susun_bukti(5, 1)

    assert max(len(b) for b in baris) <= BC.LEBAR + 5


# ---------- fungsi format ----------
@pytest.mark.parametrize(
    "nilai, harapan",
    [(1250000, "Rp1.250.000"), (0, "Rp0"), (None, "Rp0"), (25000.0, "Rp25.000")],
)
def test_format_rupiah_gaya_indonesia(nilai, harapan):
    assert BC._rp(nilai) == harapan


@pytest.mark.parametrize(
    "nilai, harapan",
    [(timedelta(hours=10), "10.00"), (timedelta(hours=24), "24.00"),
     ("09:30:00", "09.30"), (None, None)],
)
def test_format_jam(nilai, harapan):
    assert BC._jam(nilai) == harapan


# ---------- simpan ke TXT ----------
def test_simpan_txt_berhasil(tmp_path):
    path = tmp_path / "bukti_sewa_1.txt"

    ok, pesan = BC.simpan_txt(["BARIS 1", "BARIS 2"], str(path))

    assert ok is True and str(path) in pesan
    assert path.read_text(encoding="utf-8") == "BARIS 1\nBARIS 2\n"


def test_simpan_txt_lokasi_salah_mengembalikan_pesan_gagal(tmp_path):
    ok, pesan = BC.simpan_txt(["x"], str(tmp_path / "tidak_ada" / "b.txt"))

    assert ok is False and "Gagal" in pesan
