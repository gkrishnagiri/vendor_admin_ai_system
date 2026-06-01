import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# Create Vector extension in PostgreSQL DB
cur.execute("""
CREATE EXTENSION IF NOT EXISTS vector;
""")

# Documents table
cur.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    name TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# Chunks table
cur.execute("""
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INT,
    content TEXT,
    section TEXT,          -- NEW
    chunk_index INT,       -- NEW
    embedding VECTOR(1536)
);
""")

conn.commit()
cur.close()
conn.close()

print("RAG tables created")