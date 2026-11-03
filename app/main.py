"""
Entry point aplikasi FastAPI — IT Helpdesk Assistant.

Alur endpoint utama:
  1. Menerima pertanyaan/permintaan dari user
  2. Meneruskan ke router (router.py) untuk menentukan intent
  3. Router memanggil RAG (rag.py) atau tool (tools.py) sesuai intent
  4. Mengembalikan response terstruktur ke client
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.router import handle_query

app = FastAPI(title="IT Helpdesk Assistant API")


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    status: str
    intent: str
    data: str


@app.get("/health")
async def health():
    """Endpoint sederhana untuk memastikan service berjalan."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Endpoint utama. Menerima pertanyaan bebas dari user (bisa berupa
    pertanyaan informasi/kebijakan ATAU permintaan cek status tiket),
    lalu meneruskannya ke router untuk diproses dengan penanganan error.
    """
    try:
        # Validasi input kosong
        if not request.query or not request.query.strip():
            return AskResponse(
                status="error",
                intent="unknown",
                data="Query tidak boleh kosong. Silakan masukkan pertanyaan atau nomor tiket Anda."
            )

        # Proses query melalui router
        result = await handle_query(request.query)
        
        # Pastikan format result sesuai dengan AskResponse
        return AskResponse(
            status=result.get("status", "success"),
            intent=result.get("intent", "unknown"),
            data=str(result.get("data", ""))
        )

    except Exception as e:
        error_message = str(e)
        
        # Penanganan khusus jika kuota API habis (Error 429 / Quota)
        if "429" in error_message or "quota" in error_message.lower():
            try:
                # Impor fungsi semantic_search secara lokal untuk fallback
                from app.rag import semantic_search
                search_results = semantic_search(request.query, top_k=1)
                if search_results:
                    fallback_answer = f"[Mode Fallback - Kuota API Habis]\n\nBerdasarkan Knowledge Base:\n{search_results[0]['row']['answer']}"
                    return AskResponse(
                        status="success",
                        intent="faq",
                        data=fallback_answer
                    )
            except Exception:
                pass # Jika fallback gagal, lanjut ke error handler standar

        # Tangani pesan error spesifik dari Gemini API / API Key
        if "API_KEY" in error_message.upper() or "GEMINI" in error_message.upper():
            return AskResponse(
                status="error",
                intent="system_error",
                data="Maaf, terjadi kendala pada layanan AI (API Key / Koneksi LLM). Silakan coba beberapa saat lagi."
            )
            
        # Error umum lainnya termasuk 429 jika fallback tidak menemukan hasil
        return AskResponse(
            status="error",
            intent="system_error",
            data=f"Detail Error: {error_message}"
        )