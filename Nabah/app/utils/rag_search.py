from typing import List, Dict
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv


env_path = "/content/Nabah/.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print(f" .env not found at {env_path}")


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


print("🔧 rag_search config:")
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY exists:", bool(SUPABASE_KEY))


if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        f" Missing Supabase credentials.\nSUPABASE_URL={SUPABASE_URL}\nSUPABASE_KEY exists={bool(SUPABASE_KEY)}"
    )


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


_embedder = SentenceTransformer(EMBEDDING_MODEL)

def embed_query(text: str) -> list[float]:
    vec = _embedder.encode([f"query: {text}"], normalize_embeddings=True)[0]
    return np.asarray(vec, dtype=np.float32).tolist()

def search_context(query: str, top_k: int = 8, threshold: float = 0.0) -> List[Dict]:
    q = embed_query(query)
    try:
        res = supabase.rpc(
            "match_documents_rag",
            {"query_embedding": q, "match_threshold": threshold, "match_count": top_k},
        ).execute()
        rows = res.data or []
    except Exception as e:
        print(" search_context error:", e)
        rows = []
    return rows

if __name__ == "__main__":
    print("Testing search…")
    out = search_context("PPE violations", 5)
    print(f"Retrieved {len(out)} rows.")
