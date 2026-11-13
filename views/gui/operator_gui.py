import os
import re
import sys
import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------
# FUNGSI BANTU MANAJEMEN ALAT (murni, tanpa GUI/DB agar mudah diuji)
# ---------------------------------------------------------------
def parse_nominal(teks):
    """Ubah teks harga gaya Indonesia menjadi float.
    Diterima: 25000 | 25.000 | 25.000,50 | 25,5 | Rp 25.000
    Ditolak (ValueError): kosong, huruf, negatif, nan/inf, notasi ilmiah."""
    t = str(teks).strip().replace(" ", "")
    if t.lower().startswith("rp"):
        t = t[2:]
    if "," in t:  # koma = desimal, titik = pemisah ribuan
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", t):  # 25.000 / 1.250.000 = ribuan
        t = t.replace(".", "")
    if not re.fullmatch(r"\d+(\.\d+)?", t):
        raise ValueError("bukan angka valid")
    return float(t)


def validasi_alat(nama, harga_teks, stok_teks):
    """Validasi input form alat. Mengembalikan (True, (nama, harga, stok))
    atau (False, pesan_error)."""
    nama = (nama or "").strip()
    if not nama:
        return False, "Nama alat wajib diisi!"
    try:
        harga = parse_nominal(harga_teks)
    except ValueError:
        return False, "Harga sewa per hari harus berupa angka (contoh: 25.000)."
    if harga <= 0:
        return False, "Harga sewa per hari harus lebih dari 0."
    stok_teks = (stok_teks or "").strip()
    if not re.fullmatch(r"\d+", stok_teks):
        return False, "Stok harus berupa bilangan bulat 0 atau lebih."
    return True, (nama, harga, int(stok_teks))


def format_rupiah(nilai):
    """Rp 25.000 (tanpa desimal bila bulat) / Rp 25.000,50."""
    nilai = float(nilai or 0)
    if nilai == int(nilai):
        teks = f"{int(nilai):,}".replace(",", ".")
    else:
        teks = f"{nilai:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Rp {teks}"


def _koneksi():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="artstudio_rent"
    )


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
        self.geometry("1150x680")
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

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
            self, fg_color="#1a1a1a", segmented_button_fg_color="#2b2b2b"
        )
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)

        self.tab_verifikasi = self.tab_view.add("Persetujuan & Bukti Transfer")
        self.tab_inventaris = self.tab_view.add("Manajemen Studio (CRUD)")
        self.tab_alat = self.tab_view.add("Manajemen Alat (CRUD)")
        self.tab_pengembalian = self.tab_view.add("Batas Waktu & Validasi Barang")
        self.tab_riwayat = self.tab_view.add("Riwayat Transaksi")

        self.setup_tab_verifikasi()
        self.setup_tab_inventaris()
        self.setup_tab_alat()
        self.setup_tab_pengembalian()
        self.setup_tab_riwayat()

    # ================= TAB 1: VERIFIKASI PEMBAYARAN =================
    def setup_tab_verifikasi(self):
        self.tab_verifikasi.grid_columnconfigure(0, weight=3)
        self.tab_verifikasi.grid_columnconfigure(1, weight=5)
        self.tab_verifikasi.grid_rowconfigure(0, weight=1)

        f_kiri = ctk.CTkFrame(self.tab_verifikasi, fg_color="#222222", corner_radius=10)
        f_kiri.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            f_kiri, text="Verifikasi Pembayaran", font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 5))

        ctk.CTkButton(
            f_kiri,
            text="Muat Antrean Pending",
            fg_color="#3498db",
            height=40,
            command=self.muat_data_pending,
        ).pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            f_kiri,
            text="Lihat Bukti Bayar",
            fg_color="#9b59b6",
            height=40,
            command=self.lihat_bukti_bayar,
        ).pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            f_kiri,
            text="Setujui Pembayaran (Lunas)",
            fg_color="#2ecc71",
            height=40,
            command=self.aksi_setujui,
        ).pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            f_kiri,
            text="Tolak Bukti Transfer",
            fg_color="#e74c3c",
            height=40,
            command=self.aksi_tolak,
        ).pack(fill="x", padx=15, pady=10)

        f_kanan = ctk.CTkFrame(self.tab_verifikasi, fg_color="transparent")
        f_kanan.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        table_frame = ctk.CTkFrame(f_kanan, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=5)

        kolom = ("id_trx", "penyewa", "total", "status", "bukti")
        self.tabel_verif = ttk.Treeview(table_frame, columns=kolom, show="headings", height=15)
        self.tabel_verif.heading("id_trx", text="ID Trx")
        self.tabel_verif.heading("penyewa", text="Penyewa")
        self.tabel_verif.heading("total", text="Total Biaya")
        self.tabel_verif.heading("status", text="Status")
        self.tabel_verif.heading("bukti", text="File Bukti Bayar")

        self.tabel_verif.column("id_trx", width=50, anchor="center")
        self.tabel_verif.column("penyewa", width=120, anchor="w")
        self.tabel_verif.column("total", width=100, anchor="center")
        self.tabel_verif.column("status", width=80, anchor="center")
        self.tabel_verif.column("bukti", width=150, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabel_verif.yview)
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
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT t.id_transaksi, t.total_biaya, t.status_transaksi, u.username, u.nama_lengkap, p.bukti_bayar, p.id_pembayaran
                FROM transaksi t
                JOIN users u ON t.id_user = u.id_user
                LEFT JOIN pembayaran p ON t.id_transaksi = p.id_transaksi
                WHERE t.status_transaksi = 'Menunggu Konfirmasi' OR t.status_transaksi = 'Pending'
                """
            )
            for t in cursor.fetchall():
                path_bukti = t.get("bukti_bayar") or "-"
                nama_file = os.path.basename(path_bukti) if path_bukti != "-" else "-"
                self.tabel_verif.insert(
                    "",
                    "end",
                    values=(
                        t.get("id_transaksi"),
                        f"{t.get('username', '-')} ({t.get('nama_lengkap', '-')})",
                        f"Rp {float(t.get('total_biaya') or 0):,.0f}",
                        t.get("status_transaksi"),
                        nama_file,
                    ),
                )
        except Exception as e:
            messagebox.showerror("Database Error", f"Gagal memuat antrean:\n{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def lihat_bukti_bayar(self):
        sel = self.tabel_verif.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih data transaksi pada tabel terlebih dahulu!")
            return
        item = self.tabel_verif.item(sel[0])
        id_trx = item.get("values")[0]

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT bukti_bayar FROM pembayaran WHERE id_transaksi = %s", (id_trx,))
            res = cursor.fetchone()
            if not res or not res.get("bukti_bayar"):
                messagebox.showinfo("Informasi", "Belum ada file bukti bayar yang diunggah.")
                return
            file_path = res.get("bukti_bayar")
            if not os.path.exists(file_path):
                messagebox.showerror("Error", f"File tidak ditemukan:\n{file_path}")
                return
            if sys.platform == "win32":
                os.startfile(file_path)
            else:
                subprocess.Popen(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def aksi_setujui(self):
        sel = self.tabel_verif.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih transaksi!")
            return
        id_trx = self.tabel_verif.item(sel[0]).get("values")[0]

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor()
            cursor.execute("UPDATE transaksi SET status_transaksi = 'Lunas' WHERE id_transaksi = %s", (id_trx,))
            cursor.execute("UPDATE pembayaran SET status_konfirmasi = 'Diterima' WHERE id_transaksi = %s", (id_trx,))
            db.commit()
            messagebox.showinfo("Berhasil", f"Transaksi ID {id_trx} disetujui (Lunas).")
            self.muat_data_pending()
            self.muat_data_riwayat()
            self.muat_data_pengembalian()
        except Exception as e:
            if db: db.rollback()
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def aksi_tolak(self):
        sel = self.tabel_verif.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih transaksi!")
            return
        id_trx = self.tabel_verif.item(sel[0]).get("values")[0]

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor()
            cursor.execute("UPDATE transaksi SET status_transaksi = 'Pending' WHERE id_transaksi = %s", (id_trx,))
            cursor.execute("UPDATE pembayaran SET status_konfirmasi = 'Ditolak' WHERE id_transaksi = %s", (id_trx,))
            db.commit()
            messagebox.showinfo("Informasi", f"Bukti transfer untuk Transaksi ID {id_trx} ditolak.")
            self.muat_data_pending()
            self.muat_data_riwayat()
        except Exception as e:
            if db: db.rollback()
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    # ================= TAB 2: MANAJEMEN INVENTARIS STUDIO =================
    def setup_tab_inventaris(self):
        self.tab_inventaris.grid_columnconfigure(0, weight=3)
        self.tab_inventaris.grid_columnconfigure(1, weight=5)
        self.tab_inventaris.grid_rowconfigure(0, weight=1)

        f_kiri = ctk.CTkFrame(self.tab_inventaris, fg_color="#222222", corner_radius=10)
        f_kiri.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(f_kiri, text="Form Kelola Studio", font=("Segoe UI", 16, "bold")).pack(pady=(15, 10))

        self.ent_nama = ctk.CTkEntry(f_kiri, placeholder_text="Nama Studio", height=35)
        self.ent_nama.pack(fill="x", padx=15, pady=6)
        self.ent_harga = ctk.CTkEntry(f_kiri, placeholder_text="Harga per Jam", height=35)
        self.ent_harga.pack(fill="x", padx=15, pady=6)
        self.ent_kapasitas = ctk.CTkEntry(f_kiri, placeholder_text="Kapasitas", height=35)
        self.ent_kapasitas.pack(fill="x", padx=15, pady=6)
        self.ent_fasilitas = ctk.CTkEntry(f_kiri, placeholder_text="Fasilitas", height=35)
        self.ent_fasilitas.pack(fill="x", padx=15, pady=6)

        btn_f = ctk.CTkFrame(f_kiri, fg_color="transparent")
        btn_f.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(btn_f, text="Tambah", fg_color="#2ecc71", width=90, command=self.tambah_studio).pack(side="left", expand=True)
        ctk.CTkButton(btn_f, text="Ubah", fg_color="#f1c40f", text_color="#000", width=90, command=self.ubah_studio).pack(side="left", expand=True)
        ctk.CTkButton(btn_f, text="Hapus", fg_color="#e74c3c", width=90, command=self.hapus_studio).pack(side="left", expand=True)

        f_kanan = ctk.CTkFrame(self.tab_inventaris, fg_color="transparent")
        f_kanan.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        table_frame = ctk.CTkFrame(f_kanan, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=5)

        kolom_inv = ("id_studio", "nama", "harga", "kapasitas", "fasilitas", "status")
        self.tabel_inv = ttk.Treeview(table_frame, columns=kolom_inv, show="headings", height=15)
        self.tabel_inv.heading("id_studio", text="ID")
        self.tabel_inv.heading("nama", text="Nama Studio")
        self.tabel_inv.heading("harga", text="Harga / Jam")
        self.tabel_inv.heading("kapasitas", text="Kapasitas")
        self.tabel_inv.heading("fasilitas", text="Fasilitas")
        self.tabel_inv.heading("status", text="Status")

        self.tabel_inv.column("id_studio", width=40, anchor="center")
        self.tabel_inv.column("nama", width=160, anchor="w")
        self.tabel_inv.column("harga", width=90, anchor="center")
        self.tabel_inv.column("kapasitas", width=60, anchor="center")
        self.tabel_inv.column("fasilitas", width=180, anchor="w")
        self.tabel_inv.column("status", width=80, anchor="center")

        self.tabel_inv.bind("<<TreeviewSelect>>", self.pilih_data_inventaris)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabel_inv.yview)
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
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM studio")
            for s in cursor.fetchall():
                self.tabel_inv.insert(
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
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def pilih_data_inventaris(self, event):
        sel = self.tabel_inv.selection()
        if sel:
            values = self.tabel_inv.item(sel[0]).get("values")
            if values and len(values) >= 6:
                self.ent_nama.delete(0, "end")
                self.ent_nama.insert(0, str(values[1]))
                self.ent_harga.delete(0, "end")
                self.ent_harga.insert(0, str(values[2]).replace("Rp", "").replace(",", "").strip())
                self.ent_kapasitas.delete(0, "end")
                self.ent_kapasitas.insert(0, str(values[3]))
                self.ent_fasilitas.delete(0, "end")
                self.ent_fasilitas.insert(0, str(values[4]))

    def tambah_studio(self):
        nama = self.ent_nama.get().strip()
        harga = self.ent_harga.get().strip()
        kapasitas = self.ent_kapasitas.get().strip()
        fasilitas = self.ent_fasilitas.get().strip()

        if not nama or not harga or not kapasitas:
            messagebox.showwarning("Peringatan", "Semua field wajib diisi!")
            return
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO studio (nama_studio, kapasitas, harga_per_jam, fasilitas, status_ketersediaan) VALUES (%s, %s, %s, %s, 'Tersedia')",
                (nama, int(kapasitas), float(harga), fasilitas)
            )
            db.commit()
            messagebox.showinfo("Berhasil", "Studio berhasil ditambahkan.")
            self.muat_data_inventaris()
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def ubah_studio(self):
        sel = self.tabel_inv.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih studio yang akan diubah!")
            return
        id_studio = self.tabel_inv.item(sel[0]).get("values")[0]
        nama = self.ent_nama.get().strip()
        harga = self.ent_harga.get().strip()
        kapasitas = self.ent_kapasitas.get().strip()
        fasilitas = self.ent_fasilitas.get().strip()

        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor()
            cursor.execute(
                "UPDATE studio SET nama_studio = %s, kapasitas = %s, harga_per_jam = %s, fasilitas = %s WHERE id_studio = %s",
                (nama, int(kapasitas), float(harga), fasilitas, id_studio)
            )
            db.commit()
            messagebox.showinfo("Berhasil", "Studio berhasil diperbarui.")
            self.muat_data_inventaris()
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def hapus_studio(self):
        sel = self.tabel_inv.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih studio yang akan dihapus!")
            return
        id_studio = self.tabel_inv.item(sel[0]).get("values")[0]
        if not messagebox.askyesno("Konfirmasi", "Yakin ingin menghapus studio ini?"):
            return
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor()
            cursor.execute("DELETE FROM studio WHERE id_studio = %s", (id_studio,))
            db.commit()
            messagebox.showinfo("Berhasil", "Studio dihapus.")
            self.muat_data_inventaris()
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    # ================= TAB 2B: MANAJEMEN ALAT (CRUD) =================
    def setup_tab_alat(self):
        self._alat_cache = {}  # id_alat -> baris DB, supaya form terisi tanpa parsing teks tabel

        self.tab_alat.grid_columnconfigure(0, weight=3)
        self.tab_alat.grid_columnconfigure(1, weight=5)
        self.tab_alat.grid_rowconfigure(0, weight=1)

        f_kiri = ctk.CTkFrame(self.tab_alat, fg_color="#222222", corner_radius=10)
        f_kiri.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(f_kiri, text="Form Kelola Alat", font=("Segoe UI", 16, "bold")).pack(pady=(15, 10))

        self.ent_alat_nama = ctk.CTkEntry(f_kiri, placeholder_text="Nama Alat", height=35)
        self.ent_alat_nama.pack(fill="x", padx=15, pady=6)
        self.ent_alat_harga = ctk.CTkEntry(f_kiri, placeholder_text="Harga Sewa per Hari (contoh: 25.000)", height=35)
        self.ent_alat_harga.pack(fill="x", padx=15, pady=6)
        self.ent_alat_stok = ctk.CTkEntry(f_kiri, placeholder_text="Stok (bilangan bulat, minimal 0)", height=35)
        self.ent_alat_stok.pack(fill="x", padx=15, pady=6)
        self.ent_alat_deskripsi = ctk.CTkEntry(f_kiri, placeholder_text="Deskripsi (opsional)", height=35)
        self.ent_alat_deskripsi.pack(fill="x", padx=15, pady=6)

        btn_f = ctk.CTkFrame(f_kiri, fg_color="transparent")
        btn_f.pack(fill="x", padx=15, pady=(10, 4))
        ctk.CTkButton(btn_f, text="Tambah", fg_color="#2ecc71", width=90, command=self.tambah_alat).pack(side="left", expand=True)
        ctk.CTkButton(btn_f, text="Ubah", fg_color="#f1c40f", text_color="#000", width=90, command=self.ubah_alat).pack(side="left", expand=True)
        ctk.CTkButton(btn_f, text="Hapus", fg_color="#e74c3c", width=90, command=self.hapus_alat).pack(side="left", expand=True)

        ctk.CTkButton(
            f_kiri, text="Bersihkan Form", fg_color="#555555", hover_color="#666666",
            height=30, command=self.bersihkan_form_alat,
        ).pack(fill="x", padx=15, pady=(6, 10))

        ctk.CTkLabel(
            f_kiri,
            text="Klik baris pada tabel untuk mengisi form,\nlalu tekan Ubah atau Hapus.\nAlat yang pernah disewa tidak bisa dihapus\n(set stok 0 sebagai gantinya).",
            font=("Segoe UI", 11),
            text_color="#9aa0a6",
            justify="left",
        ).pack(padx=15, pady=(0, 10), anchor="w")

        f_kanan = ctk.CTkFrame(self.tab_alat, fg_color="transparent")
        f_kanan.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        table_frame = ctk.CTkFrame(f_kanan, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=5)

        kolom_alat = ("id_alat", "nama", "harga", "stok", "deskripsi")
        self.tabel_alat = ttk.Treeview(table_frame, columns=kolom_alat, show="headings", height=15)
        self.tabel_alat.heading("id_alat", text="ID")
        self.tabel_alat.heading("nama", text="Nama Alat")
        self.tabel_alat.heading("harga", text="Harga / Hari")
        self.tabel_alat.heading("stok", text="Stok")
        self.tabel_alat.heading("deskripsi", text="Deskripsi")

        self.tabel_alat.column("id_alat", width=40, anchor="center")
        self.tabel_alat.column("nama", width=180, anchor="w")
        self.tabel_alat.column("harga", width=100, anchor="center")
        self.tabel_alat.column("stok", width=60, anchor="center")
        self.tabel_alat.column("deskripsi", width=220, anchor="w")

        self.tabel_alat.tag_configure("habis", foreground="#ff8a65")  # stok 0 dibuat oranye
        self.tabel_alat.bind("<<TreeviewSelect>>", self.pilih_alat)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabel_alat.yview)
        self.tabel_alat.configure(yscrollcommand=scroll.set)
        self.tabel_alat.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.muat_data_alat()

    def muat_data_alat(self):
        for r in self.tabel_alat.get_children():
            self.tabel_alat.delete(r)
        self._alat_cache = {}
        db = None
        cursor = None
        try:
            db = _koneksi()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alat ORDER BY id_alat")
            for a in cursor.fetchall():
                id_alat = a.get("id_alat")
                self._alat_cache[id_alat] = a
                stok = int(a.get("stok") or 0)
                self.tabel_alat.insert(
                    "",
                    "end",
                    iid=str(id_alat),
                    values=(
                        id_alat,
                        a.get("nama_alat"),
                        format_rupiah(a.get("harga_per_hari")),
                        stok,
                        a.get("deskripsi") or "-",
                    ),
                    tags=("habis",) if stok == 0 else (),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data alat:\n{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def bersihkan_form_alat(self):
        for ent in (self.ent_alat_nama, self.ent_alat_harga, self.ent_alat_stok, self.ent_alat_deskripsi):
            ent.delete(0, "end")
        self.tabel_alat.selection_remove(self.tabel_alat.selection())

    def pilih_alat(self, event=None):
        sel = self.tabel_alat.selection()
        if not sel:
            return
        a = self._alat_cache.get(int(sel[0]))
        if not a:
            return
        harga = float(a.get("harga_per_hari") or 0)
        isian = (
            (self.ent_alat_nama, str(a.get("nama_alat") or "")),
            (self.ent_alat_harga, str(int(harga)) if harga == int(harga) else str(harga)),
            (self.ent_alat_stok, str(int(a.get("stok") or 0))),
            (self.ent_alat_deskripsi, str(a.get("deskripsi") or "")),
        )
        for ent, nilai in isian:
            ent.delete(0, "end")
            ent.insert(0, nilai)

    def _nama_alat_sudah_ada(self, cursor, nama, kecuali_id=None):
        cursor.execute(
            "SELECT id_alat FROM alat WHERE LOWER(nama_alat) = LOWER(%s)", (nama,)
        )
        return any(r[0] != kecuali_id for r in cursor.fetchall())

    def tambah_alat(self):
        ok, hasil = validasi_alat(
            self.ent_alat_nama.get(), self.ent_alat_harga.get(), self.ent_alat_stok.get()
        )
        if not ok:
            messagebox.showwarning("Peringatan", hasil)
            return
        nama, harga, stok = hasil
        deskripsi = self.ent_alat_deskripsi.get().strip() or None

        db = None
        cursor = None
        try:
            db = _koneksi()
            cursor = db.cursor()
            if self._nama_alat_sudah_ada(cursor, nama):
                messagebox.showwarning("Peringatan", f"Alat '{nama}' sudah ada di daftar!")
                return
            cursor.execute(
                "INSERT INTO alat (nama_alat, harga_per_hari, stok, deskripsi) VALUES (%s, %s, %s, %s)",
                (nama, harga, stok, deskripsi),
            )
            db.commit()
            messagebox.showinfo("Berhasil", f"Alat '{nama}' berhasil ditambahkan.")
            self.bersihkan_form_alat()
            self.muat_data_alat()
        except Exception as e:
            if db: db.rollback()
            messagebox.showerror("Error", f"Gagal menambah alat:\n{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def ubah_alat(self):
        sel = self.tabel_alat.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih alat pada tabel yang akan diubah!")
            return
        id_alat = int(sel[0])
        ok, hasil = validasi_alat(
            self.ent_alat_nama.get(), self.ent_alat_harga.get(), self.ent_alat_stok.get()
        )
        if not ok:
            messagebox.showwarning("Peringatan", hasil)
            return
        nama, harga, stok = hasil
        deskripsi = self.ent_alat_deskripsi.get().strip() or None

        db = None
        cursor = None
        try:
            db = _koneksi()
            cursor = db.cursor()
            if self._nama_alat_sudah_ada(cursor, nama, kecuali_id=id_alat):
                messagebox.showwarning("Peringatan", f"Nama '{nama}' sudah dipakai alat lain!")
                return
            cursor.execute(
                "UPDATE alat SET nama_alat = %s, harga_per_hari = %s, stok = %s, deskripsi = %s WHERE id_alat = %s",
                (nama, harga, stok, deskripsi, id_alat),
            )
            db.commit()
            messagebox.showinfo("Berhasil", f"Alat '{nama}' berhasil diperbarui.")
            self.muat_data_alat()
        except Exception as e:
            if db: db.rollback()
            messagebox.showerror("Error", f"Gagal mengubah alat:\n{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def hapus_alat(self):
        sel = self.tabel_alat.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih alat pada tabel yang akan dihapus!")
            return
        id_alat = int(sel[0])
        nama = (self._alat_cache.get(id_alat) or {}).get("nama_alat", f"ID {id_alat}")

        db = None
        cursor = None
        try:
            db = _koneksi()
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM detail_transaksi WHERE id_alat = %s", (id_alat,))
            if cursor.fetchone()[0] > 0:
                messagebox.showwarning(
                    "Tidak Bisa Dihapus",
                    f"Alat '{nama}' pernah dipakai dalam transaksi sehingga tidak bisa dihapus.\n"
                    "Ubah stok menjadi 0 bila alat tidak lagi disewakan.",
                )
                return
            if not messagebox.askyesno("Konfirmasi", f"Yakin ingin menghapus alat '{nama}'?"):
                return
            cursor.execute("DELETE FROM alat WHERE id_alat = %s", (id_alat,))
            db.commit()
            messagebox.showinfo("Berhasil", f"Alat '{nama}' dihapus.")
            self.bersihkan_form_alat()
            self.muat_data_alat()
        except Exception as e:
            if db: db.rollback()
            messagebox.showerror("Error", f"Gagal menghapus alat:\n{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    # ================= TAB 3: PENGEMBALIAN & DENDA =================
    def setup_tab_pengembalian(self):
        self.tab_pengembalian.grid_columnconfigure(0, weight=1)
        self.tab_pengembalian.grid_rowconfigure(0, weight=1)

        f_utama = ctk.CTkFrame(self.tab_pengembalian, fg_color="transparent")
        f_utama.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(f_utama, text="Batas Waktu, Validasi & Denda Keterlambatan", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(5, 10))

        table_frame = ctk.CTkFrame(f_utama, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=5)

        kolom_k = ("id_trx", "penyewa", "tgl_sewa", "jatuh_tempo", "status_terlambat")
        self.tabel_kembali = ttk.Treeview(table_frame, columns=kolom_k, show="headings", height=13)
        self.tabel_kembali.heading("id_trx", text="ID Trx")
        self.tabel_kembali.heading("penyewa", text="Penyewa")
        self.tabel_kembali.heading("tgl_sewa", text="Tanggal Sewa")
        self.tabel_kembali.heading("jatuh_tempo", text="Rencana Kembali")
        self.tabel_kembali.heading("status_terlambat", text="Keterangan")

        self.tabel_kembali.column("id_trx", width=60, anchor="center")
        self.tabel_kembali.column("penyewa", width=180, anchor="w")
        self.tabel_kembali.column("tgl_sewa", width=120, anchor="center")
        self.tabel_kembali.column("jatuh_tempo", width=120, anchor="center")
        self.tabel_kembali.column("status_terlambat", width=200, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabel_kembali.yview)
        self.tabel_kembali.configure(yscrollcommand=scroll.set)
        self.tabel_kembali.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        ctk.CTkButton(f_utama, text="Proses Pengembalian & Kalkulasi Denda", fg_color="#3498db", height=40, command=self.aksi_validasi).pack(fill="x", pady=10)
        self.muat_data_pengembalian()

    def muat_data_pengembalian(self):
        for r in self.tabel_kembali.get_children():
            self.tabel_kembali.delete(r)
        db = None
        cursor = None
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT t.id_transaksi, t.tgl_sewa, t.tgl_kembali_rencana, u.username, u.nama_lengkap
                FROM transaksi t
                JOIN users u ON t.id_user = u.id_user
                WHERE t.status_transaksi = 'Lunas'
                """
            )
            for t in cursor.fetchall():
                self.tabel_kembali.insert(
                    "",
                    "end",
                    values=(
                        t.get("id_transaksi"),
                        f"{t.get('username', '-')} ({t.get('nama_lengkap', '-')})",
                        t.get("tgl_sewa", "-"),
                        t.get("tgl_kembali_rencana", "-"),
                        "Aktif / Berjalan",
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def aksi_validasi(self):
        sel = self.tabel_kembali.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih transaksi pada tabel!")
            return
        id_trx = self.tabel_kembali.item(sel[0]).get("values")[0]
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor()
            cursor.execute("UPDATE transaksi SET status_transaksi = 'Selesai' WHERE id_transaksi = %s", (id_trx,))
            db.commit()
            messagebox.showinfo("Berhasil", f"Pengembalian Transaksi ID {id_trx} divalidasi.")
            self.muat_data_pengembalian()
            self.muat_data_riwayat()
        except Exception as e:
            if db: db.rollback()
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    # ================= TAB 4: RIWAYAT TRANSAKSI =================
    def setup_tab_riwayat(self):
        self.tab_riwayat.grid_columnconfigure(0, weight=1)
        self.tab_riwayat.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.tab_riwayat, text="Riwayat Transaksi Penyewaan & Denda", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        table_frame = ctk.CTkFrame(self.tab_riwayat, fg_color="transparent")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        kolom = ("id_trx", "penyewa", "total", "denda", "status", "tgl_sewa")
        self.tabel_riwayat = ttk.Treeview(table_frame, columns=kolom, show="headings", height=15)
        judul = {
            "id_trx": "ID Trx", "penyewa": "Penyewa", "total": "Total Biaya",
            "denda": "Denda", "status": "Status", "tgl_sewa": "Tanggal Sewa"
        }
        for k, v in judul.items():
            self.tabel_riwayat.heading(k, text=v)

        self.tabel_riwayat.column("id_trx", width=60, anchor="center")
        self.tabel_riwayat.column("penyewa", width=140, anchor="w")
        self.tabel_riwayat.column("total", width=120, anchor="center")
        self.tabel_riwayat.column("denda", width=110, anchor="center")
        self.tabel_riwayat.column("status", width=110, anchor="center")
        self.tabel_riwayat.column("tgl_sewa", width=110, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabel_riwayat.yview)
        self.tabel_riwayat.configure(yscrollcommand=scroll.set)
        self.tabel_riwayat.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        tombol = ctk.CTkFrame(self.tab_riwayat, fg_color="transparent")
        tombol.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkButton(tombol, text="Muat Ulang Riwayat", fg_color="#3498db", command=self.muat_data_riwayat).pack(side="left")

        self.muat_data_riwayat()

    def muat_data_riwayat(self):
        for r in self.tabel_riwayat.get_children():
            self.tabel_riwayat.delete(r)
        db = None
        cursor = None
        try:
            db = mysql.connector.connect(host="localhost", user="root", password="", database="artstudio_rent")
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT t.id_transaksi, t.total_biaya, t.denda, t.status_transaksi, t.tgl_sewa, u.username, u.nama_lengkap
                FROM transaksi t
                JOIN users u ON t.id_user = u.id_user
                ORDER BY t.id_transaksi DESC
                """
            )
            for t in cursor.fetchall():
                self.tabel_riwayat.insert(
                    "",
                    "end",
                    values=(
                        t.get("id_transaksi"),
                        f"{t.get('username', '-')} ({t.get('nama_lengkap', '-')})",
                        f"Rp {float(t.get('total_biaya') or 0):,.0f}",
                        f"Rp {float(t.get('denda') or 0):,.0f}",
                        t.get("status_transaksi", "-"),
                        t.get("tgl_sewa", "-"),
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def aksi_logout(self):
        if messagebox.askyesno("Konfirmasi", "Apakah Anda ingin keluar ke halaman login?"):
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
        OperatorGUI({"nama_lengkap": "Operator Studio", "role": "operator"}).mainloop()