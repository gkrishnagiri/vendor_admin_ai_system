from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List, Optional
import psycopg2
import os
from pydantic import BaseModel
from rag.ingestion import ingest_document
from dotenv import load_dotenv
import io
from docx import Document
from pypdf import PdfReader

load_dotenv()

router = APIRouter()
DB_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL)

# --- TAXONOMY ROUTES ---

class TaxonomyCreate(BaseModel):
    business_unit: str
    business_area: str
    business_function: str

@router.get("/taxonomy")
def get_taxonomy():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, business_unit, business_area, business_function FROM taxonomy ORDER BY business_unit, business_area")
        rows = cur.fetchall()
        
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "business_unit": r[1],
                "business_area": r[2],
                "business_function": r[3]
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@router.post("/taxonomy")
def create_taxonomy(item: TaxonomyCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO taxonomy (business_unit, business_area, business_function)
            VALUES (%s, %s, %s) RETURNING id
        """, (item.business_unit, item.business_area, item.business_function))
        new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": new_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            conn.close()


# --- DOCUMENT ROUTES ---

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    business_unit: Optional[str] = Form(None),
    business_area: Optional[str] = Form(None),
    business_function: Optional[str] = Form(None),
    application_name: Optional[str] = Form(None)
):
    try:
        content = await file.read()
        filename = file.filename.lower()
        text_content = ""

        if filename.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            text_content = "\n".join([para.text for para in doc.paragraphs])
        elif filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            text_content = "\n".join([page.extract_text() for page in reader.pages])
        else:
            # Fallback to UTF-8 text
            text_content = content.decode("utf-8", errors="ignore")
        
        # Final safety strip of NUL characters
        text_content = text_content.replace('\x00', '')
        
        ingest_document(
            name=file.filename,
            content=text_content,
            business_unit=business_unit,
            business_area=business_area,
            business_function=business_function,
            application_name=application_name
        )
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
def get_documents():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, created_at, business_unit, business_area, business_function, application_name 
            FROM documents ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "name": r[1],
                "created_at": r[2],
                "business_unit": r[3],
                "business_area": r[4],
                "business_function": r[5],
                "application_name": r[6]
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Since we use ON DELETE CASCADE, deleting from documents removes related chunks automatically
        cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        conn.commit()
        return {"status": "deleted", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            conn.close()


# --- SETTINGS ROUTES ---

class SettingUpdateItem(BaseModel):
    key: str
    value: str

@router.get("/settings")
def get_settings():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        rows = cur.fetchall()
        settings = {r[0]: r[1] for r in rows}
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@router.post("/settings")
def update_settings(updates: List[SettingUpdateItem]):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for update in updates:
            # Upsert
            cur.execute("""
                INSERT INTO settings (key, value) VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
            """, (update.key, update.value))
        conn.commit()
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals() and conn:
            conn.close()
