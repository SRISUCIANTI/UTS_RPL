import os
import subprocess
import sys
import hashlib
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

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LoginGUI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("ArtStudio-Rent — Autentikasi Pengguna")
        self.geometry("450x600")
        self.resizable(True, True)

        self.frame_login = ctk.CTkFrame(
            self, corner_radius=15, fg_color="#1a1a1a"
        )
        self.frame_login.pack(fill="both", expand=True, padx=20, pady=20)

        self.frame_register = ctk.CTkFrame(
            self, corner_radius=15, fg_color="#1a1a1a"
        )

        self.setup_gui_login()
        self.setup_gui_register()

    def setup_gui_login(self):
        ctk.CTkLabel(
            self.frame_login,
            text="ArtStudio-Rent",
            font=("Segoe UI", 22, "bold"),
            text_color="#ffffff",
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            self.frame_login,
            text="Silakan masuk sesuai akun Anda",
            font=("Segoe UI", 12),
            text_color="#888888",
        ).pack(pady=(0, 20))

        self.entry_user = ctk.CTkEntry(
            self.frame_login,
            placeholder_text="Username atau Email",
            height=42,
            corner_radius=8,
        )
        self.entry_user.pack(fill="x", padx=25, pady=10)

        self.entry_pass = ctk.CTkEntry(
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
            fg_color="#3498db",
            hover_color="#2980b9",
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
            text_color="#3498db",
            hover_color="#2c2c2c",
            font=("Segoe UI", 12, "underline"),
            command=self.tampilkan_form_register,
        )
        self.btn_goto_register.pack(pady=10)

    def setup_gui_register(self):
        ctk.CTkLabel(
            self.frame_register,
            text="Buat Akun Baru",
            font=("Segoe UI", 22, "bold"),
            text_color="#ffffff",
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self.frame_register,
            text="Lengkapi data Anda untuk mendaftar",
            font=("Segoe UI", 12),
            text_color="#888888",
        ).pack(pady=(0, 10))

        self.reg_username = ctk.CTkEntry(
            self.frame_register, placeholder_text="Username", height=35, corner_radius=8
        )
        self.reg_username.pack(fill="x", padx=25, pady=5)

        self.reg_nama = ctk.CTkEntry(
            self.frame_register, placeholder_text="Nama Lengkap", height=35, corner_radius=8
        )
        self.reg_nama.pack(fill="x", padx=25, pady=5)

        self.reg_email = ctk.CTkEntry(
            self.frame_register, placeholder_text="Email", height=35, corner_radius=8
        )
        self.reg_email.pack(fill="x", padx=25, pady=5)

        self.reg_hp = ctk.CTkEntry(
            self.frame_register, placeholder_text="No HP (Opsional)", height=35, corner_radius=8
        )
        self.reg_hp.pack(fill="x", padx=25, pady=5)

        self.reg_pass = ctk.CTkEntry(
            self.frame_register, placeholder_text="Password", show="*", height=35, corner_radius=8
        )
        self.reg_pass.pack(fill="x", padx=25, pady=5)

        ctk.CTkLabel(
            self.frame_register, text="Daftar Sebagai Role:", font=("Segoe UI", 11), text_color="#aaaaaa"
        ).pack(anchor="w", padx=25, pady=(2, 0))
        
        self.reg_role = ctk.CTkOptionMenu(
            self.frame_register,
            values=["Penyewa", "Operator", "Owner"],
            height=35,
            corner_radius=8,
            fg_color="#2b2b2b",
            button_color="#3498db",
            button_hover_color="#2980b9",
        )
        self.reg_role.pack(fill="x", padx=25, pady=(2, 10))

        self.btn_register = ctk.CTkButton(
            self.frame_register,
            text="Daftar Sekarang",
            fg_color="#2ecc71",
            hover_color="#27ae60",
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
            text_color="#e74c3c",
            hover_color="#2c2c2c",
            font=("Segoe UI", 12, "underline"),
            command=self.tampilkan_form_login,
        )
        self.btn_goto_login.pack(pady=5)

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