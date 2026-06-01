import asyncio
import sys
sys.path.insert(0, "/mnt/e/giri/AIProjects/projects/vendor_admin_ai_agents/backend_v2")
from rag.retriever import retriever

async def test():
    query = "System Access Login Authentication and Assign \"VIEW_DASHBOARD\" permission to \"Sales\" role"
    print(f"Searching for: {query}")
    chunks = await retriever.search(query, top_k=15)
    for i, c in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(c['section'])
        print(c['content'][:150])

asyncio.run(test())
