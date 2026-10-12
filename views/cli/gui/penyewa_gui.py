import os
import sys
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
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

        self.tab_katalog = self.tab_view.add("Daftar Studio")
        self.tab_pesan = self.tab_view.add("Cari Studio & Buat Pesanan")
        self.tab_riwayat = self.tab_view.add("Riwayat & Status Pesanan")

        self.setup_tab_katalog()
        self.setup_tab_pesan()
        self.setup_tab_riwayat()

    def setup_tab_katalog(self):
        self.tab_katalog.grid_columnconfigure(0, weight=1)
        self.tab_katalog.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.tab_katalog,
            text="Katalog Studio Seni yang Tersedia",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(15, 5))

        container = ctk.CTkFrame(self.tab_katalog, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        kolom = ("id_studio", "nama", "harga", "kapasitas", "fasilitas", "status")
        self.tabel_katalog = ttk.Treeview(
            container, columns=kolom, show="headings", height=13
        )
        self.tabel_katalog.heading("id_studio", text="ID")
        self.tabel_katalog.heading("nama", text="Nama Studio")
        self.tabel_katalog.heading("harga", text="Harga / Jam")
        self.tabel_katalog.heading("kapasitas", text="Kapasitas")
        self.tabel_katalog.heading("fasilitas", text="Fasilitas")
        self.tabel_katalog.heading("status", text="Status")

        self.tabel_katalog.column("id_studio", width=40, anchor="center")
        self.tabel_katalog.column("nama", width=180, anchor="w")
        self.tabel_katalog.column("harga", width=90, anchor="center")
        self.tabel_katalog.column("kapasitas", width=60, anchor="center")
        self.tabel_katalog.column("fasilitas", width=220, anchor="w")
        self.tabel_katalog.column("status", width=80, anchor="center")

        scroll = ttk.Scrollbar(
            container, orient="vertical", command=self.tabel_katalog.yview
        )
        self.tabel_katalog.configure(yscrollcommand=scroll.set)
        self.tabel_katalog.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        ctk.CTkButton(
            self.tab_katalog,
            text="Segarkan Katalog",
            fg_color="#3498db",
            command=self.muat_katalog,
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        self.muat_katalog()

    def muat_katalog(self):
        for row in self.tabel_katalog.get_children():
            self.tabel_katalog.delete(row)

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
            cursor.execute("SELECT * FROM studio")
            for s in cursor.fetchall():
                self.tabel_katalog.insert(
                    "",
                    "end",
                    values=(
                        s.get("id_studio"),
                        s.get("nama_studio"),
                        f"Rp {float(s.get('harga_per_jam') or 0):,.0f}",
                        s.get("kapasitas"),
                        s.get("fasilitas") or "-",
                        s.get("status_ketersediaan") or "Tersedia",
                    ),
                )
        except mysql.connector.Error as err:
            messagebox.showerror(
                "Database Error", f"Gagal memuat katalog studio:\n{err}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def setup_tab_pesan(self):
        ctk.CTkLabel(
            self.tab_pesan,
            text="Form Pemesanan Studio Seni",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=20)

        self.ent_alat = ctk.CTkEntry(
            self.tab_pesan,
            placeholder_text="Nama Studio",
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

        btn_frame = ctk.CTkFrame(self.tab_riwayat, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Upload Bukti Bayar (Pilih File)",
            fg_color="#27ae60",
            hover_color="#219653",
            command=self.upload_bukti_bayar,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Segarkan Riwayat",
            fg_color="#3498db",
            command=self.muat_riwayat,
        ).pack(side="right", padx=5)

        self.muat_riwayat()

    def buat_pesanan(self):
        studio = self.ent_alat.get().strip()
        durasi = self.ent_durasi.get().strip()

        if not self.id_user:
            messagebox.showerror(
                "Error Akun",
                "ID pengguna tidak ditemukan. Silakan login kembali.",
            )
            return

        if not studio:
            messagebox.showwarning(
                "Peringatan", "Nama studio harus diisi!"
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
            cursor = db.cursor(dictionary=True)

            cursor.execute("SELECT harga_per_jam FROM studio WHERE nama_studio = %s", (studio,))
            hasil_studio = cursor.fetchone()

            if not hasil_studio:
                messagebox.showerror("Error", f"Studio dengan nama '{studio}' tidak ditemukan di katalog!")
                return

            harga_per_jam = float(hasil_studio.get("harga_per_jam") or 0)
            jumlah_jam = int(durasi)
            hari_sewa = (jumlah_jam + 23) // 24
            tanggal_kembali = date.today() + timedelta(days=hari_sewa)
            total_biaya = jumlah_jam * harga_per_jam

            # 1. Masukkan ke tabel transaksi
            query_trx = """
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
                query_trx,
                (self.id_user, tanggal_kembali, total_biaya),
            )
            id_transaksi = cursor.lastrowid

            # 2. Masukkan record awal ke tabel pembayaran sesuai skema
            query_byr = """
                INSERT INTO pembayaran
                (
                    id_transaksi,
                    metode_bayar,
                    jumlah_bayar,
                    status_konfirmasi
                )
                VALUES (%s, 'Transfer', %s, 'Menunggu')
            """
            cursor.execute(query_byr, (id_transaksi, total_biaya))
            
            db.commit()

            self.ent_alat.delete(0, "end")
            self.ent_durasi.delete(0, "end")
            self.muat_riwayat()

            messagebox.showinfo(
                "Berhasil",
                "Pesanan berhasil dibuat. Silakan pilih baris pesanan pada tab Riwayat dan klik 'Upload Bukti Bayar'.",
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

    def upload_bukti_bayar(self):
        sel = self.tabel_riwayat.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih transaksi pada tabel riwayat yang ingin diunggah bukti bayarnya!")
            return

        item = self.tabel_riwayat.item(sel[0])
        id_trx = item.get("values")[0]

        file_path = filedialog.askopenfilename(
            title="Pilih File Bukti Pembayaran",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg"), ("All Files", "*.*")]
        )

        if not file_path:
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
            
            # Simpan path bukti bayar ke dalam tabel pembayaran berdasarkan id_transaksi
            query = "UPDATE pembayaran SET bukti_bayar = %s WHERE id_transaksi = %s"
            cursor.execute(query, (file_path, id_trx))
            db.commit()

            messagebox.showinfo("Berhasil", f"Bukti pembayaran untuk Transaksi ID {id_trx} berhasil diunggah!")
            self.muat_riwayat()

        except mysql.connector.Error as err:
            if db and db.is_connected():
                db.rollback()
            messagebox.showerror("Database Error", f"Gagal menyimpan bukti bayar:\n{err}")
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