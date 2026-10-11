from controllers.auth_controller import AuthController

def menu_auth():
    while True:
        print("\n======================================")
        print("    SISTEM ARTSTUDIO-RENT (CLI)      ")
        print("======================================")
        print("1. Login")
        print("2. Registrasi Akun Baru")
        print("0. Keluar")
        pilihan = input("Pilih menu (0-2): ")

        if pilihan == '1':
            print("\n--- LOGIN PENGGUNA ---")
            identifier = input("Username/Email : ")
            password = input("Password : ")
            
            success, user, msg = AuthController.login(identifier, password)
            if success:
                print(f"\n[SUCCESS] Selamat datang, {user['username']} ({user['role']})!")
                return user
            else:
                print(f"\n[ERROR] {msg}")

        elif pilihan == '2':
            print("\n--- REGISTRASI AKUN ---")
            username = input("Username     : ").strip()
            nama_lengkap = input("Nama Lengkap : ").strip()
            email = input("Email        : ").strip()
            no_hp = input("No HP        : ").strip()
            password = input("Password     : ")
            if not username or not nama_lengkap or not email or not password:
                print("\n[ERROR] Username, nama, email, dan password wajib diisi!")
                continue
            if '@' not in email or '.' not in email.split('@')[-1]:
                print("\n[ERROR] Format email tidak valid!")
                continue
            if len(password) < 4:
                print("\n[ERROR] Password minimal 4 karakter!")
                continue
            
            success, msg = AuthController.register(username, email, password, nama_lengkap, no_hp, role='Penyewa')
            if success:
                print(f"\n[SUCCESS] {msg}")
            else:
                print(f"\n[ERROR] {msg}")

        elif pilihan == '0':
            return None
        else:
            print("\n[!] Pilihan tidak valid, coba lagi.")