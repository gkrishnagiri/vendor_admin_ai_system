import asyncio
import sys
import os

# Set CWD to backend_v2
os.chdir("/mnt/e/giri/AIProjects/projects/vendor_admin_ai_agents/backend_v2")
sys.path.insert(0, "/mnt/e/giri/AIProjects/projects/vendor_admin_ai_agents/backend_v2")

from rag.retriever import retriever

async def test():
    search_query = "System Access Login Authentication and Assign 'VIEW_DASHBOARD' permission to 'Sales' role"
    chunks = await retriever.search(search_query, top_k=15)
    print(f"\nTotal retrieved chunks: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Source: {c['source']}")
        print(f"Section: {c['section']}")
        print(f"Content:\n{c['content'][:300]}...")

asyncio.run(test())
