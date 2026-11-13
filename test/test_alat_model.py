from unittest.mock import MagicMock, patch

from models.alat_model import AlatModel


def siapkan_koneksi(mock_get_connection):
    """Pasang koneksi + cursor tiruan; kembalikan keduanya."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    mock_get_connection.return_value = conn
    return conn, cursor


@patch("models.alat_model.get_connection")
def test_lihat_semua_berhasil(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)
    data = [
        {"id_alat": 1, "nama_alat": "Easel", "stok": 5},
        {"id_alat": 2, "nama_alat": "Kuas", "stok": 20},
    ]
    cursor.fetchall.return_value = data

    hasil = AlatModel.lihatSemua()

    assert hasil == data
    cursor.execute.assert_called_once()
    conn.close.assert_called_once()


@patch("models.alat_model.get_connection", return_value=None)
def test_lihat_semua_koneksi_gagal_mengembalikan_list_kosong(_):
    assert AlatModel.lihatSemua() == []


@patch("models.alat_model.get_connection")
def test_cek_ketersediaan_mengembalikan_satu_baris(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)
    cursor.fetchone.return_value = {"id_alat": 3, "nama_alat": "Kanvas", "stok": 7}

    hasil = AlatModel.cekKetersediaan(3)

    assert hasil["nama_alat"] == "Kanvas"
    assert cursor.execute.call_args[0][1] == (3,)
    conn.close.assert_called_once()


@patch("models.alat_model.get_connection")
def test_ubah_stok_kurangi_memakai_syarat_stok_tidak_negatif(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)
    cursor.rowcount = 1

    hasil = AlatModel.ubahStok(1, -2)

    assert hasil is True
    sql = cursor.execute.call_args[0][0]
    assert "stok + %s >= 0" in sql  # mencegah stok minus di level SQL
    conn.commit.assert_called_once()


@patch("models.alat_model.get_connection")
def test_ubah_stok_kurangi_gagal_bila_stok_tidak_cukup(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)
    cursor.rowcount = 0  # tidak ada baris yang memenuhi syarat stok >= 0

    assert AlatModel.ubahStok(1, -999) is False


@patch("models.alat_model.get_connection")
def test_ubah_stok_tambah_berhasil(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)
    cursor.rowcount = 1

    assert AlatModel.ubahStok(1, 3) is True
    assert cursor.execute.call_args[0][1] == (3, 1)


@patch("models.alat_model.get_connection")
def test_kelola_data_tambah_menyimpan_dan_commit(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)

    hasil = AlatModel.kelolaData(
        "tambah", nama_alat="Palet", kategori="Alat cat", stok=4, tarif_sewa=15000
    )

    assert hasil is True
    assert cursor.execute.call_args[0][1] == ("Palet", 15000, 4, "Alat cat")
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


@patch("models.alat_model.get_connection")
def test_kelola_data_hapus(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)

    assert AlatModel.kelolaData("hapus", id_alat=9) is True
    assert "DELETE FROM alat" in cursor.execute.call_args[0][0]
    assert cursor.execute.call_args[0][1] == (9,)


@patch("models.alat_model.get_connection")
def test_kelola_data_error_database_mengembalikan_false(mock_get_connection):
    conn, cursor = siapkan_koneksi(mock_get_connection)
    cursor.execute.side_effect = Exception("foreign key constraint")

    assert AlatModel.kelolaData("hapus", id_alat=1) is False
    conn.commit.assert_not_called()
    conn.close.assert_called_once()  # koneksi tetap ditutup walau error
