from views.cli.auth_cli import menu_auth
from views.cli.penyewa_cli import menu_penyewa
from views.cli.operator_cli import menu_operator
from views.cli.owner_cli import menu_owner

def main():
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

if __name__ == "__main__":
    main()