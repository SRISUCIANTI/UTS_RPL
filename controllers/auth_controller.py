import hashlib
from models.user_model import UserModel

class AuthController:
    @staticmethod
    def _hash_password(password):
        """Mengubah teks password biasa menjadi string SHA-256 hash"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def login(identifier, password):
        """Proses login dengan mengubah password input menjadi hash"""
        # 1. Ubah password input ('12345') menjadi Hash SHA-256
        password_hash = AuthController._hash_password(password)
        
        # 2. Kirim hash tersebut untuk dicocokkan ke database
        user = UserModel.login(identifier, password_hash)
        
        if user:
            return True, user, "Login berhasil!"
        return False, None, "Username/Email atau Password salah!"

    @staticmethod
    def register(username, email, password, nama_lengkap, no_hp="", role='Penyewa'):
        """Proses registrasi: hash password lalu simpan via UserModel.registrasi"""
        password_hash = AuthController._hash_password(password)
        ok = UserModel.registrasi(username, email, password_hash, nama_lengkap, no_hp, role)
        if ok:
            return True, "Registrasi berhasil! Silakan login."
        return False, "Registrasi gagal! Username/Email mungkin sudah dipakai."