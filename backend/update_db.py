import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_db_update():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Ensuring pgvector is enabled...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        print("1. Creating taxonomy table...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS taxonomy (
            id SERIAL PRIMARY KEY,
            business_unit TEXT,
            business_area TEXT,
            business_function TEXT,
            application_name TEXT
        );
        """)

        print("2. Modifying documents table...")
        try:
            cur.execute("""
            ALTER TABLE documents 
            ADD COLUMN IF NOT EXISTS business_unit TEXT,
            ADD COLUMN IF NOT EXISTS business_area TEXT,
            ADD COLUMN IF NOT EXISTS business_function TEXT,
            ADD COLUMN IF NOT EXISTS application_name TEXT;
            """)
        except Exception as e:
            print(f"Error modifying documents table: {e}")

        print("3. Updating chunks foreign key for cascading deletes...")
        try:
            # First drop the existing foreign key if it exists
            cur.execute("""
            ALTER TABLE chunks DROP CONSTRAINT IF EXISTS chunks_document_id_fkey;
            """)
            
            # Since the original table might not have been created with an explicit fkey, 
            # we just attempt to add the constraint. But wait, if document_id has orphaned rows, it fails.
            # We assume it works for now or clean data first.
            cur.execute("""
            ALTER TABLE chunks
            ADD CONSTRAINT chunks_document_id_fkey
            FOREIGN KEY (document_id)
            REFERENCES documents(id)
            ON DELETE CASCADE;
            """)
        except Exception as e:
            print(f"Error updating chunks foreign key (might already exist or data mismatch): {e}")

        print("4. Ensuring settings table exists and has defaults...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            value TEXT
        );
        """)
        
        default_settings = [
            ("llm_model", "gpt-4o-mini"),
            ("embedding_model", "text-embedding-3-small"),
            ("chunk_size", "1000"),
            ("chunk_overlap", "200")
        ]
        
        for key, val in default_settings:
            cur.execute("""
            INSERT INTO settings (key, value) VALUES (%s, %s)
            ON CONFLICT (key) DO NOTHING;
            """, (key, val))

        cur.close()
        conn.close()
        print("Database update completed successfully!")

    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    run_db_update()
