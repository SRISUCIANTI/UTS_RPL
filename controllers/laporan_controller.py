from datetime import datetime
from models.laporan_model import LaporanModel

STATUS_VALID = ('Pending', 'Lunas', 'Selesai', 'Batal', 'Tuntas')


class LaporanController:
    @staticmethod
    def _rp(nilai):
        return f"Rp{float(nilai or 0):,.0f}"

    @staticmethod
    def _tgl(nilai):
        return str(nilai) if nilai else '-'

    @staticmethod
    def rekap_umum():
        """Teks laporan rekapitulasi umum (list baris, siap tampil/cetak)."""
        data = LaporanModel.rekapUmum()
        if data is None:
            return None
        total = data['total_sewa'] + data['total_denda']
        return [
            "REKAPITULASI LAPORAN ARTSTUDIO-RENT",
            f"Transaksi dihitung (Lunas+Selesai+Tuntas) : {data['jml_transaksi']}",
            f"Total Pendapatan Sewa              : {LaporanController._rp(data['total_sewa'])}",
            f"Total Denda Terbayar (Tuntas)      : {LaporanController._rp(data['total_denda'])}",
            f"TOTAL PENDAPATAN                   : {LaporanController._rp(total)}",
            f"Info: Pending={data['pending']} (belum dibayar, tidak dihitung) | "
            f"Batal={data['batal']} (dikecualikan)",
        ]

    @staticmethod
    def riwayat_transaksi(status=None):
        """Teks laporan riwayat. status None/'Semua' = semua status."""
        if status and str(status).strip().capitalize() not in STATUS_VALID:
            return None
        data = LaporanModel.riwayat(
            str(status).strip().capitalize() if status else None
        )
        judul = f"RIWAYAT TRANSAKSI{(f' - {str(status).strip().capitalize()}') if status else ''}"
        baris = [judul, f"Jumlah: {len(data)} transaksi"]
        for t in data:
            baris.append(
                f"ID {t['id_transaksi']} | {LaporanController._tgl(t['tgl_sewa'])} -> "
                f"{LaporanController._tgl(t['tgl_kembali_rencana'])} "
                f"(aktual: {LaporanController._tgl(t['tgl_kembali_aktual'])}) | "
                f"{t['username']} ({t['nama_lengkap']}) | "
                f"Sewa {LaporanController._rp(t['total_biaya'])} + "
                f"Denda {LaporanController._rp(t['denda'])} | {t['status_transaksi']}"
            )
        if not data:
            baris.append("Tidak ada data.")
        return baris

    @staticmethod
    def pendapatan_bulanan(bulan=None):
        """Teks laporan pendapatan bulanan. bulan 'YYYY-MM' atau None = semua."""
        if bulan:
            bulan = str(bulan).strip()
            try:
                datetime.strptime(bulan, "%Y-%m")
            except ValueError:
                return None
        data = LaporanModel.pendapatanBulanan(bulan)
        judul = f"PENDAPATAN BULANAN{(f' - {bulan}') if bulan else ''}"
        baris = [judul]
        tot_trx = tot_sewa = tot_denda = 0
        for r in data:
            total = r['sewa'] + r['denda']
            baris.append(
                f"{r['bulan']} | {r['jml']} transaksi | "
                f"Sewa {LaporanController._rp(r['sewa'])} + "
                f"Denda {LaporanController._rp(r['denda'])} = "
                f"{LaporanController._rp(total)}"
            )
            tot_trx += r['jml']
            tot_sewa += r['sewa']
            tot_denda += r['denda']
        if not data:
            baris.append("Tidak ada data pada periode ini.")
        else:
            baris.append(
                f"TOTAL | {tot_trx} transaksi | "
                f"{LaporanController._rp(tot_sewa + tot_denda)}"
            )
        return baris

    @staticmethod
    def simpan_txt(nama_jenis, baris):
        """Simpan baris laporan ke file TXT. Mengembalikan nama file / None."""
        try:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nama_file = f"laporan_owner_{nama_jenis}_{stamp}.txt"
            with open(nama_file, "w", encoding="utf-8") as f:
                f.write(f"ArtStudio-Rent | dicetak {datetime.now():%Y-%m-%d %H:%M}\n")
                f.write("=" * 60 + "\n")
                f.write("\n".join(baris) + "\n")
            return nama_file
        except OSError as e:
            print(f"[ERROR] Simpan Laporan: {e}")
            return None
