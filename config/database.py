import mysql.connector
from mysql.connector import Error

def get_connection():
    """Membuat dan mengembalikan koneksi ke database MySQL artstudio_rent."""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='artstudio_rent'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"[ERROR] Gagal terhubung ke database: {e}")
        return None


