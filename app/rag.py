"""
Implementasi ini mencakup pembuatan indeks FAISS dari file it_helpdesk_knowledge_base.csv, 
pencarian semantik (semantic search), serta penyusunan prompt dan 
pemanggilan LLM Gemini untuk menghasilkan jawaban yang akurat berdasarkan knowledge base

Modul RAG — mengubah knowledge base menjadi embedding, menyimpannya ke FAISS,
melakukan semantic search, lalu menghasilkan jawaban menggunakan LLM.

Alur ini serupa dengan yang sudah dibangun di Assignment 3 (Semantic Search &
LLM Application) dan Sesi 11 (Building a Simple RAG System) — di assignment ini,
alur tersebut dibungkus menjadi fungsi yang dipanggil oleh router.py.
"""
"""
Modul RAG — mengubah knowledge base menjadi pencarian berbasis TF-IDF & FAISS,
lalu menghasilkan jawaban menggunakan LLM Gemini.
"""

import os
import pandas as pd
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
import google.generativeai as genai

# Konfigurasi LLM Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

KNOWLEDGE_BASE_PATH = "data/it_helpdesk_knowledge_base.csv"

_index = None
_documents = None
_df = None
_vectorizer = None


def build_index():
    """
    Memuat knowledge base CSV dan membangun index FAISS berbasis TF-IDF Vectorizer lokal.
    (Solusi andal, cepat, dan bebas dari error 404 API model embedding).
    """
    global _index, _documents, _df, _vectorizer
    
    file_path = KNOWLEDGE_BASE_PATH
    if not os.path.exists(file_path):
        file_path = "it_helpdesk_knowledge_base.csv"
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Knowledge base file not found at {file_path}")

    _df = pd.read_csv(file_path)

    _documents = []
    texts_to_embed = []
    
    for _, row in _df.iterrows():
        doc_text = (
            f"Kategori: {row['category']}\n"
            f"Pertanyaan: {row['question']}\n"
            f"Jawaban: {row['answer']}"
        )
        _documents.append(doc_text)
        texts_to_embed.append(f"{row['category']} {row['question']} {row['answer']}")

    # Menggunakan TF-IDF untuk mengubah teks dokumen menjadi vektor numerik
    _vectorizer = TfidfVectorizer(max_features=1000)
    matrix = _vectorizer.fit_transform(texts_to_embed).toarray().astype("float32")

    # Normalisasi L2 untuk kesesuaian cosine similarity dengan IndexFlatIP
    faiss.normalize_L2(matrix)
    dimension = matrix.shape[1]
    
    _index = faiss.IndexFlatIP(dimension)
    _index.add(matrix)


def semantic_search(query: str, top_k: int = 3):
    """
    Melakukan pencarian dokumen relevan menggunakan TF-IDF vector & FAISS index.
    """
    global _index, _documents, _df, _vectorizer
    if _index is None or _vectorizer is None:
        build_index()

    # Ubah query user menjadi vektor menggunakan vectorizer yang sama
    query_vec = _vectorizer.transform([query]).toarray().astype("float32")
    faiss.normalize_L2(query_vec)

    k = min(top_k, len(_documents))
    distances, indices = _index.search(query_vec, k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(_documents):
            results.append({
                "document": _documents[idx],
                "score": float(distances[0][i]),
                "row": _df.iloc[idx].to_dict(),
            })
    return results


async def answer_from_knowledge_base(query: str) -> str:
    """
    Menjalankan semantic search, menyusun prompt dengan konteks,
    lalu memanggil LLM Gemini untuk menghasilkan jawaban.
    """
    search_results = semantic_search(query, top_k=3)
    context_text = "\n\n---\n\n".join([res["document"] for res in search_results])

    prompt = f"""Anda adalah asisten AI IT Helpdesk yang ramah, profesional, dan solutif.
Tugas Anda adalah menjawab pertanyaan pengguna berdasarkan informasi dari Knowledge Base IT Helpdesk di bawah ini.
Jika informasi yang relevan tidak ditemukan di dalam context, katakan dengan jujur bahwa Anda tidak memiliki informasi tersebut dan sarankan menghubungi tim IT Support secara langsung. Jangan mengarang informasi.

Context dari Knowledge Base:
{context_text}

Pertanyaan Pengguna: {query}

Berikan jawaban yang jelas, terstruktur, dan langsung pada inti permasalahan dalam Bahasa Indonesia.
"""

    # Memanggil LLM Gemini untuk generasi jawaban akhir
    model = genai.GenerativeModel("gemini-3.8-flash")
    response = model.generate_content(prompt)

    return response.text