from views.cli.auth_cli import menu_auth
from views.cli.penyewa_cli import menu_penyewa
from views.cli.operator_cli import menu_operator
from views.cli.owner_cli import menu_owner
import sys

def jalankan_gui():
    """Buka aplikasi GUI: intro dulu, lalu halaman login.
    Lewati intro dengan: python main.py --no-intro"""
    from views.gui.login_gui import LoginGUI

    app = LoginGUI()
    if "--no-intro" not in sys.argv[1:]:
        try:
            from views.gui.intro_gui import IntroGUI

            IntroGUI(app)
        except Exception:
            # intro hanya pemanis: bila gagal, langsung tampilkan login
            app.deiconify()
    app.mainloop()


def jalankan_cli():
    """Mode teks (CLI) lama. Jalankan dengan: python main.py --cli"""
    from views.cli.auth_cli import menu_auth
    from views.cli.penyewa_cli import menu_penyewa
    from views.cli.operator_cli import menu_operator
    from views.cli.owner_cli import menu_owner

    try:
        while True:
            # Pintu Masuk Otentikasi Login/Register
            user = menu_auth()
            if not user:
                print("\nTerima kasih telah menggunakan sistem ArtStudio-Rent!")
                break

            # Arahkan Tampilan Berdasarkan Role User (Penyewa, Operator, Owner)
            role = user.get('role', 'Penyewa')
            if role == 'Penyewa':
                menu_penyewa(user)
            elif role == 'Operator':
                menu_operator(user)
            elif role == 'Owner':
                menu_owner(user)
    except (KeyboardInterrupt, EOFError):
        print("\n\nKeluar dari sistem ArtStudio-Rent. Sampai jumpa!")


def main():
    if "--cli" in sys.argv[1:]:
        jalankan_cli()
    else:
        jalankan_gui()


if __name__ == "__main__":
    main()