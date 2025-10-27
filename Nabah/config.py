import os
from dotenv import load_dotenv


env_path = "/content/Nabah/.env"
if not os.path.exists(env_path):
    raise FileNotFoundError(f".env file not found at: {env_path}")

load_dotenv(env_path)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

print("🔗 Loaded config values:")
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY exists:", bool(SUPABASE_KEY))
print("LLM_MODEL:", LLM_MODEL)
