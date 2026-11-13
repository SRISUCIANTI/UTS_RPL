"""FR-01 (validasi kelola alat & studio) dan FR-02 (jadwal untuk katalog)."""
from datetime import date, time, timedelta
from unittest.mock import patch

import pytest

from controllers.inventaris_controller import InventarisController as IC


# ---------- FR-01: kelola alat ----------
@patch("controllers.inventaris_controller.AlatModel")
def test_kelola_alat_tambah_valid(alat_model):
    alat_model.kelolaData.return_value = True

    ok, pesan = IC.kelola_alat("tambah", nama_alat="Easel", tarif_sewa=25000, stok=5)

    assert ok is True and "tambah" in pesan
    alat_model.kelolaData.assert_called_once()


@pytest.mark.parametrize("nama, tarif", [("", 25000), ("Easel", 0), ("Easel", -1)])
@patch("controllers.inventaris_controller.AlatModel")
def test_kelola_alat_nama_atau_tarif_tidak_valid(alat_model, nama, tarif):
    ok, _ = IC.kelola_alat("tambah", nama_alat=nama, tarif_sewa=tarif, stok=1)

    assert ok is False
    alat_model.kelolaData.assert_not_called()


@patch("controllers.inventaris_controller.AlatModel")
def test_kelola_alat_stok_bukan_angka(alat_model):
    ok, pesan = IC.kelola_alat("tambah", nama_alat="Easel", tarif_sewa=25000, stok="abc")

    assert ok is False and "angka" in pesan.lower()


@patch("controllers.inventaris_controller.AlatModel")
def test_kelola_alat_stok_negatif_ditolak(alat_model):
    ok, pesan = IC.kelola_alat("update", 1, nama_alat="Easel", tarif_sewa=25000, stok=-1)

    assert ok is False and "negatif" in pesan.lower()
    alat_model.kelolaData.assert_not_called()


@patch("controllers.inventaris_controller.AlatModel")
def test_kelola_alat_gagal_di_database(alat_model):
    alat_model.kelolaData.return_value = False

    ok, pesan = IC.kelola_alat("hapus", 1)

    assert ok is False and "Gagal" in pesan


# ---------- FR-01: kelola studio ----------
@patch("controllers.inventaris_controller.StudioModel")
def test_kelola_studio_tambah_valid_status_awal_tersedia(studio_model):
    studio_model.kelolaData.return_value = True

    ok, _ = IC.kelola_studio("tambah", nama_studio="Studio A", kapasitas=5, tarif_sewa=50000)

    assert ok is True
    assert studio_model.kelolaData.call_args[0][6] == "Tersedia"


@pytest.mark.parametrize(
    "kapasitas, tarif",
    [(0, 50000), (-2, 50000), (5, 0), (5, -100)],
)
@patch("controllers.inventaris_controller.StudioModel")
def test_kelola_studio_kapasitas_atau_tarif_tidak_valid(studio_model, kapasitas, tarif):
    ok, _ = IC.kelola_studio("tambah", nama_studio="Studio A", kapasitas=kapasitas, tarif_sewa=tarif)

    assert ok is False
    studio_model.kelolaData.assert_not_called()


@patch("controllers.inventaris_controller.StudioModel")
def test_kelola_studio_kapasitas_bukan_angka(studio_model):
    ok, pesan = IC.kelola_studio("tambah", nama_studio="A", kapasitas="banyak", tarif_sewa=1000)

    assert ok is False and "angka" in pesan.lower()


@patch("controllers.inventaris_controller.StudioModel")
def test_kelola_studio_update_mempertahankan_status_lama(studio_model):
    studio_model.getById.return_value = {"status_ketersediaan": "Maintenance"}
    studio_model.kelolaData.return_value = True

    IC.kelola_studio("update", 1, nama_studio="Studio A", kapasitas=5, tarif_sewa=50000)

    assert studio_model.kelolaData.call_args[0][6] == "Maintenance"


# ---------- FR-01: hapus studio (aturan keamanan riwayat) ----------
@patch("controllers.inventaris_controller.StudioModel")
def test_hapus_studio_id_bukan_angka(studio_model):
    ok, pesan = IC.hapus_studio("abc")
    assert ok is False and "angka" in pesan.lower()


@patch("controllers.inventaris_controller.StudioModel")
def test_hapus_studio_tidak_ditemukan(studio_model):
    studio_model.getById.return_value = None
    ok, pesan = IC.hapus_studio(9)
    assert ok is False and "tidak ditemukan" in pesan


@patch("controllers.inventaris_controller.StudioModel")
def test_hapus_studio_ditolak_bila_ada_booking_aktif(studio_model):
    studio_model.getById.return_value = {"nama_studio": "Studio A"}
    studio_model.adaBookingAktif.return_value = True

    ok, pesan = IC.hapus_studio(1)

    assert ok is False and "booking aktif" in pesan
    studio_model.kelolaData.assert_not_called()


@patch("controllers.inventaris_controller.StudioModel")
def test_hapus_studio_ditolak_bila_pernah_disewa(studio_model):
    studio_model.getById.return_value = {"nama_studio": "Studio A"}
    studio_model.adaBookingAktif.return_value = False
    studio_model.hitungPemakaian.return_value = 3

    ok, pesan = IC.hapus_studio(1)

    assert ok is False and "3x" in pesan
    studio_model.kelolaData.assert_not_called()


@patch("controllers.inventaris_controller.StudioModel")
def test_hapus_studio_ditolak_bila_cek_riwayat_gagal(studio_model):
    studio_model.getById.return_value = {"nama_studio": "Studio A"}
    studio_model.adaBookingAktif.return_value = False
    studio_model.hitungPemakaian.return_value = -1

    ok, _ = IC.hapus_studio(1)
    assert ok is False


@patch("controllers.inventaris_controller.StudioModel")
def test_hapus_studio_aman_berhasil(studio_model):
    studio_model.getById.return_value = {"nama_studio": "Studio A"}
    studio_model.adaBookingAktif.return_value = False
    studio_model.hitungPemakaian.return_value = 0
    studio_model.kelolaData.return_value = True

    ok, pesan = IC.hapus_studio(1)

    assert ok is True and "berhasil dihapus" in pesan
    studio_model.kelolaData.assert_called_once_with("hapus", 1)


@patch("controllers.inventaris_controller.StudioModel")
def test_kelola_studio_aksi_hapus_diarahkan_ke_hapus_studio(studio_model):
    studio_model.getById.return_value = None

    ok, _ = IC.kelola_studio("hapus", 5, nama_studio="x", kapasitas=1, tarif_sewa=1)

    assert ok is False
    studio_model.getById.assert_called_once_with(5)


# ---------- status studio ----------
@patch("controllers.inventaris_controller.StudioModel")
def test_atur_status_studio_berhasil_dan_huruf_dinormalkan(studio_model):
    studio_model.getById.return_value = {"nama_studio": "A", "status_ketersediaan": "Tersedia"}
    studio_model.ubahStatus.return_value = True

    ok, pesan = IC.atur_status_studio(1, "maintenance")

    assert ok is True and "Tersedia -> Maintenance" in pesan
    studio_model.ubahStatus.assert_called_once_with(1, "Maintenance")


@patch("controllers.inventaris_controller.StudioModel")
def test_atur_status_studio_dibooking_mengingatkan_membuka_kembali(studio_model):
    studio_model.getById.return_value = {"nama_studio": "A", "status_ketersediaan": "Tersedia"}
    studio_model.ubahStatus.return_value = True

    ok, pesan = IC.atur_status_studio(1, "Dibooking")

    assert ok is True and "kembalikan" in pesan


@patch("controllers.inventaris_controller.StudioModel")
def test_atur_status_studio_tidak_valid(studio_model):
    ok, _ = IC.atur_status_studio(1, "Rusak")
    assert ok is False
    studio_model.getById.assert_not_called()


@patch("controllers.inventaris_controller.StudioModel")
def test_atur_status_studio_sama_dengan_sebelumnya(studio_model):
    studio_model.getById.return_value = {"nama_studio": "A", "status_ketersediaan": "Tersedia"}

    ok, pesan = IC.atur_status_studio(1, "Tersedia")

    assert ok is False and "sudah berstatus" in pesan
    studio_model.ubahStatus.assert_not_called()


# ---------- FR-02: tampilan jam & jadwal ----------
@pytest.mark.parametrize(
    "nilai, harapan",
    [
        (timedelta(hours=9), "09.00"),
        (timedelta(hours=22, minutes=30), "22.30"),
        (timedelta(hours=24), "24.00"),   # MySQL TIME 24:00 terbaca 1 hari
        (time(9, 5), "09.05"),
        ("09:00:00", "09.00"),
        ("sampah", "--.--"),
        (None, "--.--"),
    ],
)
def test_tampil_jam(nilai, harapan):
    assert IC.tampil_jam(nilai) == harapan


@patch("controllers.inventaris_controller.StudioModel")
def test_jadwal_studio_memakai_bahasa_sederhana_tanpa_nama_penyewa(studio_model):
    studio_model.jadwalStudio.return_value = [
        {"tgl_sewa": date(2026, 11, 14), "jam_mulai": timedelta(hours=10),
         "jam_selesai": timedelta(hours=12)},
        {"tgl_sewa": date(2026, 12, 1), "jam_mulai": None, "jam_selesai": None},
    ]

    assert IC.jadwal_studio(1) == ["14 Nov, jam 10.00-12.00", "1 Des (sehari penuh)"]


@patch("controllers.inventaris_controller.StudioModel")
def test_jadwal_studio_kosong(studio_model):
    studio_model.jadwalStudio.return_value = []
    assert IC.jadwal_studio(1) == []


@patch("controllers.inventaris_controller.StudioModel")
def test_jadwal_hari_ini_hanya_booking_yang_mencakup_hari_ini(studio_model):
    hari_ini = date.today()
    studio_model.jadwalStudio.return_value = [
        {"tgl_sewa": hari_ini, "tgl_kembali_rencana": hari_ini,
         "jam_mulai": timedelta(hours=10), "jam_selesai": timedelta(hours=12)},
        {"tgl_sewa": hari_ini + timedelta(days=5), "tgl_kembali_rencana": hari_ini + timedelta(days=5),
         "jam_mulai": timedelta(hours=8), "jam_selesai": timedelta(hours=9)},
        {"tgl_sewa": hari_ini - timedelta(days=1), "tgl_kembali_rencana": hari_ini + timedelta(days=1),
         "jam_mulai": None, "jam_selesai": None},
    ]

    assert IC.jadwal_hari_ini(1) == ["10.00-12.00", "sehari penuh"]
