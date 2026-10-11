import os
import sys
import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector

# Ambil direktori tempat operator_gui.py berada
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class OperatorGUI(ctk.CTk):
    def __init__(self, user=None):
        super().__init__()

        self.user = user or {}
        nama_user = (
            self.user.get("nama_lengkap")
            or self.user.get("username")
            or "Operator"
        )

        self.title(
            f"ArtStudio-Rent — Dashboard Operator / Pengelola "
            f"({str(nama_user).title()})"
        )
        self.geometry("1100x650")
        self.overrideredirect(False)
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ================= HEADER =================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 0))

        ctk.CTkLabel(
            header_frame,
            text=f"Operator: {str(nama_user).title()}",
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff",
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="Keluar (Logout)",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=("Segoe UI", 11, "bold"),
            width=120,
            height=32,
            command=self.aksi_logout,
        ).pack(side="right")

        # ================= STYLING TABEL =================
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

        # ================= TAB UTAMA =================
        self.tab_view = ctk.CTkTabview(
            self, fg_color="#1a1a1a", segmented_button_fg_color="#2b2b2b"
        )
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)

        self.tab_verifikasi = self.tab_view.add("Persetujuan & Bukti Transfer")
        self.tab_inventaris = self.tab_view.add("Manajemen Inventaris (CRUD)")
        self.tab_pengembalian = self.tab_view.add("Batas Waktu & Validasi Barang")
        self.tab_riwayat = self.tab_view.add("Riwayat Transaksi")

        self.setup_tab_verifikasi()
        self.setup_tab_inventaris()
        self.setup_tab_pengembalian()
        self.setup_tab_riwayat()

    def koneksi_db(self):
        return mysql.connector.connect(
            host="localhost", user="root", password="", database="artstudio_rent"
        )

    # ==================================================
    # TAB 1: VERIFIKASI PEMBAYARAN
    # ==================================================
    def setup_tab_verifikasi(self):
        self.tab_verifikasi.grid_columnconfigure(0, weight=3)
        self.tab_verifikasi.grid_columnconfigure(1, weight=5)
        self.tab_verifikasi.grid_rowconfigure(0, weight=1)

        f_kiri = ctk.CTkFrame(
            self.tab_verifikasi, fg_color="#222222", corner_radius=10
        )
        f_kiri.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            f_kiri, text="Verifikasi Pembayaran", font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 5))

        ctk.CTkButton(
            f_kiri,
            text="Muat Antrean Pending",
            fg_color="#3498db",
            hover_color="#2980b9",
            height=40,
            command=self.muat_data_pending,
        ).pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(
            f_kiri,
            text="Setujui Pembayaran (Lunas)",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            height=40,
            command=self.aksi_setujui,
        ).pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(
            f_kiri,
            text="Tolak Bukti Transfer",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            height=40,
            command=self.aksi_tolak,
        ).pack(fill="x", padx=15, pady=10)

        f_kanan = ctk.CTkFrame(self.tab_verifikasi, fg_color="transparent")
        f_kanan.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        table_frame = ctk.CTkFrame(f_kanan, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=5)

        kolom = ("id_trx", "penyewa", "total", "status")
        self.tabel_verif = ttk.Treeview(
            table_frame, columns=kolom, show="headings", height=15
        )
        self.tabel_verif.heading("id_trx", text="ID Trx")
        self.tabel_verif.heading("penyewa", text="Penyewa")
        self.tabel_verif.heading("total", text="Total Biaya")
        self.tabel_verif.heading("status", text="Status")
        self.tabel_verif.column("id_trx", width=50, anchor="center")
        self.tabel_verif.column("penyewa", width=150, anchor="w")
        self.tabel_verif.column("total", width=110, anchor="center")
        self.tabel_verif.column("status", width=90, anchor="center")

        scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tabel_verif.yview
        )
        self.tabel_verif.configure(yscrollcommand=scroll.set)
        self.tabel_verif.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.muat_data_pending()

    def muat_data_pending(self):
        for r in self.tabel_verif.get_children():
            self.tabel_verif.delete(r)
        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM transaksi WHERE status_transaksi = %s",
                ("Pending",),
            )
            for t in cursor.fetchall():
                self.tabel_verif.insert(
                    "",
                    "end",
                    values=(
                        t.get("id_transaksi"),
                        f"User ID: {t.get('id_user')}",
                        f"Rp {float(t.get('total_biaya') or 0):,.0f}",
                        t.get("status_transaksi"),
                    ),
                )
        except mysql.connector.Error as e:
            messagebox.showerror(
                "Database Error", f"Gagal memuat antrean pembayaran:\n{e}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def aksi_setujui(self):
        sel = self.tabel_verif.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih transaksi!")
            return
        id_trx = self.tabel_verif.item(sel[0], "values")[0]
        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor()
            cursor.execute(
                "UPDATE transaksi SET status_transaksi = %s WHERE id_transaksi = %s",
                ("Lunas", id_trx),
            )
            db.commit()
            messagebox.showinfo(
                "Berhasil", f"Transaksi ID {id_trx} disetujui (Lunas)."
            )
            self.muat_data_pending()
            self.muat_data_riwayat()
            self.muat_data_pengembalian()
        except mysql.connector.Error as e:
            if db:
                db.rollback()
            messagebox.showerror("Error", str(e))
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def aksi_tolak(self):
        sel = self.tabel_verif.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih transaksi!")
            return
        id_trx = self.tabel_verif.item(sel[0], "values")[0]
        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor()
            cursor.execute(
                "UPDATE transaksi SET status_transaksi = %s WHERE id_transaksi = %s",
                ("Ditolak", id_trx),
            )
            db.commit()
            messagebox.showinfo("Informasi", f"Transaksi ID {id_trx} ditolak.")
            self.muat_data_pending()
            self.muat_data_riwayat()
        except mysql.connector.Error as e:
            if db:
                db.rollback()
            messagebox.showerror("Error", str(e))
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    # ==================================================
    # TAB 2: MANAJEMEN INVENTARIS (TERHUBUNG KE DATABASE)
    # ==================================================
    def setup_tab_inventaris(self):
        self.tab_inventaris.grid_columnconfigure(0, weight=3)
        self.tab_inventaris.grid_columnconfigure(1, weight=5)
        self.tab_inventaris.grid_rowconfigure(0, weight=1)

        f_kiri = ctk.CTkFrame(
            self.tab_inventaris, fg_color="#222222", corner_radius=10
        )
        f_kiri.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            f_kiri, text="Form Kelola Inventaris", font=("Segoe UI", 16, "bold")
        ).pack(pady=(15, 10))

        self.ent_nama = ctk.CTkEntry(
            f_kiri, placeholder_text="Nama Alat / Studio", height=35
        )
        self.ent_nama.pack(fill="x", padx=15, pady=8)
        self.ent_kat = ctk.CTkEntry(
            f_kiri, placeholder_text="Kategori (Opsional)", height=35
        )
        self.ent_kat.pack(fill="x", padx=15, pady=8)
        self.ent_hrg = ctk.CTkEntry(
            f_kiri, placeholder_text="Tarif per Jam", height=35
        )
        self.ent_hrg.pack(fill="x", padx=15, pady=8)

        btn_f = ctk.CTkFrame(f_kiri, fg_color="transparent")
        btn_f.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(
            btn_f,
            text="Tambah",
            fg_color="#2ecc71",
            width=90,
            command=self.tambah_alat,
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            btn_f,
            text="Ubah",
            fg_color="#f1c40f",
            text_color="#000",
            width=90,
            command=self.ubah_alat,
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            btn_f,
            text="Hapus",
            fg_color="#e74c3c",
            width=90,
            command=self.hapus_alat,
        ).pack(side="left", expand=True)

        f_kanan = ctk.CTkFrame(self.tab_inventaris, fg_color="transparent")
        f_kanan.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        table_frame = ctk.CTkFrame(f_kanan, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=5)

        kolom_inv = ("id_alat", "nama", "kategori", "harga")
        self.tabel_inv = ttk.Treeview(
            table_frame, columns=kolom_inv, show="headings", height=15
        )
        self.tabel_inv.heading("id_alat", text="ID")
        self.tabel_inv.heading("nama", text="Nama Alat / Studio")
        self.tabel_inv.heading("kategori", text="Kategori")
        self.tabel_inv.heading("harga", text="Tarif / Jam")
        self.tabel_inv.column("id_alat", width=40, anchor="center")
        self.tabel_inv.column("nama", width=180, anchor="w")
        self.tabel_inv.column("kategori", width=120, anchor="w")
        self.tabel_inv.column("harga", width=100, anchor="center")

        # Event: klik baris tabel untuk mengisi form otomatis
        self.tabel_inv.bind("<<TreeviewSelect>>", self.pilih_data_inventaris)

        scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tabel_inv.yview
        )
        self.tabel_inv.configure(yscrollcommand=scroll.set)
        self.tabel_inv.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.muat_data_inventaris()

    def muat_data_inventaris(self):
        for r in self.tabel_inv.get_children():
            self.tabel_inv.delete(r)
        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM studio")
            for s in cursor.fetchall():
                # Tangani jika kolom kategori tidak ada di database agar tidak error
                kategori_val = s.get("kategori") if "kategori" in s else "Studio"
                self.tabel_inv.insert(
                    "",
                    "end",
                    values=(
                        s.get("id_studio") or s.get("id_alat", "-"),
                        s.get("nama_studio") or s.get("nama_alat", "-"),
                        kategori_val,
                        f"Rp {float(s.get('harga_per_jam') or 0):,.0f}",
                    ),
                )
        except mysql.connector.Error as e:
            messagebox.showerror(
                "Database Error", f"Gagal memuat inventaris:\n{e}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def pilih_data_inventaris(self, event):
        sel = self.tabel_inv.selection()
        if sel:
            item = self.tabel_inv.item(sel[0])
            values = item.get("values")
            if values and len(values) >= 4:
                self.ent_nama.delete(0, "end")
                self.ent_nama.insert(0, str(values[1]))

                self.ent_kat.delete(0, "end")
                self.ent_kat.insert(0, str(values[2]))

                harga_str = (
                    str(values[3]).replace("Rp", "").replace(",", "").strip()
                )
                self.ent_hrg.delete(0, "end")
                self.ent_hrg.insert(0, harga_str)

    def tambah_alat(self):
        nama = self.ent_nama.get().strip()
        harga = self.ent_hrg.get().strip()

        if not nama or not harga:
            messagebox.showwarning(
                "Peringatan", "Nama alat/studio dan harga wajib diisi!"
            )
            return

        if not harga.isdigit():
            messagebox.showwarning("Peringatan", "Tarif per jam harus berupa angka!")
            return

        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor()
            # Query disesuaikan dengan kolom dasar tabel studio (tanpa kategori untuk menghindari error jika kolom belum ada)
            query = "INSERT INTO studio (nama_studio, harga_per_jam) VALUES (%s, %s)"
            cursor.execute(query, (nama, int(harga)))
            db.commit()

            messagebox.showinfo("Berhasil", "Data inventaris berhasil ditambahkan!")
            self.ent_nama.delete(0, "end")
            self.ent_kat.delete(0, "end")
            self.ent_hrg.delete(0, "end")
            self.muat_data_inventaris()

        except mysql.connector.Error as e:
            if db:
                db.rollback()
            messagebox.showerror("Database Error", f"Gagal menambah data:\n{e}")
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def ubah_alat(self):
        sel = self.tabel_inv.selection()
        if not sel:
            messagebox.showwarning(
                "Peringatan", "Pilih data inventaris yang ingin diubah pada tabel!"
            )
            return

        item = self.tabel_inv.item(sel[0])
        id_alat = item.get("values")[0]

        nama = self.ent_nama.get().strip()
        harga = self.ent_hrg.get().strip()

        if not nama or not harga:
            messagebox.showwarning("Peringatan", "Nama dan harga tidak boleh kosong!")
            return

        if not harga.isdigit():
            messagebox.showwarning("Peringatan", "Tarif per jam harus berupa angka!")
            return

        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor()
            query = "UPDATE studio SET nama_studio = %s, harga_per_jam = %s WHERE id_studio = %s"
            cursor.execute(query, (nama, int(harga), id_alat))
            db.commit()

            messagebox.showinfo(
                "Berhasil", f"Data inventaris ID {id_alat} berhasil diperbarui!"
            )
            self.ent_nama.delete(0, "end")
            self.ent_kat.delete(0, "end")
            self.ent_hrg.delete(0, "end")
            self.muat_data_inventaris()

        except mysql.connector.Error as e:
            if db:
                db.rollback()
            messagebox.showerror("Database Error", f"Gagal mengubah data:\n{e}")
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def hapus_alat(self):
        sel = self.tabel_inv.selection()
        if not sel:
            messagebox.showwarning(
                "Peringatan", "Pilih data inventaris yang ingin dihapus pada tabel!"
            )
            return

        item = self.tabel_inv.item(sel[0])
        id_alat = item.get("values")[0]
        nama_alat = item.get("values")[1]

        if not messagebox.askyesno(
            "Konfirmasi Hapus",
            f"Apakah Anda yakin ingin menghapus '{nama_alat}' dari inventaris?",
        ):
            return

        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor()
            query = "DELETE FROM studio WHERE id_studio = %s"
            cursor.execute(query, (id_alat,))
            db.commit()

            messagebox.showinfo("Berhasil", "Data inventaris berhasil dihapus.")
            self.ent_nama.delete(0, "end")
            self.ent_kat.delete(0, "end")
            self.ent_hrg.delete(0, "end")
            self.muat_data_inventaris()

        except mysql.connector.Error as e:
            if db:
                db.rollback()
            messagebox.showerror(
                "Database Error", f"Gagal menghapus data:\n{e}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    # ==================================================
    # TAB 3: PENGEMBALIAN & VALIDASI BARANG
    # ==================================================
    def setup_tab_pengembalian(self):
        self.tab_pengembalian.grid_columnconfigure(0, weight=1)
        self.tab_pengembalian.grid_rowconfigure(0, weight=1)

        f_utama = ctk.CTkFrame(self.tab_pengembalian, fg_color="transparent")
        f_utama.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(
            f_utama,
            text="Batas Waktu & Validasi Kondisi Barang",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(5, 10))

        table_frame = ctk.CTkFrame(f_utama, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=5)

        kolom_k = ("id_trx", "penyewa", "tgl_sewa", "jatuh_tempo", "kondisi")
        self.tabel_kembali = ttk.Treeview(
            table_frame, columns=kolom_k, show="headings", height=13
        )
        self.tabel_kembali.heading("id_trx", text="ID Trx")
        self.tabel_kembali.heading("penyewa", text="Penyewa")
        self.tabel_kembali.heading("tgl_sewa", text="Tanggal Sewa")
        self.tabel_kembali.heading("jatuh_tempo", text="Tenggat Waktu")
        self.tabel_kembali.heading("kondisi", text="Kondisi Barang")
        self.tabel_kembali.column("id_trx", width=50, anchor="center")
        self.tabel_kembali.column("penyewa", width=150, anchor="w")
        self.tabel_kembali.column("tgl_sewa", width=120, anchor="center")
        self.tabel_kembali.column("jatuh_tempo", width=130, anchor="center")
        self.tabel_kembali.column("kondisi", width=120, anchor="center")

        scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tabel_kembali.yview
        )
        self.tabel_kembali.configure(yscrollcommand=scroll.set)
        self.tabel_kembali.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        ctk.CTkButton(
            f_utama,
            text="Validasi Kondisi Barang (Aman / Selesai)",
            fg_color="#3498db",
            height=40,
            command=self.aksi_validasi,
        ).pack(fill="x", pady=10)
        self.muat_data_pengembalian()

    def muat_data_pengembalian(self):
        for r in self.tabel_kembali.get_children():
            self.tabel_kembali.delete(r)
        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM transaksi WHERE status_transaksi = %s", ("Lunas",)
            )
            for t in cursor.fetchall():
                self.tabel_kembali.insert(
                    "",
                    "end",
                    values=(
                        t.get("id_transaksi"),
                        f"User ID: {t.get('id_user')}",
                        t.get("tgl_sewa", "-"),
                        "Aktif",
                        "Aman",
                    ),
                )
        except mysql.connector.Error as e:
            messagebox.showerror(
                "Database Error", f"Gagal memuat data pengembalian:\n{e}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def aksi_validasi(self):
        if not self.tabel_kembali.selection():
            messagebox.showwarning("Peringatan", "Pilih transaksi peminjaman!")
            return
        messagebox.showinfo("Berhasil", "Kondisi barang divalidasi aman.")

    # ==================================================
    # TAB 4: RIWAYAT TRANSAKSI
    # ==================================================
    def setup_tab_riwayat(self):
        self.tab_riwayat.grid_columnconfigure(0, weight=1)
        self.tab_riwayat.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.tab_riwayat,
            text="Riwayat Transaksi Penyewaan",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        table_frame = ctk.CTkFrame(self.tab_riwayat, fg_color="transparent")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        kolom = ("id_trx", "id_user", "total", "status", "tgl_sewa")
        self.tabel_riwayat = ttk.Treeview(
            table_frame, columns=kolom, show="headings", height=15
        )
        judul = {
            "id_trx": "ID Transaksi",
            "id_user": "ID Penyewa",
            "total": "Total Biaya",
            "status": "Status",
            "tgl_sewa": "Tanggal Sewa",
        }
        for kolom_id, teks in judul.items():
            self.tabel_riwayat.heading(kolom_id, text=teks)
        self.tabel_riwayat.column("id_trx", width=100, anchor="center")
        self.tabel_riwayat.column("id_user", width=120, anchor="center")
        self.tabel_riwayat.column("total", width=160, anchor="center")
        self.tabel_riwayat.column("status", width=140, anchor="center")
        self.tabel_riwayat.column("tgl_sewa", width=160, anchor="center")

        scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tabel_riwayat.yview
        )
        self.tabel_riwayat.configure(yscrollcommand=scroll.set)
        self.tabel_riwayat.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        tombol = ctk.CTkFrame(self.tab_riwayat, fg_color="transparent")
        tombol.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkButton(
            tombol,
            text="Muat Ulang Riwayat",
            fg_color="#3498db",
            command=self.muat_data_riwayat,
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            tombol,
            text="Hapus Riwayat Terpilih",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.hapus_riwayat_transaksi,
        ).pack(side="left")

        self.muat_data_riwayat()

    def muat_data_riwayat(self):
        for r in self.tabel_riwayat.get_children():
            self.tabel_riwayat.delete(r)
        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM transaksi ORDER BY id_transaksi DESC")
            for t in cursor.fetchall():
                self.tabel_riwayat.insert(
                    "",
                    "end",
                    values=(
                        t.get("id_transaksi"),
                        t.get("id_user"),
                        f"Rp {float(t.get('total_biaya') or 0):,.0f}",
                        t.get("status_transaksi", "-"),
                        t.get("tgl_sewa", "-"),
                    ),
                )
        except mysql.connector.Error as e:
            messagebox.showerror(
                "Database Error", f"Gagal memuat riwayat transaksi:\n{e}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def hapus_riwayat_transaksi(self):
        sel = self.tabel_riwayat.selection()
        if not sel:
            messagebox.showwarning(
                "Peringatan", "Pilih riwayat transaksi yang ingin dihapus!"
            )
            return

        nilai = self.tabel_riwayat.item(sel[0], "values")
        id_trx = nilai[0]

        if not messagebox.askyesno(
            "Konfirmasi Hapus",
            f"Yakin ingin menghapus transaksi ID {id_trx} dari database?\n\n"
            "Penghapusan bersifat permanen.",
        ):
            return

        db = None
        cursor = None
        try:
            db = self.koneksi_db()
            cursor = db.cursor()
            cursor.execute(
                "DELETE FROM transaksi WHERE id_transaksi = %s", (id_trx,)
            )
            if cursor.rowcount == 0:
                db.rollback()
                messagebox.showwarning(
                    "Informasi", "Transaksi tidak ditemukan atau sudah dihapus."
                )
                self.muat_data_riwayat()
                return
            db.commit()
            messagebox.showinfo(
                "Berhasil", f"Riwayat transaksi ID {id_trx} berhasil dihapus."
            )
            self.muat_data_riwayat()
            self.muat_data_pending()
            self.muat_data_pengembalian()
        except mysql.connector.Error as e:
            if db:
                db.rollback()
            messagebox.showerror("Gagal Menghapus", f"Detail: {e}")
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def aksi_logout(self):
        if messagebox.askyesno(
            "Konfirmasi", "Apakah Anda ingin keluar ke halaman login?"
        ):
            self.destroy()
            try:
                from login_gui import LoginGUI

                LoginGUI().mainloop()
            except ImportError:
                pass


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        user = {
            "id_user": int(sys.argv[1]),
            "nama_lengkap": sys.argv[2],
            "role": sys.argv[3],
        }
        OperatorGUI(user).mainloop()
    else:
        OperatorGUI(
            {"nama_lengkap": "Operator Studio", "role": "operator"}
        ).mainloop()