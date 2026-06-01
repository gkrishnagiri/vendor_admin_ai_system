import asyncio
import sys
import os

# Set CWD to backend_v2
os.chdir("/mnt/e/giri/AIProjects/projects/vendor_admin_ai_agents/backend_v2")
sys.path.insert(0, "/mnt/e/giri/AIProjects/projects/vendor_admin_ai_agents/backend_v2")

from rag.retriever import retriever
from agents.info_gatherer import info_gatherer

async def test():
    search_query = "System Access Login Authentication and Assign 'VIEW_DASHBOARD' permission to 'Sales' role"
    chunks = await retriever.search(search_query, top_k=15)
    sop_context = "\n\n".join([f"Source: {c['source']}\nSection: {c['section']}\nContent: {c['content']}" for c in chunks])
    
    task_description = "Assign \"VIEW_DASHBOARD\" permission to \"Sales\" role"
    query = "Assign \"VIEW_DASHBOARD\" permission to \"Sales\" role"
    history = []
    
    result, extracted, usage = await info_gatherer.check_missing_info(
        query=query,
        task_description=task_description,
        sop_context=sop_context,
        history=history
    )
    
    print("\n--- RESULT ---")
    print(f"Unsupported action: {result.unsupported_action}")
    print(f"Is complete: {result.is_complete}")
    print(f"Title: {result.title}")
    print(f"Description: {result.description}")
    print(f"Fields: {result.fields}")
    print(f"Extracted parameters: {extracted}")

asyncio.run(test())
