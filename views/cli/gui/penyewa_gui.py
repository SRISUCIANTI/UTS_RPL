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
        self.geometry("1150x680")
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

        self.tab_katalog = self.tab_view.add("Daftar Studio & Alat")
        self.tab_pesan = self.tab_view.add("Buat Pesanan Studio")
        self.tab_bayar = self.tab_view.add("Bayar Pesanan & Denda")
        self.tab_riwayat = self.tab_view.add("Pesanan & Riwayat Saya")

        self.setup_tab_katalog()
        self.setup_tab_pesan()
        self.setup_tab_bayar()
        self.setup_tab_riwayat()

    def setup_tab_katalog(self):
        self.tab_katalog.grid_columnconfigure(0, weight=1)
        self.tab_katalog.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.tab_katalog,
            text="Katalog Studio Seni",
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
        ).pack(pady=(20, 10))

        self.ent_alat = ctk.CTkEntry(
            self.tab_pesan,
            placeholder_text="ID Studio atau Nama Studio",
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
            text="Kirim & Buat Pesanan",
            fg_color="#3498db",
            hover_color="#2980b9",
            width=350,
            height=42,
            command=self.buat_pesanan,
        ).pack(pady=15)

    def setup_tab_bayar(self):
        self.tab_bayar.grid_columnconfigure(0, weight=1)
        self.tab_bayar.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self.tab_bayar, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        kolom = ("id_trx", "label", "tgl", "nominal", "denda", "jenis")
        self.tabel_tagihan = ttk.Treeview(
            container, columns=kolom, show="headings", height=12
        )
        self.tabel_tagihan.heading("id_trx", text="ID Trx")
        self.tabel_tagihan.heading("label", text="Keterangan")
        self.tabel_tagihan.heading("tgl", text="Tanggal")
        self.tabel_tagihan.heading("nominal", text="Total Biaya")
        self.tabel_tagihan.heading("denda", text="Denda")
        self.tabel_tagihan.heading("jenis", text="Jenis Tagihan")

        self.tabel_tagihan.column("id_trx", width=50, anchor="center")
        self.tabel_tagihan.column("label", width=150, anchor="w")
        self.tabel_tagihan.column("tgl", width=100, anchor="center")
        self.tabel_tagihan.column("nominal", width=100, anchor="center")
        self.tabel_tagihan.column("denda", width=100, anchor="center")
        self.tabel_tagihan.column("jenis", width=100, anchor="center")

        scroll = ttk.Scrollbar(container, orient="vertical", command=self.tabel_tagihan.yview)
        self.tabel_tagihan.configure(yscrollcommand=scroll.set)
        self.tabel_tagihan.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        btn_f = ctk.CTkFrame(self.tab_bayar, fg_color="transparent")
        btn_f.pack(fill="x", pady=10)

        ctk.CTkButton(
            btn_f,
            text="Bayar via Transfer (Upload Bukti)",
            fg_color="#27ae60",
            hover_color="#219653",
            command=self.bayar_transfer,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_f,
            text="Bayar via Tunai (Cash)",
            fg_color="#f39c12",
            hover_color="#d35400",
            command=self.bayar_tunai,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_f,
            text="Segarkan Tagihan",
            fg_color="#3498db",
            command=self.muat_tagihan,
        ).pack(side="right", padx=5)

        self.muat_tagihan()

    def setup_tab_riwayat(self):
        self.tab_riwayat.grid_columnconfigure(0, weight=1)
        self.tab_riwayat.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(
            self.tab_riwayat, fg_color="transparent"
        )
        container.pack(fill="both", expand=True, padx=10, pady=10)

        kolom = ("id_trx", "tgl", "total", "denda", "status")
        self.tabel_riwayat = ttk.Treeview(
            container, columns=kolom, show="headings", height=13
        )

        self.tabel_riwayat.heading("id_trx", text="ID Trx")
        self.tabel_riwayat.heading("tgl", text="Tanggal Sewa")
        self.tabel_riwayat.heading("total", text="Total Biaya")
        self.tabel_riwayat.heading("denda", text="Denda")
        self.tabel_riwayat.heading("status", text="Status Pembayaran")

        self.tabel_riwayat.column("id_trx", width=60, anchor="center")
        self.tabel_riwayat.column("tgl", width=120, anchor="center")
        self.tabel_riwayat.column("total", width=120, anchor="center")
        self.tabel_riwayat.column("denda", width=110, anchor="center")
        self.tabel_riwayat.column("status", width=140, anchor="center")

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
            text="Segarkan Riwayat",
            fg_color="#3498db",
            command=self.muat_riwayat,
        ).pack(side="right", padx=5)

        self.muat_riwayat()

    def buat_pesanan(self):
        input_studio = self.ent_alat.get().strip()
        durasi = self.ent_durasi.get().strip()

        if not self.id_user:
            messagebox.showerror(
                "Error Akun",
                "ID pengguna tidak ditemukan. Silakan login kembali.",
            )
            return

        if not input_studio:
            messagebox.showwarning(
                "Peringatan", "ID Studio atau Nama Studio harus diisi!"
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

            if input_studio.isdigit():
                cursor.execute("SELECT harga_per_jam FROM studio WHERE id_studio = %s", (int(input_studio),))
            else:
                cursor.execute("SELECT harga_per_jam FROM studio WHERE nama_studio = %s", (input_studio,))
            
            hasil_studio = cursor.fetchone()

            if not hasil_studio:
                messagebox.showerror("Error", f"Studio dengan data '{input_studio}' tidak ditemukan di katalog!")
                return

            harga_per_jam = float(hasil_studio.get("harga_per_jam") or 0)
            jumlah_jam = int(durasi)
            hari_sewa = (jumlah_jam + 23) // 24
            tanggal_kembali = date.today() + timedelta(days=hari_sewa)
            total_biaya = jumlah_jam * harga_per_jam

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

            query_byr = """
                INSERT INTO pembayaran
                (
                    id_transaksi,
                    metode_bayar,
                    jumlah_bayar,
                    status_konfirmasi
                )
                VALUES (%s, 'Transfer', %s, 'Pending')
            """
            cursor.execute(query_byr, (id_transaksi, total_biaya))
            
            db.commit()

            self.ent_alat.delete(0, "end")
            self.ent_durasi.delete(0, "end")
            self.muat_tagihan()
            self.muat_riwayat()

            messagebox.showinfo(
                "Berhasil",
                "Pesanan berhasil dibuat. Silakan buka tab 'Bayar Pesanan & Denda' untuk melakukan pembayaran.",
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

    def muat_tagihan(self):
        for row in self.tabel_tagihan.get_children():
            self.tabel_tagihan.delete(row)

        if not self.id_user:
            return

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id_transaksi, tgl_sewa, total_biaya, denda, status_transaksi
                FROM transaksi
                WHERE id_user = %s AND status_transaksi = 'Pending'
                """,
                (self.id_user,)
            )
            for t in cursor.fetchall():
                denda_val = float(t.get('denda') or 0)
                self.tabel_tagihan.insert("", "end", values=(
                    t['id_transaksi'], "Sewa Studio", t['tgl_sewa'],
                    f"Rp {float(t['total_biaya']):,.0f}", f"Rp {denda_val:,.0f}", "Sewa Normal"
                ))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Gagal memuat tagihan:\n{err}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def bayar_transfer(self):
        sel = self.tabel_tagihan.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih tagihan pada tabel terlebih dahulu!")
            return
        item = self.tabel_tagihan.item(sel[0])
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
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor()
            cursor.execute("UPDATE pembayaran SET bukti_bayar = %s, metode_bayar = 'Transfer', status_konfirmasi = 'Menunggu' WHERE id_transaksi = %s", (file_path, id_trx))
            cursor.execute("UPDATE transaksi SET status_transaksi = 'Menunggu Konfirmasi' WHERE id_transaksi = %s", (id_trx,))
            db.commit()
            messagebox.showinfo("Berhasil", f"Bukti bayar untuk Transaksi ID {id_trx} berhasil diunggah!")
            self.muat_tagihan()
            self.muat_riwayat()
        except mysql.connector.Error as err:
            if db and db.is_connected(): db.rollback()
            messagebox.showerror("Database Error", f"Gagal mengunggah bukti bayar:\n{err}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def bayar_tunai(self):
        sel = self.tabel_tagihan.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih tagihan pada tabel terlebih dahulu!")
            return
        item = self.tabel_tagihan.item(sel[0])
        id_trx = item.get("values")[0]

        if messagebox.askyesno("Konfirmasi Tunai", f"Konfirmasi pembayaran tunai untuk Transaksi ID {id_trx}?"):
            db = None
            cursor = None
            try:
                db = mysql.connector.connect(
                    host="localhost", user="root", password="", database="artstudio_rent"
                )
                cursor = db.cursor()
                cursor.execute("UPDATE pembayaran SET metode_bayar = 'Tunai', status_konfirmasi = 'Menunggu' WHERE id_transaksi = %s", (id_trx,))
                cursor.execute("UPDATE transaksi SET status_transaksi = 'Menunggu Konfirmasi' WHERE id_transaksi = %s", (id_trx,))
                db.commit()
                messagebox.showinfo("Berhasil", f"Pembayaran tunai untuk Transaksi ID {id_trx} dicatat dan menunggu verifikasi operator!")
                self.muat_tagihan()
                self.muat_riwayat()
            except mysql.connector.Error as err:
                if db and db.is_connected(): db.rollback()
                messagebox.showerror("Database Error", f"Gagal mencatat pembayaran:\n{err}")
            finally:
                if cursor: cursor.close()
                if db and db.is_connected(): db.close()

    def muat_riwayat(self):
        for row in self.tabel_riwayat.get_children():
            self.tabel_riwayat.delete(row)

        if not self.id_user:
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
                       total_biaya, denda, status_transaksi
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
                        f"Rp {float(transaksi['denda'] or 0):,.0f}",
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
        user = {
            "id_user": 3,
            "nama_lengkap": "Sri Suci",
            "role": "penyewa",
        }
        PenyewaGUI(user).mainloop()