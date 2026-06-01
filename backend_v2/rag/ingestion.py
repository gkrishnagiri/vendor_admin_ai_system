import os
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

# Load from current directory or parent
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_URL = os.getenv("DATABASE_URL")

# -----------------------------
# 🔹 EMBEDDING
# -----------------------------
def get_embedding(text):
    """
    Generate embedding for full document using OpenAI
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# -----------------------------
# 🔹 INGEST DOCUMENT (NO CHUNKING)
# -----------------------------
def ingest_document(name, content, business_unit=None, business_area=None, business_function=None, application_name=None):
    """
    Store entire document as a SINGLE embedding with taxonomy support
    """

    print(f"\n[Ingest] Processing document: {name}")
    
    # 🚨 FIX: Remove NUL (0x00) characters which crash PostgreSQL
    if content:
        content = content.replace('\x00', '')

    if not content or len(content.strip()) == 0:
        print("[Ingest] Empty content. Skipping.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # 🔥 STEP 1 — Remove existing document (avoid duplicates)
        cur.execute("DELETE FROM documents WHERE name = %s RETURNING id", (name,))
        existing = cur.fetchone()

        if existing:
            doc_id = existing[0]
            cur.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))
            print(f"[Ingest] Deleted existing document: {name}")

        # 🔥 STEP 2 — Insert document metadata
        cur.execute(
            """
            INSERT INTO documents (name, content, business_unit, business_area, business_function, application_name) 
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (name, content, business_unit, business_area, business_function, application_name)
        )
        doc_id = cur.fetchone()[0]

        print(f"[Ingest] Document ID: {doc_id}")

        # 🔥 STEP 3 — Generate SINGLE embedding
        print("[Ingest] Generating embedding...")
        embedding = get_embedding(content)

        # 🔥 STEP 4 — Store as SINGLE chunk
        cur.execute(
            """
            INSERT INTO chunks (document_id, content, embedding)
            VALUES (%s, %s, %s)
            """,
            (doc_id, content, embedding)
        )

        conn.commit()

        print(f"[Ingest] Successfully stored document: {name}")

    except Exception as e:
        print(f"[Ingest] Error processing {name}: {e}")
        raise

    finally:
        if conn:
            cur.close()
            conn.close()
