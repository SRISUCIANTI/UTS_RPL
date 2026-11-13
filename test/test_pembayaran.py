"""FR-04: Konfirmasi Pembayaran Manual (upload bukti oleh penyewa,
verifikasi oleh operator) di TransaksiController dan PembayaranModel."""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from controllers.transaksi_controller import TransaksiController as TC
from models.pembayaran_model import PembayaranModel

TM = "controllers.transaksi_controller.TransaksiModel"
PM = "controllers.transaksi_controller.PembayaranModel"


def trx(status="Pending", id_user=5, total=150000, denda=0):
    return {"id_transaksi": 1, "id_user": id_user, "status_transaksi": status,
            "total_biaya": total, "denda": denda}


# ---------- penyewa mengirim pembayaran ----------
@patch(PM)
@patch(TM)
def test_upload_tunai_tanpa_bukti_dicatat_dengan_nominal_total(tm, pm):
    tm.getById.return_value = trx()
    pm.getByTransaksi.return_value = None
    pm.tambahPembayaran.return_value = True

    ok, pesan = TC.proses_upload_bayar(5, 1, "tunai")

    assert ok is True and "Tunai" in pesan
    pm.tambahPembayaran.assert_called_once_with(1, "Tunai", None, 150000.0)


@patch(PM)
@patch(TM)
def test_upload_transfer_dengan_bukti_berhasil(tm, pm):
    tm.getById.return_value = trx()
    pm.getByTransaksi.return_value = None
    pm.tambahPembayaran.return_value = True

    ok, _ = TC.proses_upload_bayar(5, 1, "Transfer", "bayar.jpg")

    assert ok is True
    pm.tambahPembayaran.assert_called_once_with(1, "Transfer", "bayar.jpg", 150000.0)


@patch(PM)
@patch(TM)
def test_upload_transfer_tanpa_bukti_ditolak(tm, pm):
    ok, pesan = TC.proses_upload_bayar(5, 1, "Transfer", "  ")

    assert ok is False and "bukti" in pesan.lower()
    pm.tambahPembayaran.assert_not_called()


@patch(PM)
@patch(TM)
def test_upload_metode_tidak_dikenal(tm, pm):
    ok, pesan = TC.proses_upload_bayar(5, 1, "Kartu")
    assert ok is False and "Tunai atau Transfer" in pesan


@patch(PM)
@patch(TM)
def test_upload_id_transaksi_bukan_angka(tm, pm):
    ok, pesan = TC.proses_upload_bayar(5, "abc", "Tunai")
    assert ok is False and "angka" in pesan


@patch(PM)
@patch(TM)
def test_upload_transaksi_tidak_ditemukan(tm, pm):
    tm.getById.return_value = None
    ok, pesan = TC.proses_upload_bayar(5, 99, "Tunai")
    assert ok is False and "tidak ditemukan" in pesan


@patch(PM)
@patch(TM)
def test_upload_transaksi_milik_orang_lain_ditolak(tm, pm):
    tm.getById.return_value = trx(id_user=7)

    ok, pesan = TC.proses_upload_bayar(5, 1, "Tunai")

    assert ok is False and "bukan milik" in pesan
    pm.tambahPembayaran.assert_not_called()


@pytest.mark.parametrize("status", ["Lunas", "Batal", "Tuntas"])
@patch(PM)
@patch(TM)
def test_upload_status_yang_tidak_bisa_dibayar(tm, pm, status):
    tm.getById.return_value = trx(status=status)

    ok, _ = TC.proses_upload_bayar(5, 1, "Tunai")

    assert ok is False
    pm.tambahPembayaran.assert_not_called()


@patch(PM)
@patch(TM)
def test_upload_pembayaran_ganda_saat_masih_menunggu_ditolak(tm, pm):
    tm.getById.return_value = trx()
    pm.getByTransaksi.return_value = {"status_konfirmasi": "Menunggu"}

    ok, pesan = TC.proses_upload_bayar(5, 1, "Tunai")

    assert ok is False and "Menunggu" in pesan
    pm.tambahPembayaran.assert_not_called()


@patch(PM)
@patch(TM)
def test_upload_bayar_denda_memakai_nominal_denda(tm, pm):
    tm.getById.return_value = trx(status="Selesai", denda=40000)
    pm.getByTransaksi.return_value = {"status_konfirmasi": "Diterima"}  # sewa lama sudah diterima
    pm.tambahPembayaran.return_value = True

    ok, pesan = TC.proses_upload_bayar(5, 1, "Tunai")

    assert ok is True and "Denda" in pesan
    assert pm.tambahPembayaran.call_args[0][3] == 40000.0


@patch(PM)
@patch(TM)
def test_upload_selesai_tanpa_denda_tidak_bisa_dibayar(tm, pm):
    tm.getById.return_value = trx(status="Selesai", denda=0)

    ok, _ = TC.proses_upload_bayar(5, 1, "Tunai")

    assert ok is False


@patch(PM)
@patch(TM)
def test_upload_gagal_simpan_database(tm, pm):
    tm.getById.return_value = trx()
    pm.getByTransaksi.return_value = None
    pm.tambahPembayaran.return_value = False

    ok, pesan = TC.proses_upload_bayar(5, 1, "Tunai")

    assert ok is False and "database" in pesan


# ---------- operator memverifikasi ----------
BAYAR_MENUNGGU = {"id_pembayaran": 9, "id_transaksi": 1, "status_konfirmasi": "Menunggu"}


@patch.object(TC, "_slot_masih_kosong", return_value=(True, ""))
@patch(PM)
@patch(TM)
def test_verifikasi_diterima_sewa_menjadi_lunas(tm, pm, _slot):
    pm.getById.return_value = BAYAR_MENUNGGU
    pm.verifikasi.return_value = True
    tm.getById.return_value = trx()
    tm.ubahStatus.return_value = True

    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Diterima")

    assert ok is True and "Lunas" in pesan
    pm.verifikasi.assert_called_once_with(9, "Diterima")
    tm.ubahStatus.assert_called_once_with(1, "Lunas")


@patch(PM)
@patch(TM)
def test_verifikasi_ditolak_sewa_menjadi_batal(tm, pm):
    pm.getById.return_value = BAYAR_MENUNGGU
    pm.verifikasi.return_value = True
    tm.getById.return_value = trx()
    tm.ubahStatus.return_value = True

    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Ditolak")

    assert ok is True and "pesanan baru" in pesan
    tm.ubahStatus.assert_called_once_with(1, "Batal")


@patch.object(TC, "_slot_masih_kosong", return_value=(False, "Slot sudah direbut"))
@patch(PM)
@patch(TM)
def test_verifikasi_diterima_ditolak_bila_slot_sudah_direbut(tm, pm, _slot):
    pm.getById.return_value = BAYAR_MENUNGGU
    tm.getById.return_value = trx()

    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Diterima")

    assert ok is False and "direbut" in pesan
    pm.verifikasi.assert_not_called()
    tm.ubahStatus.assert_not_called()


@patch(PM)
@patch(TM)
def test_verifikasi_denda_diterima_menjadi_tuntas(tm, pm):
    pm.getById.return_value = BAYAR_MENUNGGU
    pm.verifikasi.return_value = True
    tm.getById.return_value = trx(status="Selesai", denda=40000)
    tm.ubahStatus.return_value = True

    ok, _ = TC.konfirmasi_pembayaran_transaksi(1, 9, "Diterima")

    assert ok is True
    tm.ubahStatus.assert_called_once_with(1, "Tuntas")


@patch(PM)
@patch(TM)
def test_verifikasi_denda_ditolak_tetap_selesai(tm, pm):
    pm.getById.return_value = BAYAR_MENUNGGU
    pm.verifikasi.return_value = True
    tm.getById.return_value = trx(status="Selesai", denda=40000)
    tm.ubahStatus.return_value = True

    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Ditolak")

    assert ok is True and "bayar ulang" in pesan
    tm.ubahStatus.assert_called_once_with(1, "Selesai")


@patch.object(TC, "_slot_masih_kosong", return_value=(True, ""))
@patch(PM)
@patch(TM)
def test_verifikasi_dibatalkan_bila_status_transaksi_gagal_diubah(tm, pm, _slot):
    pm.getById.return_value = BAYAR_MENUNGGU
    pm.verifikasi.return_value = True
    tm.getById.return_value = trx()
    tm.ubahStatus.return_value = False

    ok, _ = TC.konfirmasi_pembayaran_transaksi(1, 9, "Diterima")

    assert ok is False
    pm.verifikasi.assert_called_with(9, "Menunggu")  # dikembalikan agar konsisten


@patch(PM)
@patch(TM)
def test_verifikasi_status_pembayaran_tidak_valid(tm, pm):
    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Batal")
    assert ok is False and "Diterima atau Ditolak" in pesan


@patch(PM)
@patch(TM)
def test_verifikasi_id_bukan_angka(tm, pm):
    ok, _ = TC.konfirmasi_pembayaran_transaksi("a", 9, "Diterima")
    assert ok is False


@patch(PM)
@patch(TM)
def test_verifikasi_pembayaran_tidak_ditemukan(tm, pm):
    pm.getById.return_value = None
    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Diterima")
    assert ok is False and "tidak ditemukan" in pesan


@patch(PM)
@patch(TM)
def test_verifikasi_id_pembayaran_milik_transaksi_lain(tm, pm):
    pm.getById.return_value = {**BAYAR_MENUNGGU, "id_transaksi": 2}

    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Diterima")

    assert ok is False and "milik transaksi 2" in pesan


@patch(PM)
@patch(TM)
def test_verifikasi_tidak_bisa_diulang(tm, pm):
    pm.getById.return_value = {**BAYAR_MENUNGGU, "status_konfirmasi": "Diterima"}

    ok, pesan = TC.konfirmasi_pembayaran_transaksi(1, 9, "Ditolak")

    assert ok is False and "tidak bisa diverifikasi ulang" in pesan
    pm.verifikasi.assert_not_called()


# ---------- cek ulang slot saat verifikasi ----------
def _trx_studio():
    return {"tgl_sewa": date(2026, 11, 14), "tgl_kembali_rencana": date(2026, 11, 14)}


@patch("controllers.transaksi_controller.StudioModel")
@patch(TM)
def test_slot_masih_kosong_memakai_jam_dari_detail(tm, sm):
    tm.getById.return_value = _trx_studio()
    tm.lihatDetail.return_value = [{
        "id_studio": 1, "nama_studio": "Studio A",
        "jam_mulai": timedelta(hours=10), "jam_selesai": timedelta(hours=12)}]
    sm.cekJadwal.return_value = True

    assert TC._slot_masih_kosong(1) == (True, "")
    sm.cekJadwal.assert_called_once_with(1, "2026-11-14", "2026-11-14", "10:00", "12:00")


@patch("controllers.transaksi_controller.StudioModel")
@patch(TM)
def test_slot_direbut_booking_lunas_lain(tm, sm):
    tm.getById.return_value = _trx_studio()
    tm.lihatDetail.return_value = [{
        "id_studio": 1, "nama_studio": "Studio A",
        "jam_mulai": timedelta(hours=10), "jam_selesai": timedelta(hours=12)}]
    sm.cekJadwal.return_value = False

    ok, pesan = TC._slot_masih_kosong(1)

    assert ok is False and "direbut" in pesan


@patch("controllers.transaksi_controller.StudioModel")
@patch(TM)
def test_slot_pesanan_alat_saja_tidak_cek_jadwal(tm, sm):
    tm.getById.return_value = _trx_studio()
    tm.lihatDetail.return_value = [{"id_studio": None, "id_alat": 3, "nama_alat": "Easel"}]

    assert TC._slot_masih_kosong(1) == (True, "")
    sm.cekJadwal.assert_not_called()


@patch("controllers.transaksi_controller.StudioModel")
@patch(TM)
def test_slot_transaksi_tidak_ditemukan(tm, sm):
    tm.getById.return_value = None
    ok, _ = TC._slot_masih_kosong(1)
    assert ok is False


@pytest.mark.parametrize(
    "nilai, harapan",
    [
        (timedelta(hours=9), "09:00"),
        ("09:30:00", "09:30"),
        (None, None),
        ("sampah", None),
    ],
)
def test_jam_db_ke_str(nilai, harapan):
    assert TC._jam_db_ke_str(nilai) == harapan


# ---------- PembayaranModel ----------
@patch("models.pembayaran_model.get_connection")
def test_model_tambah_pembayaran_status_awal_menunggu(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)

    assert PembayaranModel.tambahPembayaran(1, "Transfer", "bukti.jpg", 150000) is True
    sql, params = cursor.execute.call_args[0]
    assert "'Menunggu'" in sql
    assert params == (1, "Transfer", 150000, "bukti.jpg")
    conn.commit.assert_called_once()


@patch("models.pembayaran_model.get_connection")
def test_model_verifikasi_berhasil_dan_tidak_ditemukan(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.rowcount = 1
    assert PembayaranModel.verifikasi(9, "Diterima") is True
    assert cursor.execute.call_args[0][1] == ("Diterima", 9)

    cursor.rowcount = 0
    assert PembayaranModel.verifikasi(999, "Diterima") is False


@patch("models.pembayaran_model.get_connection", return_value=None)
def test_model_pembayaran_koneksi_gagal(_):
    assert PembayaranModel.verifikasi(1, "Diterima") is False
    assert PembayaranModel.tambahPembayaran(1, "Tunai", None, 1000) is False
