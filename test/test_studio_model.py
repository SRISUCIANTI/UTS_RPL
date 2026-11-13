"""FR-01 (CRUD studio) dan FR-02 (cek jadwal & jadwal terisi) di StudioModel."""
from unittest.mock import patch

from models.studio_model import StudioModel

TERSEDIA = {"status_ketersediaan": "Tersedia"}


# ---------- FR-02: cekJadwal ----------
@patch("models.studio_model.get_connection")
def test_cek_jadwal_kosong_boleh_dipesan(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.side_effect = [TERSEDIA, None]  # studio ada, tidak ada bentrok

    assert StudioModel.cekJadwal(1, "2026-11-20", "2026-11-20", "10:00", "12:00") is True
    conn.close.assert_called_once()


@patch("models.studio_model.get_connection")
def test_cek_jadwal_bentrok_booking_lunas_ditolak(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.side_effect = [TERSEDIA, {"id_transaksi": 5}]

    assert StudioModel.cekJadwal(1, "2026-11-20", "2026-11-20", "10:00", "12:00") is False


@patch("models.studio_model.get_connection")
def test_cek_jadwal_hanya_booking_lunas_yang_mengunci_slot(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.side_effect = [TERSEDIA, None]

    StudioModel.cekJadwal(1, "2026-11-20", "2026-11-20", "10:00", "12:00")

    sql_bentrok = cursor.execute.call_args_list[1][0][0]
    assert "status_transaksi = 'Lunas'" in sql_bentrok  # Pending tidak menahan slot


@patch("models.studio_model.get_connection")
def test_cek_jadwal_dengan_jam_mengirim_parameter_jam(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.side_effect = [TERSEDIA, None]

    StudioModel.cekJadwal(1, "2026-11-20", "2026-11-20", "10:00", "12:00")

    assert cursor.execute.call_args_list[1][0][1] == (
        1, "2026-11-20", "2026-11-20", "10:00", "12:00")


@patch("models.studio_model.get_connection")
def test_cek_jadwal_tanpa_jam_hanya_cek_tanggal(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.side_effect = [TERSEDIA, None]

    StudioModel.cekJadwal(1, "2026-11-20", "2026-11-21")

    assert cursor.execute.call_args_list[1][0][1] == (1, "2026-11-20", "2026-11-21")


@patch("models.studio_model.get_connection")
def test_cek_jadwal_studio_maintenance_ditolak_tanpa_cek_bentrok(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = {"status_ketersediaan": "Maintenance"}

    assert StudioModel.cekJadwal(1, "2026-11-20", "2026-11-20", "10:00", "12:00") is False
    assert cursor.execute.call_count == 1  # berhenti sebelum query bentrok


@patch("models.studio_model.get_connection")
def test_cek_jadwal_studio_dibooking_operator_ditolak(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = {"status_ketersediaan": "Dibooking"}

    assert StudioModel.cekJadwal(1, "2026-11-20", "2026-11-20") is False


@patch("models.studio_model.get_connection")
def test_cek_jadwal_studio_tidak_ada(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = None

    assert StudioModel.cekJadwal(99, "2026-11-20", "2026-11-20") is False


@patch("models.studio_model.get_connection", return_value=None)
def test_cek_jadwal_koneksi_gagal(_):
    assert StudioModel.cekJadwal(1, "2026-11-20", "2026-11-20") is False


# ---------- FR-02: jadwal terisi untuk katalog ----------
@patch("models.studio_model.get_connection")
def test_jadwal_studio_hanya_lunas_masa_kini_dan_depan(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    data = [{"tgl_sewa": "2026-11-20", "jam_mulai": None, "jam_selesai": None}]
    cursor.fetchall.return_value = data

    assert StudioModel.jadwalStudio(1) == data
    sql = cursor.execute.call_args[0][0]
    assert "'Lunas'" in sql and "CURDATE()" in sql
    assert "nama" not in sql.lower().replace("nama_studio", "")  # tanpa nama penyewa


@patch("models.studio_model.get_connection", return_value=None)
def test_jadwal_studio_koneksi_gagal_list_kosong(_):
    assert StudioModel.jadwalStudio(1) == []


@patch("models.studio_model.get_connection")
def test_lihat_semua_studio(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchall.return_value = [{"id_studio": 1}, {"id_studio": 2}]

    assert len(StudioModel.lihatSemua()) == 2


# ---------- FR-01: CRUD studio ----------
@patch("models.studio_model.get_connection")
def test_kelola_tambah_studio(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)

    hasil = StudioModel.kelolaData(
        "tambah", nama_studio="Studio A", kapasitas=5, tarif_sewa=50000,
        fasilitas="AC", status_ketersediaan="Tersedia")

    assert hasil is True
    assert cursor.execute.call_args[0][1] == ("Studio A", 50000, 5, "AC", "Tersedia")
    conn.commit.assert_called_once()


@patch("models.studio_model.get_connection")
def test_kelola_update_studio_tidak_ditemukan(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.rowcount = 0

    assert StudioModel.kelolaData("update", 99, "X", 1, 1000) is False


@patch("models.studio_model.get_connection")
def test_kelola_hapus_studio_berhasil(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.rowcount = 1

    assert StudioModel.kelolaData("hapus", 3) is True
    assert "DELETE FROM studio" in cursor.execute.call_args[0][0]


@patch("models.studio_model.get_connection")
def test_kelola_hapus_studio_tidak_ada(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.rowcount = 0

    assert StudioModel.kelolaData("hapus", 99) is False


@patch("models.studio_model.get_connection")
def test_kelola_error_database_mengembalikan_false(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.execute.side_effect = Exception("db error")

    assert StudioModel.kelolaData("tambah", nama_studio="X") is False
    conn.close.assert_called_once()


@patch("models.studio_model.get_connection")
def test_hitung_pemakaian(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = (3,)

    assert StudioModel.hitungPemakaian(1) == 3


@patch("models.studio_model.get_connection", return_value=None)
def test_hitung_pemakaian_koneksi_gagal_minus_satu(_):
    assert StudioModel.hitungPemakaian(1) == -1


@patch("models.studio_model.get_connection")
def test_ada_booking_aktif(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = (2,)
    assert StudioModel.adaBookingAktif(1) is True
    cursor.fetchone.return_value = (0,)
    assert StudioModel.adaBookingAktif(1) is False


@patch("models.studio_model.get_connection", return_value=None)
def test_ada_booking_aktif_koneksi_gagal_dianggap_ada_demi_keamanan(_):
    assert StudioModel.adaBookingAktif(1) is True


@patch("models.studio_model.get_connection")
def test_ubah_status_studio(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.rowcount = 1

    assert StudioModel.ubahStatus(1, "Maintenance") is True
    conn.commit.assert_called_once()


@patch("models.studio_model.get_connection")
def test_ubah_status_tidak_valid_tidak_menyentuh_database(mock_gc):
    assert StudioModel.ubahStatus(1, "Rusak") is False
    mock_gc.assert_not_called()
