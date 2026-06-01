from ingestion import ingest_document

# Example test document
content = """
To start backend:
uv run uvicorn app.main:app --reload

To start frontend:
npm run dev
"""

ingest_document("setup_guide", content)