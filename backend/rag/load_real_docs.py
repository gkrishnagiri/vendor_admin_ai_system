import os
from docx import Document
from ingestion import ingest_document

# 🔥 Absolute-safe path (important)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔥 Go to project root (two levels up)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))

DOCS_PATH = os.path.join(PROJECT_ROOT, "docs/uploaded_docs")


def read_docx(file_path):
    """
    Read entire DOCX file as single string
    """
    doc = Document(file_path)

    # Join all paragraphs
    content = "\n".join([para.text.strip() for para in doc.paragraphs if para.text.strip()])

    return content


def read_sql(file_path):
    """
    Read SQL file as full text
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_all_docs():
    """
    Load ALL documents as SINGLE embeddings (no chunking)
    """

    if not os.path.exists(DOCS_PATH):
        print(f"[Loader] Path not found: {DOCS_PATH}")
        return

    files = os.listdir(DOCS_PATH)

    if not files:
        print("[Loader] No files found")
        return

    print(f"[Loader] Found {len(files)} files\n")

    for file in files:
        full_path = os.path.join(DOCS_PATH, file)

        print(f"\n[Loader] Processing: {file}")

        # -----------------------------
        # 🔹 STEP 1 — READ FILE
        # -----------------------------
        try:
            if file.endswith(".docx"):
                content = read_docx(full_path)

            elif file.endswith(".sql"):
                content = read_sql(full_path)

            else:
                print(f"[Loader] Skipping unsupported file: {file}")
                continue

        except Exception as e:
            print(f"[Loader] ERROR reading file {file}: {e}")
            continue  # move to next file

        # -----------------------------
        # 🔹 STEP 2 — VALIDATE CONTENT
        # -----------------------------
        if not content or len(content.strip()) == 0:
            print(f"[Loader] Empty content, skipping: {file}")
            continue

        print(f"[Loader] Content length: {len(content)} characters")

        # -----------------------------
        # 🔹 STEP 3 — INGEST (SEPARATE TRY)
        # -----------------------------
        try:
            ingest_document(file, content)
            print(f"[Loader] Successfully ingested: {file}")

        except Exception as e:
            print(f"[Loader] ERROR during ingestion {file}: {e}")
            continue  # continue with next file


if __name__ == "__main__":
    load_all_docs()