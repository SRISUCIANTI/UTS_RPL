import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
import mysql.connector
import customtkinter as ctk

# Ambil direktori tempat login_gui.py berada
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LoginGUI(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title("ArtStudio-Rent — Login Pengguna")
    self.geometry("420x480")
    self.overrideredirect(False)
    self.resizable(True, True)

    # Kontainer Utama Login
    self.frame_login = ctk.CTkFrame(
        self, corner_radius=15, fg_color="#1a1a1a"
    )
    self.frame_login.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        self.frame_login,
        text="ArtStudio-Rent",
        font=("Segoe UI", 22, "bold"),
        text_color="#ffffff",
    ).pack(pady=(35, 5))

    ctk.CTkLabel(
        self.frame_login,
        text="Silakan masuk sesuai akun Anda",
        font=("Segoe UI", 12),
        text_color="#888888",
    ).pack(pady=(0, 25))

    # Input Username / Email
    self.entry_user = ctk.CTkEntry(
        self.frame_login,
        placeholder_text="Username atau Email",
        height=42,
        corner_radius=8,
    )
    self.entry_user.pack(fill="x", padx=25, pady=10)

    # Input Password
    self.entry_pass = ctk.CTkEntry(
        self.frame_login,
        placeholder_text="Password",
        show="*",
        height=42,
        corner_radius=8,
    )
    self.entry_pass.pack(fill="x", padx=25, pady=10)

    # Tombol Login (Biru Soft)
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
    self.btn_login.pack(fill="x", padx=25, pady=(25, 15))

  def proses_login(self):
    username = self.entry_user.get().strip()
    password = self.entry_pass.get().strip()

    if not username or not password:
      messagebox.showwarning(
          "Peringatan", "Username dan password wajib diisi!"
      )
      return

    try:
      # Koneksi MySQL ke database artstudio_rent
      db = mysql.connector.connect(
          host="localhost", user="root", password="", database="artstudio_rent"
      )
      cursor = db.cursor(dictionary=True)

      # Query pencocokan user
      query = (
          "SELECT * FROM users WHERE (username = %s OR email = %s) AND password"
          " = %s"
      )
      cursor.execute(query, (username, username, password))
      user_data = cursor.fetchone()

      cursor.close()
      db.close()

      if user_data:
        role = str(user_data.get("role", "")).strip().lower()
        id_user = user_data.get("id_user") or user_data.get("id")
        nama_lengkap = user_data.get("nama_lengkap") or user_data.get(
            "username"
        )

        messagebox.showinfo(
            "Berhasil", f"Login berhasil sebagai {role.upper()}!"
        )
        self.destroy()

        target_script = ""
        if role in ["penyewa", "pelanggan"]:
          target_script = "penyewa_gui.py"
        elif role in ["operator", "admin"]:
          target_script = "operator_gui.py"
        elif role in ["owner", "pemilik"]:
          target_script = "owner_gui.py"
        else:
          messagebox.showerror(
              "Error", f"Role '{role}' tidak dikenali sistem!"
          )
          return

        script_path = os.path.join(current_dir, target_script)

        # Jalankan subprocess dengan membawa parameter data user
        subprocess.Popen([
            sys.executable,
            script_path,
            str(id_user),
            str(nama_lengkap),
            str(role),
        ])
      else:
        messagebox.showerror(
            "Gagal Login", "Username atau password salah!"
        )

    except mysql.connector.Error as err:
      messagebox.showerror(
          "Database Error", f"Terjadi kesalahan koneksi MySQL:\n{err}"
      )
    except Exception as e:
      messagebox.showerror("Error", f"Terjadi kesalahan sistem:\n{e}")


if __name__ == "__main__":
  app = LoginGUI()
  app.mainloop()