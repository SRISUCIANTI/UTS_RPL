import os
import sys
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
  sys.path.insert(0, project_root)
if current_dir not in sys.path:
  sys.path.append(current_dir)

from controllers.laporan_controller import LaporanController
from models.laporan_model import LaporanModel

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

STATUS_FILTER = ["Semua", "Pending", "Lunas", "Selesai", "Batal", "Tuntas"]
JENIS_REKAP = "Rekapitulasi Umum"
JENIS_RIWAYAT = "Riwayat Transaksi (sesuai filter)"
JENIS_BULANAN = "Pendapatan Bulanan (sesuai filter bulan)"
JENIS_SEMUA = "Semua Laporan"


def format_rupiah(nilai):
  """Rp 25.000 (tanpa desimal bila bulat) / Rp 25.000,50."""
  nilai = float(nilai or 0)
  if nilai == int(nilai):
    teks = f"{int(nilai):,}".replace(",", ".")
  else:
    teks = f"{nilai:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
  return f"Rp {teks}"


def _bulan_dari(tgl):
  """date / 'YYYY-MM-DD' -> 'YYYY-MM'."""
  return tgl.strftime("%Y-%m") if hasattr(tgl, "strftime") else str(tgl or "")[:7]


class OwnerGUI(ctk.CTk):

  def __init__(self, user):
    super().__init__()

    self.user = user or {}
    nama_user = (
        self.user.get("nama_lengkap")
        or self.user.get("username")
        or "Owner"
    )

    self.title(
        f"ArtStudio-Rent — Dashboard Owner / Pemilik Studio"
        f" ({str(nama_user).title()})"
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
        text=f"Owner Dashboard — {str(nama_user).title()}",
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

    self.tab_laporan = self.tab_view.add("Rekapitulasi & Laporan Pendapatan")
    self.tab_analisis = self.tab_view.add("Analisis Utilisasi Alat & Studio")

    self.setup_tab_laporan()
    self.setup_tab_analisis()

  # ==================================================
  # TAB LAPORAN PENDAPATAN
  # ==================================================
  def setup_tab_laporan(self):
    self.tab_laporan.grid_columnconfigure(0, weight=1)
    self.tab_laporan.grid_rowconfigure(2, weight=1)

    top_f = ctk.CTkFrame(self.tab_laporan, fg_color="#222222", corner_radius=10)
    top_f.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

    ctk.CTkLabel(
        top_f, text="Laporan Pendapatan", font=("Segoe UI", 15, "bold")
    ).pack(side="left", padx=20, pady=15)

    self.lbl_total = ctk.CTkLabel(
        top_f,
        text="Total Pendapatan: Rp 0",
        font=("Segoe UI", 15, "bold"),
        text_color="#2ecc71",
    )
    self.lbl_total.pack(side="right", padx=20, pady=15)

    # ---- baris filter ----
    filter_f = ctk.CTkFrame(self.tab_laporan, fg_color="transparent")
    filter_f.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))

    ctk.CTkLabel(filter_f, text="Status:").pack(side="left", padx=(5, 4))
    self.opt_status = ctk.CTkOptionMenu(
        filter_f, values=STATUS_FILTER, width=120
    )
    self.opt_status.set("Semua")
    self.opt_status.pack(side="left", padx=(0, 14))

    ctk.CTkLabel(filter_f, text="Bulan (YYYY-MM):").pack(side="left", padx=(0, 4))
    self.ent_bulan = ctk.CTkEntry(
        filter_f, width=110, placeholder_text="kosong = semua"
    )
    self.ent_bulan.pack(side="left", padx=(0, 14))

    ctk.CTkButton(
        filter_f, text="Terapkan Filter", width=130,
        command=self.muat_data_owner,
    ).pack(side="left", padx=(0, 6))
    ctk.CTkButton(
        filter_f, text="Reset", width=80, fg_color="#555555",
        command=self.reset_filter,
    ).pack(side="left")

    # ---- tabel ----
    table_frame = ctk.CTkFrame(self.tab_laporan, fg_color="transparent")
    table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

    kolom = ("id_trx", "tanggal", "penyewa", "total", "denda", "status", "kembali")

    self.tabel_laporan = ttk.Treeview(
        table_frame, columns=kolom, show="headings", height=12
    )

    for k, judul, lebar, rata in (
        ("id_trx", "ID Transaksi", 90, "center"),
        ("tanggal", "Tanggal Sewa", 110, "center"),
        ("penyewa", "Nama Penyewa", 200, "w"),
        ("total", "Total Biaya", 120, "center"),
        ("denda", "Denda", 100, "center"),
        ("status", "Status Transaksi", 120, "center"),
        ("kembali", "Kembali Aktual", 120, "center"),
    ):
      self.tabel_laporan.heading(k, text=judul)
      self.tabel_laporan.column(k, width=lebar, anchor=rata)

    scroll = ttk.Scrollbar(
        table_frame, orient="vertical", command=self.tabel_laporan.yview
    )
    self.tabel_laporan.configure(yscrollcommand=scroll.set)

    self.tabel_laporan.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    self.lbl_info_laporan = ctk.CTkLabel(
        self.tab_laporan, text="", font=("Segoe UI", 11), text_color="#9aa0a6"
    )
    self.lbl_info_laporan.grid(row=3, column=0, sticky="w", padx=15)

    # ---- baris export ----
    btn_f = ctk.CTkFrame(self.tab_laporan, fg_color="transparent")
    btn_f.grid(row=4, column=0, sticky="ew", padx=10, pady=10)

    self.opt_jenis = ctk.CTkOptionMenu(
        btn_f,
        values=[JENIS_REKAP, JENIS_RIWAYAT, JENIS_BULANAN, JENIS_SEMUA],
        width=330, height=42,
    )
    self.opt_jenis.set(JENIS_SEMUA)
    self.opt_jenis.pack(side="left", padx=(0, 10))

    ctk.CTkButton(
        btn_f,
        text="Cetak / Export Laporan ke TXT",
        fg_color="#2980b9",
        height=42,
        command=self.aksi_export,
    ).pack(side="left", expand=True, fill="x", padx=(0, 10))

    ctk.CTkButton(
        btn_f,
        text="Segarkan Data Laporan",
        fg_color="#3498db",
        height=42,
        command=self.muat_data_owner,
    ).pack(side="right", expand=True, fill="x", padx=(10, 0))

    self.muat_data_owner()

  # ==================================================
  # TAB ANALISIS
  # ==================================================
  def setup_tab_analisis(self):
    self.tab_analisis.grid_columnconfigure(0, weight=1)
    self.tab_analisis.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(
        self.tab_analisis,
        text="Statistik & Analisis Utilisasi Alat & Studio",
        font=("Segoe UI", 15, "bold"),
    ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

    table_frame = ctk.CTkFrame(self.tab_analisis, fg_color="transparent")
    table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

    kolom = ("nama_ruangan", "kategori", "total_disewa", "pendapatan_alat")

    self.tabel_analisis = ttk.Treeview(
        table_frame, columns=kolom, show="headings", height=13
    )

    self.tabel_analisis.heading("nama_ruangan", text="Nama Alat / Studio")
    self.tabel_analisis.heading("kategori", text="Kategori")
    self.tabel_analisis.heading("total_disewa", text="Frekuensi Disewa")
    self.tabel_analisis.heading("pendapatan_alat", text="Kontribusi Pendapatan")

    self.tabel_analisis.column("nama_ruangan", width=220, anchor="w")
    self.tabel_analisis.column("kategori", width=150, anchor="w")
    self.tabel_analisis.column("total_disewa", width=140, anchor="center")
    self.tabel_analisis.column("pendapatan_alat", width=180, anchor="center")

    scroll = ttk.Scrollbar(
        table_frame, orient="vertical", command=self.tabel_analisis.yview
    )
    self.tabel_analisis.configure(yscrollcommand=scroll.set)

    self.tabel_analisis.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    self.muat_data_analisis()

  # ==================================================
  # MEMUAT LAPORAN DARI DATABASE
  # ==================================================
  def reset_filter(self):
    self.opt_status.set("Semua")
    self.ent_bulan.delete(0, "end")
    self.muat_data_owner()

  def _filter_laporan(self):
    """(status|None, bulan|None) dari form; None bila bulan tidak valid."""
    status = self.opt_status.get()
    status = None if status == "Semua" else status
    bulan = self.ent_bulan.get().strip() or None
    if bulan:
      try:
        datetime.strptime(bulan, "%Y-%m")
      except ValueError:
        messagebox.showwarning(
            "Filter Bulan", "Format bulan harus YYYY-MM (contoh: 2026-11)."
        )
        return None
    return status, bulan

  def muat_data_owner(self):
    for r in self.tabel_laporan.get_children():
      self.tabel_laporan.delete(r)

    filt = self._filter_laporan()
    if filt is None:
      return
    status, bulan = filt

    rows = LaporanModel.riwayat(status)
    if bulan:
      rows = [r for r in rows if _bulan_dari(r.get("tgl_sewa")) == bulan]

    for t in rows:
      self.tabel_laporan.insert(
          "",
          "end",
          values=(
              t.get("id_transaksi"),
              t.get("tgl_sewa") or "-",
              f"{t.get('nama_lengkap') or '-'} ({t.get('username') or '-'})",
              format_rupiah(t.get("total_biaya")),
              format_rupiah(t.get("denda")),
              t.get("status_transaksi") or "-",
              t.get("tgl_kembali_aktual") or "-",
          ),
      )

    # Pendapatan = sewa (Lunas+Selesai+Tuntas) + denda yang sudah dibayar (Tuntas)
    rekap = LaporanModel.rekapUmum()
    if rekap is None:
      self.lbl_total.configure(text="Total Pendapatan: (gagal memuat)")
    else:
      total = rekap["total_sewa"] + rekap["total_denda"]
      self.lbl_total.configure(
          text=f"Total Pendapatan (sewa + denda terbayar): {format_rupiah(total)}"
      )

    info = f"Menampilkan {len(rows)} transaksi"
    if status:
      info += f" | status {status}"
    if bulan:
      bln = LaporanModel.pendapatanBulanan(bulan)
      pendapatan = sum(b["sewa"] + b["denda"] for b in bln)
      info += f" | bulan {bulan} | pendapatan bulan ini {format_rupiah(pendapatan)}"
    if rekap is not None:
      info += (
          f" | Pending {rekap['pending']} dan Batal {rekap['batal']}"
          " tidak dihitung sebagai pendapatan"
      )
    self.lbl_info_laporan.configure(text=info)

  # ==================================================
  # ANALISIS UTILISASI
  # ==================================================
  def muat_data_analisis(self):
    for r in self.tabel_analisis.get_children():
      self.tabel_analisis.delete(r)

    rows = LaporanModel.utilisasi()
    if rows is None:
      messagebox.showerror(
          "Database Error", "Gagal memuat analisis utilisasi dari database."
      )
      return
    if not rows:
      self.tabel_analisis.insert(
          "", "end",
          values=("Belum ada transaksi berbayar", "-", "-", "-"),
      )
      return
    for r in rows:
      self.tabel_analisis.insert(
          "",
          "end",
          values=(
              r["nama"],
              r["kategori"],
              f"{r['frekuensi']} Kali",
              format_rupiah(r["pendapatan"]),
          ),
      )

  # ==================================================
  # EXPORT LAPORAN (TXT)
  # ==================================================
  def aksi_export(self):
    filt = self._filter_laporan()
    if filt is None:
      return
    status, bulan = filt
    jenis = self.opt_jenis.get()

    bagian = []  # (kode, baris)
    if jenis in (JENIS_REKAP, JENIS_SEMUA):
      bagian.append(("rekap", LaporanController.rekap_umum()))
    if jenis in (JENIS_RIWAYAT, JENIS_SEMUA):
      bagian.append(("riwayat", LaporanController.riwayat_transaksi(status, bulan)))
    if jenis in (JENIS_BULANAN, JENIS_SEMUA):
      bagian.append(("bulanan", LaporanController.pendapatan_bulanan(bulan)))

    if any(baris is None for _, baris in bagian):
      messagebox.showerror(
          "Export Gagal",
          "Laporan tidak bisa disusun (database tidak terjangkau atau filter tidak valid).",
      )
      return

    gabung = []
    for _, baris in bagian:
      gabung += baris + [""]
    kode = bagian[0][0] if len(bagian) == 1 else "lengkap"

    path = filedialog.asksaveasfilename(
        title="Simpan Laporan",
        defaultextension=".txt",
        initialfile=f"laporan_owner_{kode}_{datetime.now():%Y%m%d_%H%M%S}.txt",
        filetypes=[("Teks", "*.txt"), ("Semua File", "*.*")],
    )
    if not path:
      return

    hasil = LaporanController.simpan_txt(kode, gabung, path)
    if hasil:
      messagebox.showinfo("Berhasil", f"Laporan tersimpan di:\n{hasil}")
    else:
      messagebox.showerror("Gagal", "Laporan gagal disimpan. Periksa lokasi file.")

  # ==================================================
  # LOGOUT
  # ==================================================
  def aksi_logout(self):
    if messagebox.askyesno(
        "Konfirmasi", "Apakah Anda ingin keluar ke halaman login?"
    ):
      self.destroy()
      from login_gui import LoginGUI

      LoginGUI().mainloop()


# ======================================================
# MENJALANKAN DASHBOARD
# ======================================================
if __name__ == "__main__":
  if len(sys.argv) >= 4:
    user = {
        "id_user": int(sys.argv[1]),
        "nama_lengkap": sys.argv[2],
        "role": sys.argv[3],
    }
    OwnerGUI(user).mainloop()
  else:
    print("Silakan jalankan dashboard melalui login_gui.py.")