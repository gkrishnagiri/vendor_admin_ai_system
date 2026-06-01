import os
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class Retriever:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db_url = os.getenv("DATABASE_URL")
        self.embedding_model = "text-embedding-3-small"

    def get_embedding(self, text):
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    async def search(self, query, top_k=10):
        """
        Search for the most relevant document chunks (single-chunk ingestion).
        Returns a list of dictionary chunks with 'content' and 'source'.
        """
        print(f"\n[Retriever] Search Query: '{query}'")
        
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()

        try:
            query_embedding = self.get_embedding(query)
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

            cur.execute("""
                SELECT c.content, d.name, c.section
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                ORDER BY c.embedding <-> %s::vector
                LIMIT %s
            """, (embedding_str, top_k))

            results = cur.fetchall()
            
            print(f"[Retriever] Found {len(results)} potential chunks.")
            
            context_chunks = []
            for i, r in enumerate(results):
                content, source, section = r
                print(f"  » #{i+1} | Source: {source} | Section: {section if section else 'N/A'}")
                print(f"    Snippet: {content[:150].replace('\\n', ' ')}...")
                
                context_chunks.append({
                    "content": content,
                    "source": source,
                    "section": section
                })
            
            return context_chunks

        finally:
            cur.close()
            conn.close()

# Singleton instance
retriever = Retriever()
