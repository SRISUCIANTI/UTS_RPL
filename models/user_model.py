from config.database import get_connection

class UserModel:
    @staticmethod
    def login(identifier, password_hash):
        """Mendukung login menggunakan email atau username dengan password ter-hash"""
        conn = get_connection()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT * FROM users 
                   WHERE (username = %s OR email = %s) AND password = %s""", 
                (identifier, identifier, password_hash)
            )
            return cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Login gagal: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def registrasi(username, email, password_hash, nama_lengkap, no_hp="", role='Penyewa'):
        """Menyimpan data registrasi pengguna baru dengan nilai password ter-hash ke kolom 'password'"""
        conn = get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO users (username, email, password, nama_lengkap, role, no_hp) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (username, email, password_hash, nama_lengkap, role, no_hp)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Registrasi gagal: {e}")
            return False
        finally:
            conn.close()