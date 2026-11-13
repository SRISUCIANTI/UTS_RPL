"""Pengaturan bersama pytest.

- Menambahkan folder utama project ke sys.path agar `import models...` berjalan
  dari mana pun pytest dijalankan.
- Bila mysql-connector / tkinter / customtkinter tidak terpasang di mesin
  pengetes (misalnya server CI), dipasang modul tiruan supaya tes tetap bisa
  jalan. Tes TIDAK PERNAH menyentuh database asli atau membuka jendela.
"""
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _tiruan_mysql():
    mysql_pkg = types.ModuleType("mysql")
    konektor = types.ModuleType("mysql.connector")

    class Error(Exception):
        pass

    def connect(*args, **kwargs):
        raise Error("tes tidak boleh menyentuh database asli")

    konektor.Error = Error
    konektor.connect = connect
    mysql_pkg.connector = konektor
    sys.modules["mysql"] = mysql_pkg
    sys.modules["mysql.connector"] = konektor


def _tiruan_modul_gui(nama):
    """Modul tiruan: atribut apa pun (CTk, CTkFrame, ttk, ...) menjadi kelas kosong,
    sehingga `class X(ctk.CTk)` dan pemanggilan di level modul tetap berjalan."""

    class _Kosong:
        def __init__(self, *args, **kwargs):
            pass

    modul = types.ModuleType(nama)
    modul.__getattr__ = lambda atribut: type(atribut, (_Kosong,), {})
    sys.modules[nama] = modul


try:
    import mysql.connector  # noqa: F401
except ModuleNotFoundError:
    _tiruan_mysql()

try:
    import tkinter  # noqa: F401
except ModuleNotFoundError:
    for _nama in ("tkinter", "tkinter.ttk", "tkinter.messagebox", "tkinter.filedialog"):
        _tiruan_modul_gui(_nama)

try:
    import customtkinter  # noqa: F401
except ModuleNotFoundError:
    _tiruan_modul_gui("customtkinter")


@pytest.fixture
def fake_db():
    """Pasang koneksi + cursor tiruan pada hasil patch get_connection.

    Pemakaian:
        @patch("models.alat_model.get_connection")
        def test_x(mock_gc, fake_db):
            conn, cursor = fake_db(mock_gc)
    """

    def pasang(mock_get_connection):
        conn, cursor = MagicMock(), MagicMock()
        conn.cursor.return_value = cursor
        mock_get_connection.return_value = conn
        return conn, cursor

    return pasang
