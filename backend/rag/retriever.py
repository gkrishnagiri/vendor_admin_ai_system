import os
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI
from services.llm_service import generate_answer
from agents.tracing import trace
from services.query_rewriter import rewrite_query

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text, embedding_model="text-embedding-3-small"):

    response = client.embeddings.create(
        model=embedding_model,
        input=text
    )
    return response.data[0].embedding


def search(query, top_k=3, llm_model="gpt-4o-mini", embedding_model="text-embedding-3-small", history=None):
    history = history or []

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    rewritten_query = rewrite_query(query, llm_model=llm_model)

    print("[Retriever] Rewritten Query:", rewritten_query)

    query_embedding = get_embedding(rewritten_query, embedding_model=embedding_model)
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    cur.execute("""
        SELECT c.content, d.name
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        ORDER BY c.embedding <-> %s::vector
        LIMIT %s
    """, (embedding_str, top_k))

    results = cur.fetchall()

    cur.close()
    conn.close()

    context_chunks = [
        {"content": r[0], "source": r[1]}
        for r in results
    ]

    rag_result = generate_answer(query, context_chunks, llm_model=llm_model, history=history)

    return {
        "query": query,
        "status": rag_result["status"],
        "answer": rag_result["answer"],
        "sources": [c["source"] for c in context_chunks],
        "usage": rag_result.get("usage", {})
    }