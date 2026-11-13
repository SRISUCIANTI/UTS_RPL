import os
import subprocess
import sys
import hashlib
import tkinter
from tkinter import messagebox
import mysql.connector
import customtkinter as ctk

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if os.path.basename(project_root) == "views" or os.path.basename(project_root) == "gui":
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from controllers.auth_controller import AuthController
except ImportError:
    AuthController = None

MODE_AWAL = "Light"  # mode saat aplikasi dibuka: "Light" atau "Dark"
ctk.set_appearance_mode(MODE_AWAL)
ctk.set_default_color_theme("blue")

def _cari_root():
    """Naik dari folder file ini sampai ketemu folder yang berisi main.py atau assets/."""
    awal = os.path.dirname(os.path.abspath(__file__))
    d = awal
    while True:
        if os.path.exists(os.path.join(d, "main.py")) or os.path.isdir(os.path.join(d, "assets")):
            return d
        induk = os.path.dirname(d)
        if induk == d:
            return awal
        d = induk


BASE_DIR = _cari_root()
LOGO_PATH = os.path.join(BASE_DIR, "assets", "artstudio-07.png")            # untuk mode terang
LOGO_PATH_GELAP = os.path.join(BASE_DIR, "assets", "artstudio-06.png")  # untuk mode gelap
LOGO_SIZE = (150, 150)  # kotak maksimum (lebar, tinggi) saat ditampilkan

# ---------------------------------------------------------------
# PALET WARNA (terang, gelap) — diambil dari kedua logo
# ---------------------------------------------------------------
WARNA_LATAR = ("#F3F7EA", "#0E130F")         # latar jendela: putih kehijauan lembut
WARNA_KARTU = ("#FFFFFF", "#151B16")         # kartu form
WARNA_GARIS = ("#D9E5C3", "#2A382C")         # garis tepi kartu
WARNA_INPUT = ("#F6F9EE", "#1D261F")         # isi kolom input
WARNA_INPUT_HOVER = ("#E8F1D4", "#26332A")   # hover tombol teks
WARNA_GARIS_INPUT = ("#B9CC94", "#3C5442")   # garis tepi kolom input
WARNA_TEKS = ("#1C0500", "#F4F8EC")          # cokelat tua (warna pensil)
WARNA_TEKS_REDUP = ("#6B7560", "#9BA991")    # teks sekunder
WARNA_PLACEHOLDER = ("#7C8872", "#7F8D77")
WARNA_UTAMA = ("#2D7D4F", "#B5FF5B")         # hijau daun (tombol utama)
WARNA_UTAMA_HOVER = ("#236340", "#9BE043")
WARNA_TEKS_TOMBOL = ("#FFFFFF", "#0D1A08")  # teks di atas tombol hijau

GAYA_ENTRY = dict(
    fg_color=WARNA_INPUT,
    border_color=WARNA_GARIS_INPUT,
    border_width=1,
    text_color=WARNA_TEKS,
    placeholder_text_color=WARNA_PLACEHOLDER,
)


def buat_entry(master, **opsi):
    """CTkEntry dengan gaya tema; opsi yang diberikan menimpa gaya bawaan."""
    gaya = dict(GAYA_ENTRY)
    gaya.update(opsi)
    return ctk.CTkEntry(master, **gaya)


def _potong_tepi(gambar):
    """Buang ruang kosong di sekeliling logo supaya tampil lebih besar, lalu perkecil."""
    from PIL import Image, ImageChops

    gambar = gambar.convert("RGBA")
    alpha = gambar.getchannel("A")
    if alpha.getextrema()[0] < 255:  # logo transparan: pakai batas piksel terisi
        kotak = alpha.point(lambda v: 255 if v > 10 else 0).getbbox()
    else:  # latar putih polos
        putih = Image.new("RGB", gambar.size, (255, 255, 255))
        selisih = ImageChops.difference(gambar.convert("RGB"), putih).convert("L")
        kotak = selisih.point(lambda v: 255 if v > 12 else 0).getbbox()
    if kotak:
        pad = int(max(gambar.size) * 0.01)
        kotak = (
            max(0, kotak[0] - pad),
            max(0, kotak[1] - pad),
            min(gambar.width, kotak[2] + pad),
            min(gambar.height, kotak[3] + pad),
        )
        gambar = gambar.crop(kotak)
    gambar.thumbnail((600, 600), Image.LANCZOS)  # hemat memori untuk file besar
    return gambar


class LoginGUI(ctk.CTk):

    def tengahkan_jendela(self, lebar=450, tinggi=640):
        """Taruh jendela di tengah layar (benar juga di layar HiDPI)."""
        self.update_idletasks()
        try:
            skala = self._get_window_scaling()
        except Exception:
            skala = 1.0
        w, h = int(lebar * skala), int(tinggi * skala)
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        tkinter.Wm.wm_geometry(self, f"{w}x{h}+{x}+{max(0, y - 30)}")

    def __init__(self):
        super().__init__()

        self.title("ArtStudio-Rent — Autentikasi Pengguna")
        self.tengahkan_jendela(450, 640)
        self.configure(fg_color=WARNA_LATAR)
        self.resizable(True, True)

        self.frame_login = ctk.CTkFrame(
            self, corner_radius=15, fg_color=WARNA_KARTU, border_width=1, border_color=WARNA_GARIS
        )
        self.frame_login.pack(fill="both", expand=True, padx=20, pady=20)

        self.frame_register = ctk.CTkFrame(
            self, corner_radius=15, fg_color=WARNA_KARTU, border_width=1, border_color=WARNA_GARIS
        )

        self.setup_gui_login()
        self.setup_gui_register()
        self.setup_tombol_mode()

    def muat_logo(self):
        """Muat logo terang + gelap (otomatis berganti saat mode berubah). None bila gagal."""
        try:
            from PIL import Image

            gambar = _potong_tepi(Image.open(LOGO_PATH))
            gambar_gelap = gambar  # bila logo gelap tidak ada, pakai logo yang sama
            if os.path.exists(LOGO_PATH_GELAP):
                try:
                    gambar_gelap = _potong_tepi(Image.open(LOGO_PATH_GELAP))
                    if gambar_gelap.size != gambar.size:  # samakan agar posisi tidak bergeser
                        gambar_gelap = gambar_gelap.resize(gambar.size, Image.LANCZOS)
                except Exception:
                    gambar_gelap = gambar
            lebar, tinggi = gambar.size
            skala = min(LOGO_SIZE[0] / lebar, LOGO_SIZE[1] / tinggi)
            ukuran = (max(1, int(lebar * skala)), max(1, int(tinggi * skala)))
            return ctk.CTkImage(light_image=gambar, dark_image=gambar_gelap, size=ukuran)
        except Exception:
            return None

    def setup_gui_login(self):
        # Simpan ke self agar gambar tidak dibuang oleh garbage collector
        self.logo_image = self.muat_logo()
        if self.logo_image:
            ctk.CTkLabel(
                self.frame_login, image=self.logo_image, text=""
            ).pack(pady=(25, 0))

        ctk.CTkLabel(
            self.frame_login,
            text="ArtStudio-Rent",
            font=("Segoe UI", 22, "bold"),
            text_color=WARNA_TEKS,
        ).pack(pady=(10 if self.logo_image else 25, 5))

        ctk.CTkLabel(
            self.frame_login,
            text="Silakan masuk sesuai akun Anda",
            font=("Segoe UI", 12),
            text_color=WARNA_TEKS_REDUP,
        ).pack(pady=(0, 20))

        self.entry_user = buat_entry(
            self.frame_login,
            placeholder_text="Username atau Email",
            height=42,
            corner_radius=8,
        )
        self.entry_user.pack(fill="x", padx=25, pady=10)

        self.entry_pass = buat_entry(
            self.frame_login,
            placeholder_text="Password",
            show="*",
            height=42,
            corner_radius=8,
        )
        self.entry_pass.pack(fill="x", padx=25, pady=10)

        self.btn_login = ctk.CTkButton(
            self.frame_login,
            text="Masuk (Login)",
            fg_color=WARNA_UTAMA,
            text_color=WARNA_TEKS_TOMBOL,
            hover_color=WARNA_UTAMA_HOVER,
            font=("Segoe UI", 13, "bold"),
            height=45,
            corner_radius=8,
            command=self.proses_login,
        )
        self.btn_login.pack(fill="x", padx=25, pady=(20, 10))

        self.btn_goto_register = ctk.CTkButton(
            self.frame_login,
            text="Belum punya akun? Buat Akun Baru",
            fg_color="transparent",
            text_color=WARNA_UTAMA,
            hover_color=WARNA_INPUT_HOVER,
            font=("Segoe UI", 12, "underline"),
            command=self.tampilkan_form_register,
        )
        self.btn_goto_register.pack(pady=10)

    def setup_gui_register(self):
        ctk.CTkLabel(
            self.frame_register,
            text="Buat Akun Baru",
            font=("Segoe UI", 22, "bold"),
            text_color=WARNA_TEKS,
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self.frame_register,
            text="Lengkapi data Anda untuk mendaftar",
            font=("Segoe UI", 12),
            text_color=WARNA_TEKS_REDUP,
        ).pack(pady=(0, 10))

        self.reg_username = buat_entry(
            self.frame_register, placeholder_text="Username", height=35, corner_radius=8
        )
        self.reg_username.pack(fill="x", padx=25, pady=5)

        self.reg_nama = buat_entry(
            self.frame_register, placeholder_text="Nama Lengkap", height=35, corner_radius=8
        )
        self.reg_nama.pack(fill="x", padx=25, pady=5)

        self.reg_email = buat_entry(
            self.frame_register, placeholder_text="Email", height=35, corner_radius=8
        )
        self.reg_email.pack(fill="x", padx=25, pady=5)

        self.reg_hp = buat_entry(
            self.frame_register, placeholder_text="No HP (Opsional)", height=35, corner_radius=8
        )
        self.reg_hp.pack(fill="x", padx=25, pady=5)

        self.reg_pass = buat_entry(
            self.frame_register, placeholder_text="Password", show="*", height=35, corner_radius=8
        )
        self.reg_pass.pack(fill="x", padx=25, pady=5)

        ctk.CTkLabel(
            self.frame_register, text="Daftar Sebagai Role:", font=("Segoe UI", 11), text_color=WARNA_TEKS_REDUP
        ).pack(anchor="w", padx=25, pady=(2, 0))
        
        self.reg_role = ctk.CTkOptionMenu(
            self.frame_register,
            values=["Penyewa", "Operator", "Owner"],
            height=35,
            corner_radius=8,
            fg_color=WARNA_INPUT,
            button_color=WARNA_UTAMA,
            button_hover_color=WARNA_UTAMA_HOVER,
            text_color=WARNA_TEKS,
            dropdown_fg_color=WARNA_KARTU,
            dropdown_text_color=WARNA_TEKS,
            dropdown_hover_color=WARNA_INPUT_HOVER,
        )
        self.reg_role.pack(fill="x", padx=25, pady=(2, 10))

        self.btn_register = ctk.CTkButton(
            self.frame_register,
            text="Daftar Sekarang",
            fg_color=WARNA_UTAMA,
            text_color=WARNA_TEKS_TOMBOL,
            hover_color=WARNA_UTAMA_HOVER,
            font=("Segoe UI", 13, "bold"),
            height=40,
            corner_radius=8,
            command=self.proses_register,
        )
        self.btn_register.pack(fill="x", padx=25, pady=(5, 5))

        self.btn_goto_login = ctk.CTkButton(
            self.frame_register,
            text="Sudah punya akun? Kembali ke Login",
            fg_color="transparent",
            text_color=WARNA_TEKS,
            hover_color=WARNA_INPUT_HOVER,
            font=("Segoe UI", 12, "underline"),
            command=self.tampilkan_form_login,
        )
        self.btn_goto_login.pack(pady=5)

    def setup_tombol_mode(self):
        """Tombol ikon kanan atas untuk ganti mode: ☾ (ke gelap) / ☀ (ke terang)."""
        self.btn_mode = ctk.CTkButton(
            self,
            text="",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="transparent",
            bg_color=WARNA_KARTU,  # samakan dengan kartu di belakangnya, bukan latar jendela
            border_width=1,
            border_color=WARNA_GARIS_INPUT,
            text_color=WARNA_TEKS,
            hover_color=WARNA_INPUT_HOVER,
            font=("Segoe UI Symbol", 18),
            command=self.ganti_mode,
        )
        # Dibuat paling akhir sehingga tampil di atas kartu; x/y mengatur jarak dari sudut kanan atas
        self.btn_mode.place(relx=1.0, x=-32, y=32, anchor="ne")
        self.perbarui_tombol_mode()

    def ganti_mode(self):
        mode_baru = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(mode_baru)
        self.perbarui_tombol_mode()

    def perbarui_tombol_mode(self):
        if ctk.get_appearance_mode() == "Light":
            self.btn_mode.configure(text="☾")
        else:
            self.btn_mode.configure(text="☀")

    def tampilkan_form_register(self):
        self.frame_login.pack_forget()
        self.frame_register.pack(fill="both", expand=True, padx=20, pady=20)

    def tampilkan_form_login(self):
        self.frame_register.pack_forget()
        self.frame_login.pack(fill="both", expand=True, padx=20, pady=20)

    def proses_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Peringatan", "Username dan password wajib diisi!")
            return

        try:
            user_data = None
            sukses = False
            pesan = ""

            password_hash = hashlib.sha256(password.encode()).hexdigest()

            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT * FROM users WHERE (username = %s OR email = %s) AND (password = %s OR password = %s)",
                (username, username, password_hash, password)
            )
            user_data = cursor.fetchone()
            cursor.close()
            db.close()

            if user_data:
                sukses = True
                pesan = "Login berhasil!"

            if sukses and user_data:
                messagebox.showinfo("Berhasil", pesan)
                self.destroy()

                role = str(user_data.get("role", "")).strip().lower()
                id_user = user_data.get("id_user") or user_data.get("id")
                nama_lengkap = user_data.get("nama_lengkap") or user_data.get("username")

                target_script = ""
                if role in ["penyewa", "pelanggan"]:
                    target_script = "penyewa_gui.py"
                elif role in ["operator", "admin"]:
                    target_script = "operator_gui.py"
                elif role in ["owner", "pemilik"]:
                    target_script = "owner_gui.py"
                else:
                    messagebox.showerror("Error", f"Role '{role}' tidak dikenali sistem!")
                    return

                script_path = os.path.join(current_dir, target_script)
                if not os.path.exists(script_path):
                    script_path = os.path.join(project_root, target_script)

                subprocess.Popen([
                    sys.executable,
                    script_path,
                    str(id_user),
                    str(nama_lengkap),
                    str(role),
                ])
            else:
                messagebox.showerror("Gagal Login", "Username atau password salah!")

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan sistem:\n{e}")

    def proses_register(self):
        username = self.reg_username.get().strip()
        nama = self.reg_nama.get().strip()
        email = self.reg_email.get().strip()
        no_hp = self.reg_hp.get().strip()
        password = self.reg_pass.get().strip()
        role = self.reg_role.get().strip()

        if not username or not nama or not email or not password:
            messagebox.showwarning("Peringatan", "Username, Nama, Email, dan Password wajib diisi!")
            return

        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                sukses, pesan = False, "Username atau Email sudah terdaftar!"
            else:
                cursor.execute(
                    "INSERT INTO users (username, nama_lengkap, email, no_hp, password, role) VALUES (%s, %s, %s, %s, %s, %s)",
                    (username, nama, email, no_hp, password_hash, role)
                )
                db.commit()
                sukses, pesan = True, "Registrasi berhasil! Silakan login."
            cursor.close()
            db.close()

            if sukses:
                messagebox.showinfo("Berhasil", pesan)
                self.reg_username.delete(0, "end")
                self.reg_nama.delete(0, "end")
                self.reg_email.delete(0, "end")
                self.reg_hp.delete(0, "end")
                self.reg_pass.delete(0, "end")
                self.tampilkan_form_login()
            else:
                messagebox.showerror("Gagal Registrasi", pesan)

        except Exception as err:
            messagebox.showerror("Database Error", f"Gagal membuat akun:\n{err}")


if __name__ == "__main__":
    app = LoginGUI()
    app.mainloop()