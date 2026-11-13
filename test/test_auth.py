"""FR-09: Registrasi & Otentikasi Akun (AuthController, UserModel)."""
import hashlib
from unittest.mock import patch

from controllers.auth_controller import AuthController
from models.user_model import UserModel

UM = "controllers.auth_controller.UserModel"


def sha(teks):
    return hashlib.sha256(teks.encode()).hexdigest()


# ---------- AuthController ----------
def test_hash_password_sha256():
    assert AuthController._hash_password("12345") == sha("12345")
    assert AuthController._hash_password("12345") != "12345"  # tidak disimpan polos


@patch(UM)
def test_login_berhasil_mengirim_hash_bukan_password_asli(um):
    um.login.return_value = {"id_user": 1, "role": "Penyewa"}

    ok, user, pesan = AuthController.login("kila", "rahasia")

    assert ok is True and user["role"] == "Penyewa" and "berhasil" in pesan
    um.login.assert_called_once_with("kila", sha("rahasia"))


@patch(UM)
def test_login_gagal_password_salah(um):
    um.login.return_value = None

    ok, user, pesan = AuthController.login("kila", "salah")

    assert ok is False and user is None and "salah" in pesan


@patch(UM)
def test_register_berhasil_menyimpan_password_ter_hash(um):
    um.registrasi.return_value = True

    ok, pesan = AuthController.register("kila", "kila@mail.com", "rahasia", "Kila Sari", "0812")

    assert ok is True and "berhasil" in pesan
    um.registrasi.assert_called_once_with(
        "kila", "kila@mail.com", sha("rahasia"), "Kila Sari", "0812", "Penyewa")


@patch(UM)
def test_register_role_bisa_ditentukan(um):
    um.registrasi.return_value = True

    AuthController.register("bimo", "b@mail.com", "pw", "Bimo", role="Operator")

    assert um.registrasi.call_args[0][5] == "Operator"


@patch(UM)
def test_register_gagal_username_atau_email_sudah_dipakai(um):
    um.registrasi.return_value = False

    ok, pesan = AuthController.register("kila", "kila@mail.com", "pw", "Kila")

    assert ok is False and "sudah dipakai" in pesan


# ---------- UserModel ----------
@patch("models.user_model.get_connection")
def test_model_login_cocok_username_atau_email(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = {"id_user": 1}

    hasil = UserModel.login("kila@mail.com", sha("pw"))

    assert hasil == {"id_user": 1}
    sql, params = cursor.execute.call_args[0]
    assert "username = %s OR email = %s" in sql
    assert params == ("kila@mail.com", "kila@mail.com", sha("pw"))
    conn.close.assert_called_once()


@patch("models.user_model.get_connection")
def test_model_login_tidak_cocok(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = None

    assert UserModel.login("x", "y") is None


@patch("models.user_model.get_connection")
def test_model_login_error_database_mengembalikan_none(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.execute.side_effect = Exception("db error")

    assert UserModel.login("x", "y") is None
    conn.close.assert_called_once()


@patch("models.user_model.get_connection", return_value=None)
def test_model_koneksi_gagal(_):
    assert UserModel.login("x", "y") is None
    assert UserModel.registrasi("a", "a@a", "h", "A") is False


@patch("models.user_model.get_connection")
def test_model_registrasi_menyimpan_dan_commit(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)

    assert UserModel.registrasi("kila", "k@m.com", "hash", "Kila", "0812", "Penyewa") is True
    assert cursor.execute.call_args[0][1] == ("kila", "k@m.com", "hash", "Kila", "Penyewa", "0812")
    conn.commit.assert_called_once()


@patch("models.user_model.get_connection")
def test_model_registrasi_duplikat_mengembalikan_false(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.execute.side_effect = Exception("Duplicate entry")

    assert UserModel.registrasi("kila", "k@m.com", "hash", "Kila") is False
    conn.commit.assert_not_called()
