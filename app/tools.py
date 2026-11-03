"""
Modul Tools — fungsi-fungsi "aksi" yang dipanggil router ketika intent
BUKAN pertanyaan informasi/kebijakan, melainkan permintaan spesifik
yang butuh pengecekan data langsung (bukan retrieval semantik).

Pola ini mengikuti konsep Tool Integration di Sesi 12.3.
"""
import os
import pandas as pd

MOCK_TICKETS_PATH = "data/mock_tickets.csv"

def get_ticket_status(ticket_id: str) -> str:
    """
    Mencari status tiket berdasarkan ticket_id pada data mock_tickets.csv.

    Langkah implementasi:
      1. Muat mock_tickets.csv menggunakan pandas.
      2. Cari baris dengan ticket_id yang cocok (aman terhadap case-sensitivity).
      3. Jika ditemukan, susun string jawaban (subject, status, last_update).
      4. Jika tidak ditemukan, kembalikan pesan bahwa tiket tidak ditemukan.
    """
    # Tentukan path file yang aman (mendukung folder data/ atau direktori lokal)
    file_path = MOCK_TICKETS_PATH
    if not os.path.exists(file_path):
        file_path = "data/mock_tickets.csv"

    if not os.path.exists(file_path):
        return f"Maaf, data tiket (mock_tickets.csv) tidak ditemukan di sistem."

    try:
        df = pd.read_csv(file_path)
        
        # Pastikan kolom 'ticket_id' ada di dataframe
        if 'ticket_id' not in df.columns:
            return "Maaf, struktur data tiket tidak valid."

        # Normalisasi input ticket_id dan kolom untuk pencarian yang lebih fleksibel
        target_id = str(ticket_id).strip()
        
        # Cari baris yang cocok (pencarian exact match, bisa disesuaikan dengan .str.lower() jika perlu)
        matched_row = df[df['ticket_id'].astype(str).str.strip().str.lower() == target_id.lower()]

        if matched_row.empty:
            return f"Maaf, tiket dengan ID '{ticket_id}' tidak ditemukan di dalam sistem. Mohon periksa kembali nomor ID tiket Anda."

        # Ambil data baris pertama yang cocok
        ticket = matched_row.iloc[0]
        
        employee = ticket.get('employee_name', 'Karyawan')
        subject = ticket.get('subject', 'Tidak ada subjek')
        status = ticket.get('status', 'Tidak diketahui')
        last_update = ticket.get('last_update', '-')
        category = ticket.get('category', 'Umum')

        # Susun string jawaban yang informatif
        response_msg = (
            f"Informasi Status Tiket ({target_id}):\n"
            f"- Pemohon: {employee}\n"
            f"- Kategori: {category}\n"
            f"- Subjek: {subject}\n"
            f"- Status Saat Ini: {status}\n"
            f"- Pembaruan Terakhir: {last_update}"
        )
        return response_msg

    except Exception as e:
        # Menangani error tak terduga agar aplikasi tidak crash
        return f"Terjadi kesalahan saat memproses pencarian tiket: {str(e)}"