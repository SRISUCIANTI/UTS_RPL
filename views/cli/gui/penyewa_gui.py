
import os
import sys
import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import date, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class PenyewaGUI(ctk.CTk):
    def __init__(self, user):
        super().__init__()

        self.user = user or {}
        self.id_user = self.user.get("id_user") or self.user.get("id")
        nama_user = (
            self.user.get("nama_lengkap")
            or self.user.get("username")
            or "Penyewa"
        )

        self.title(
            f"ArtStudio-Rent — Dashboard Penyewa ({str(nama_user).title()})"
        )
        self.geometry("1100x650")
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(
            row=0, column=0, sticky="ew", padx=15, pady=(15, 0)
        )

        ctk.CTkLabel(
            header_frame,
            text=f"Halo, {str(nama_user).title()} (Penyewa)",
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff",
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="Keluar (Logout)",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=120,
            height=32,
            command=self.aksi_logout,
        ).pack(side="right")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
            rowheight=28,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#1f538d",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", "#1f456e")])

        self.tab_view = ctk.CTkTabview(
            self,
            fg_color="#1a1a1a",
            segmented_button_fg_color="#2b2b2b",
        )
        self.tab_view.grid(
            row=1, column=0, sticky="nsew", padx=15, pady=10
        )

        self.tab_pesan = self.tab_view.add("Cari Alat & Buat Pesanan")
        self.tab_riwayat = self.tab_view.add("Riwayat & Status Pesanan")

        self.setup_tab_pesan()
        self.setup_tab_riwayat()

    def setup_tab_pesan(self):
        ctk.CTkLabel(
            self.tab_pesan,
            text="Form Pemesanan Alat & Studio Seni",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=20)

        self.ent_alat = ctk.CTkEntry(
            self.tab_pesan,
            placeholder_text="Nama Alat / Studio",
            width=350,
            height=40,
        )
        self.ent_alat.pack(pady=10)

        self.ent_durasi = ctk.CTkEntry(
            self.tab_pesan,
            placeholder_text="Durasi Sewa (Jam)",
            width=350,
            height=40,
        )
        self.ent_durasi.pack(pady=10)

        ctk.CTkButton(
            self.tab_pesan,
            text="Kirim & Buat Pesanan (Pending)",
            fg_color="#3498db",
            hover_color="#2980b9",
            width=350,
            height=42,
            command=self.buat_pesanan,
        ).pack(pady=15)

    def setup_tab_riwayat(self):
        self.tab_riwayat.grid_columnconfigure(0, weight=1)
        self.tab_riwayat.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(
            self.tab_riwayat, fg_color="transparent"
        )
        container.pack(fill="both", expand=True, padx=10, pady=10)

        kolom = ("id_trx", "tgl", "total", "status")
        self.tabel_riwayat = ttk.Treeview(
            container, columns=kolom, show="headings", height=13
        )

        self.tabel_riwayat.heading("id_trx", text="ID Trx")
        self.tabel_riwayat.heading("tgl", text="Tanggal Sewa")
        self.tabel_riwayat.heading("total", text="Total Biaya")
        self.tabel_riwayat.heading("status", text="Status Pembayaran")

        self.tabel_riwayat.column(
            "id_trx", width=60, anchor="center"
        )
        self.tabel_riwayat.column(
            "tgl", width=150, anchor="center"
        )
        self.tabel_riwayat.column(
            "total", width=130, anchor="center"
        )
        self.tabel_riwayat.column(
            "status", width=150, anchor="center"
        )

        scroll = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.tabel_riwayat.yview,
        )
        self.tabel_riwayat.configure(yscrollcommand=scroll.set)

        self.tabel_riwayat.pack(
            side="left", fill="both", expand=True
        )
        scroll.pack(side="right", fill="y")

        ctk.CTkButton(
            self.tab_riwayat,
            text="Segarkan Riwayat",
            command=self.muat_riwayat,
        ).pack(pady=(0, 10))

        self.muat_riwayat()

    def buat_pesanan(self):
        alat = self.ent_alat.get().strip()
        durasi = self.ent_durasi.get().strip()

        if not self.id_user:
            messagebox.showerror(
                "Error Akun",
                "ID pengguna tidak ditemukan. Silakan login kembali.",
            )
            return

        if not alat:
            messagebox.showwarning(
                "Peringatan", "Nama alat/studio harus diisi!"
            )
            return

        if not durasi.isdigit() or int(durasi) <= 0:
            messagebox.showwarning(
                "Peringatan",
                "Durasi sewa harus berupa angka positif (jam)!",
            )
            return

        db = None
        cursor = None

        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="artstudio_rent",
            )
            cursor = db.cursor()

            # Sesuaikan dengan struktur tabel transaksi saat ini.
            # Karena kolom bertipe DATE, tanggal kembali dibulatkan
            # ke hari berikutnya jika durasi melewati 24 jam.
            jumlah_jam = int(durasi)
            hari_sewa = (jumlah_jam + 23) // 24
            tanggal_kembali = date.today() + timedelta(days=hari_sewa)
            total_biaya = jumlah_jam * 50000

            query = """
                INSERT INTO transaksi
                (
                    id_user,
                    tgl_sewa,
                    tgl_kembali_rencana,
                    total_biaya,
                    status_transaksi
                )
                VALUES (%s, CURDATE(), %s, %s, 'Pending')
            """

            cursor.execute(
                query,
                (self.id_user, tanggal_kembali, total_biaya),
            )
            db.commit()

            self.ent_alat.delete(0, "end")
            self.ent_durasi.delete(0, "end")
            self.muat_riwayat()

            messagebox.showinfo(
                "Berhasil",
                "Pesanan berhasil disimpan dengan status Pending.",
            )

        except mysql.connector.Error as err:
            if db and db.is_connected():
                db.rollback()
            messagebox.showerror(
                "Database Error", f"Gagal membuat pesanan:\n{err}"
            )

        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def muat_riwayat(self):
        for row in self.tabel_riwayat.get_children():
            self.tabel_riwayat.delete(row)

        if not self.id_user:
            messagebox.showerror(
                "Error Akun",
                "ID pengguna tidak ditemukan. Silakan login kembali.",
            )
            return

        db = None
        cursor = None

        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="artstudio_rent",
            )
            cursor = db.cursor(dictionary=True)

            # Filter wajib: hanya transaksi akun yang sedang login.
            cursor.execute(
                """
                SELECT id_transaksi, tgl_sewa,
                       total_biaya, status_transaksi
                FROM transaksi
                WHERE id_user = %s
                ORDER BY id_transaksi DESC
                """,
                (self.id_user,),
            )

            for transaksi in cursor.fetchall():
                self.tabel_riwayat.insert(
                    "",
                    "end",
                    values=(
                        transaksi["id_transaksi"],
                        transaksi["tgl_sewa"],
                        f"Rp {float(transaksi['total_biaya'] or 0):,.0f}",
                        transaksi["status_transaksi"],
                    ),
                )

        except mysql.connector.Error as err:
            messagebox.showerror(
                "Database Error",
                f"Gagal memuat riwayat:\n{err}",
            )

        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def aksi_logout(self):
        if messagebox.askyesno(
            "Konfirmasi",
            "Apakah Anda ingin keluar ke halaman login?",
        ):
            self.destroy()
            from login_gui import LoginGUI
            LoginGUI().mainloop()



if __name__ == "__main__":
    if len(sys.argv) >= 4:
        user = {
            "id_user": int(sys.argv[1]),
            "nama_lengkap": sys.argv[2],
            "role": sys.argv[3],
        }
        PenyewaGUI(user).mainloop()
    else:
        print("Silakan jalankan aplikasi melalui login_gui.py.")
