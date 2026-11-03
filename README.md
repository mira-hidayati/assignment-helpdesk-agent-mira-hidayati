MIRA HIDAYATI
CAI02
3-November-2026

# IT Helpdesk Assistant — Starter Repository
Starter repository untuk Assignment 4: End-to-End RAG & AI Agent Development.

## OBJECTIVE:
Membangun aplikasi AI Helpdesk internal yang dapat menangani pertanyaan repetitif dari karyawan, baik berupa kebijakan umum maupun pengecekan data tiket dalam satu sistem.  Seluruh sistem ini dibungkus menjadi backend API menggunakan FastAPI, dikelola dengan environment variables untuk API key, dan dijalankan dalam container Docker

## 2 JENIS PERMINTAAN USE YANG PERLU DITANGANI SISTEM
(1) Menjawab pertanyaan kebijakan berdasarkan knowledge base menggunakan RAG.  Contoh: "berapa jatah cuti saya?", "bagaimana cara reset password VPN?"
(2) Mengenali ketika permintaan user butuh pengecekan data spesifik (status tiket), lalu mengambil data tersebut menggunakan tool call, bukan retrieval semantik. Contoh: "apa status tiket TICKET-0042 saya?"

## BATASAN ATAU ASUMSI YANG DIGUNAKAN
{1) Pertanyaan terkait informasi/kebijakan ditangani dengan sistem RAG, menggunakan data dari knowledgebase "it_helpdesk_knowledge_base.csv".
(2) Pertanyaan terkait tiket ditangani dengan workflow routing sederhana/mini-agent, menggunakan dari data "mock_tickets.csv"


## DESAIN WORKFLOW aplikasi
Alur sistem: query masuk → intent detection → RAG atau tool call → response keluar.
Kriteria yang membedakan intent 'faq' dan 'ticket_status'

## Struktur Project

```
app/
├── main.py       # Entry point FastAPI, berisi endpoint /ask
├── router.py     # Intent detection + routing ke RAG atau tool call
├── rag.py        # Modul RAG: embedding, FAISS, semantic search, LLM answer
└── tools.py      # Modul tool call: pengecekan status tiket

data/
├── it_helpdesk_knowledge_base.csv   # Knowledge base untuk RAG
└── mock_tickets.csv                 # Data mock untuk tool call
```

## TODO Peserta

Seluruh bagian yang perlu diimplementasikan ditandai dengan komentar `# TODO`
atau `# 🔧 TODO` di dalam masing-masing file. Ikuti urutan berikut:

1. `app/rag.py` — implementasikan `build_index()`, `semantic_search()`, `answer_from_knowledge_base()`
2. `app/tools.py` — implementasikan `get_ticket_status()`
3. `app/router.py` — implementasikan `detect_intent()` dan `extract_ticket_id()`
4. `Dockerfile` — lengkapi konfigurasi container

## Komponen Utama dalam app/rag.py
# build_index(): 
Membaca file CSV it_helpdesk_knowledge_base.csv, menggabungkan kolom kategori, pertanyaan, dan jawaban menjadi format dokumen teks terstruktur, mengubahnya menjadi vektor menggunakan model text-embedding-004, dan menyimpannya ke dalam FAISS IndexFlatIP (dengan normalisasi L2 untuk cosine similarity).

# semantic_search(): 
Mengubah query pengguna menjadi embedding, menormalisasinya, lalu mencari top_k dokumen teratas yang paling mirip dari index FAISS.

# answer_from_knowledge_base(): 
Mengambil hasil pencarian FAISS sebagai konteks, membangun prompt dengan instruksi persona IT Helpdesk yang ketat agar menghindari halusinasi, lalu memanggil model gemini-1.5-flash untuk memberikan jawaban akhir kepada pengguna.


## Komponen Utama dalam app/router.py:
# detect_intent(): 
Memanfaatkan model gemini-1.5-flash dengan structured prompt untuk mengklasifikasikan apakah pengguna ingin bertanya tentang informasi/prosedur (faq) atau melacak tiket (ticket_status), lengkap dengan sistem fallback berbasis keyword untuk keamanan ekstra.

# extract_ticket_id(): 
Menggunakan ekspresi reguler (re) untuk mendeteksi pola ID tiket seperti TICKET-0001, ticket 0002, atau variasi spasi/tanda hubung, lalu menormalkannya secara otomatis.

# handle_query(): 
Berfungsi sebagai pengarah utama (router) yang memanggil fungsi RAG (answer_from_knowledge_base) atau Tool (get_ticket_status) berdasarkan hasil deteksi intent.

## Menjalankan Secara Lokal (tanpa Docker)

```bash
pip install -r requirements.txt
cp .env.example .env   # lalu isi GEMINI_API_KEY di dalam .env
uvicorn app.main:app --reload
```
http://127.0.0.1:8000/docs

## Menjalankan dengan Docker

```bash
docker build --no-cache -t it-helpdesk-app .
docker run -d -p 8000:8000 --env-file .env it-helpdesk-app
```

## Menguji Endpoint

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "berapa jatah cuti tahunan saya?"}'
```

## Pengujian 5 Skenario:
## 1. Skenario 1 (RAG - Kebijakan Cuti):

JSON
{
  "query": "Berapa jatah cuti tahunan untuk karyawan tetap?"
}

# 1st Test Response:
{
  "status": "success",
  "intent": "faq",
  "data": "Halo! \n\nBerdasarkan ketentuan yang berlaku, jatah cuti tahunan untuk karyawan tetap adalah sebagai berikut:\n\n* **Jumlah Jatah Cuti:** 12 hari per tahun.\n* **Syarat Pengambilan:** Dapat mulai diambil setelah masa kerja minimal **3 bulan**.\n\nJika Anda membutuhkan informasi lebih lanjut mengenai pengajuan cuti, silakan tanyakan kembali. Semoga membantu!"
}

# 2nd Test Response:
{
  "status": "success",
  "intent": "faq",
  "data": "Halo! \n\nBerdasarkan informasi yang tersedia, jatah cuti tahunan untuk karyawan tetap adalah **12 hari**. \n\nSebagai catatan, hak cuti ini dapat mulai diambil setelah Anda memiliki **masa kerja minimal 3 bulan**.\n\nJika Anda memiliki pertanyaan lain atau membutuhkan bantuan lebih lanjut, jangan ragu untuk menghubungi kami kembali. Semoga harinya menyenangkan!"
}

# 3rd Test Response dengan Fallback mechanism due to kuota harian limit:
{
  "status": "success",
  "intent": "faq",
  "data": "[Mode Fallback - Kuota API Habis]\n\nBerdasarkan Knowledge Base:\nKaryawan tetap mendapat jatah 12 hari cuti tahunan yang dapat diambil setelah masa kerja minimal 3 bulan."
}

## 2. Skenario 2 (RAG - Kebijakan IT/Prosedur):

JSON
{
  "query": "Bagaimana cara menyambungkan printer kantor?"
}

# 1st Test Response:
{
  "status": "success",
  "intent": "faq",
  "data": "Halo, terima kasih telah menghubungi IT Helpdesk.\n\nMohon maaf, saat ini informasi mengenai **cara menyambungkan printer kantor** tidak tersedia di dalam basis pengetahuan (*Knowledge Base*) kami.\n\nUntuk membantu menyelesaikan kendala tersebut dan mendapatkan panduan instalasi printer pada perangkat Anda, kami menyarankan Anda untuk **menghubungi tim IT Support secara langsung**.\n\nJika ada pertanyaan lain terkait akses sistem atau kendala lainnya yang bisa saya bantu, silakan beri tahu saya. Terima kasih!"
}

# 2nd Test Response:
{
  "status": "success",
  "intent": "faq",
  "data": "Halo! Terima kasih telah menghubungi IT Helpdesk.\n\nMohon maaf, saat ini saya tidak memiliki informasi mengenai panduan menyambungkan printer kantor di dalam Knowledge Base kami. \n\nUntuk bantuan lebih lanjut terkait konfigurasi printer pada perangkat Anda, silakan menghubungi tim **IT Support** secara langsung agar dapat dipandu atau dibantu secara teknis. \n\nApakah ada hal lain yang bisa saya bantu terkait akses sistem atau portal internal?"
}

# 3rd Test Response dengan Fallback mechanism due to kuota harian limit:
{
  "status": "success",
  "intent": "faq",
  "data": "[Mode Fallback - Kuota API Habis]\n\nBerdasarkan Knowledge Base:\nAkses dari luar kantor memerlukan koneksi VPN aktif yang sudah terinstal pada perangkat kerja resmi."
}

## 3. Skenario 3 (Tool Call - Tiket Valid):

JSON
{
  "query": "Tolong cek status laporan tiket TICKET-0001"
}


# 1st Test Response:
{
  "status": "success",
  "intent": "ticket_status",
  "data": "Informasi Status Tiket (TICKET-0001):\n- Pemohon: Andi Pratama\n- Kategori: Hardware\n- Subjek: Laptop tidak bisa menyala\n- Status Saat Ini: Selesai\n- Pembaruan Terakhir: 2026-08-20"
}

# 2nd Test Response:
{
  "status": "success",
  "intent": "ticket_status",
  "data": "Informasi Status Tiket (TICKET-0001):\n- Pemohon: Andi Pratama\n- Kategori: Hardware\n- Subjek: Laptop tidak bisa menyala\n- Status Saat Ini: Selesai\n- Pembaruan Terakhir: 2026-08-20"
}

# 3rd Test Response dengan Fallback mechanism due to kuota harian limit, tidak berdampak karena untuk ticket_status tidak menggunakan gemini.
{
  "status": "success",
  "intent": "ticket_status",
  "data": "Informasi Status Tiket (TICKET-0001):\n- Pemohon: Andi Pratama\n- Kategori: Hardware\n- Subjek: Laptop tidak bisa menyala\n- Status Saat Ini: Selesai\n- Pembaruan Terakhir: 2026-08-20"
}

## 4. Skenario 4 (Tool Call - Tiket Tidak Ditemukan):

JSON
{
  "query": "Bagaimana status tiket TICKET-9999?"
}

# 1st Test Response:
{
  "status": "success",
  "intent": "ticket_status",
  "data": "Maaf, tiket dengan ID 'TICKET-9999' tidak ditemukan di dalam sistem. Mohon periksa kembali nomor ID tiket Anda."
}

# 2nd Test Response:
{
  "status": "success",
  "intent": "ticket_status",
  "data": "Maaf, tiket dengan ID 'TICKET-9999' tidak ditemukan di dalam sistem. Mohon periksa kembali nomor ID tiket Anda."
}

# 3rd Test Response dengan Fallback mechanism due to kuota harian limit, tidak berdampak karena untuk ticket_status tidak menggunakan gemini.
{
  "status": "success",
  "intent": "ticket_status",
  "data": "Maaf, tiket dengan ID 'TICKET-9999' tidak ditemukan di dalam sistem. Mohon periksa kembali nomor ID tiket Anda."
}


## 5. Skenario 5 (Query Ambigu / Di Luar Cakupan):

JSON
{
  "query": "Bagaimana resep membuat kue pancong?"
}

# 1st Test Response:
{
  "status": "success",
  "intent": "faq",
  "data": "Halo! Mohon maaf, saya tidak memiliki informasi mengenai resep membuat kue pancong di dalam Knowledge Base kami. \n\nLayanan ini khusus ditujukan untuk pertanyaan seputar IT Helpdesk dan sistem internal. Jika Anda memiliki pertanyaan atau kendala terkait sistem kerja dan teknis IT, silakan ajukan kembali atau Anda dapat menghubungi tim IT Support secara langsung."
}

# 2nd Test Response:
{
  "status": "success",
  "intent": "faq",
  "data": "Halo! Mohon maaf, saya tidak memiliki informasi mengenai resep membuat kue pancong di dalam Knowledge Base IT Helpdesk. \n\nFokus saya adalah membantu Anda seputar layanan dan kendala teknis IT internal. Jika Anda memiliki pertanyaan atau kendala terkait sistem kerja, silakan beri tahu saya atau hubungi tim IT Support secara langsung untuk bantuan lebih lanjut. \n\nTerima kasih!"
}

# 3rd Test Response dengan Fallback mechanism due to kuota harian limit, response tidak sesuai
{
  "status": "success",
  "intent": "faq",
  "data": "[Mode Fallback - Kuota API Habis]\n\nBerdasarkan Knowledge Base:\nCuti diajukan melalui portal HR internal minimal 3 hari kerja sebelum tanggal cuti, dan memerlukan persetujuan atasan langsung."
}

## KETERBATASAN SISTEM:
(1) Ada batas kuota harian (Daily Free Tier Limit) untuk model gemini-3.8-flash yang digunakan.  Jadi dibuat solusi Mock/Fallback jika terjadi error 429 (You exceeded your current quota, please check your plan and billing details).
