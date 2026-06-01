import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_current_settings():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        rows = cur.fetchall()
        settings = {r[0]: r[1] for r in rows}
        return settings
    except Exception as e:
        print(f"[Settings] Error fetching settings: {e}")
        return {
            "llm_model": "gpt-4o-mini",
            "embedding_model": "text-embedding-3-small"
        }
    finally:
        if 'conn' in locals() and conn:
            conn.close()
