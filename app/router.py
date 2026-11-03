"""
Router — menentukan apakah query user butuh RAG (informasi/kebijakan)
atau tool call (aksi spesifik, misal cek status tiket).

Pola ini mengikuti workflow router yang sudah dipelajari di Sesi 12.4:
  user input -> intent detection -> jika butuh data -> retrieval (RAG)
                                  -> jika butuh aksi -> tool call
"""

import os
import re
import google.generativeai as genai
from app.rag import answer_from_knowledge_base
from app.tools import get_ticket_status

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


async def detect_intent(query: str) -> str:
    prompt = f"""Klasifikasikan pertanyaan berikut ke dalam salah satu kategori:
- 'faq' jika pertanyaan berupa informasi umum, kebijakan, atau prosedur.
- 'ticket_status' jika permintaan mengenai pengecekan status, progres, atau pelacakan tiket aduan tertentu.

Jawab HANYA dengan satu kata kategori saja ('faq' atau 'ticket_status').

Pertanyaan: {query}"""

    try:
        model = genai.GenerativeModel("gemini-3.8-flash")
        response = model.generate_content(prompt)
        intent = response.text.strip().lower()
        
        if "ticket_status" in intent:
            return "ticket_status"
        elif "faq" in intent:
            return "faq"
        else:
            if any(kw in query.lower() for kw in ["ticket", "tiket", "status", "laporan", "aduan", "nomor"]):
                return "ticket_status"
            return "faq"
            
    except Exception:
        if any(kw in query.lower() for kw in ["ticket", "tiket", "status", "laporan", "aduan"]):
            return "ticket_status"
        return "faq"


async def handle_query(query: str) -> dict:
    intent = await detect_intent(query)

    if intent == "ticket_status":
        ticket_id = extract_ticket_id(query)
        data = get_ticket_status(ticket_id)
        return {"status": "success", "intent": "ticket_status", "data": data}

    elif intent == "faq":
        data = await answer_from_knowledge_base(query)
        return {"status": "success", "intent": "faq", "data": data}

    else:
        return {"status": "error", "intent": "unknown", "data": "Maaf, saya tidak memahami permintaan Anda."}


def extract_ticket_id(query: str) -> str:
    pattern = r"ticket[-\s]?\d+"
    match = re.search(pattern, query, re.IGNORECASE)
    
    if match:
        found = match.group(0)
        normalized = re.sub(r"[-\s]", "-", found).upper()
        if not normalized.startswith("TICKET-"):
            normalized = normalized.replace("TICKET", "TICKET-")
        return normalized
    
    words = query.split()
    for word in words:
        if "-" in word or any(char.isdigit() for char in word):
            cleaned = word.strip(".,!?")
            if "TICKET" in cleaned.upper():
                return cleaned.upper()
                
    return query.strip()