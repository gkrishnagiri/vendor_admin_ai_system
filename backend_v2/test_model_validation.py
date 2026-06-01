import asyncio
import sys
import os
import psycopg2
from dotenv import load_dotenv

# Load env variables first thing
load_dotenv()

# Set CWD to backend_v2
os.chdir("/mnt/e/giri/AIProjects/projects/vendor_admin_ai_agents/backend_v2")
sys.path.insert(0, "/mnt/e/giri/AIProjects/projects/vendor_admin_ai_agents/backend_v2")

from agents.info_gatherer import info_gatherer

async def test():
    
    # 1. Fetch exact database content
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT content FROM chunks LIMIT 1")
    sop_context = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    task_description = "Assign \"VIEW_DASHBOARD\" permission to \"Sales\" role"
    query = "Assign \"VIEW_DASHBOARD\" permission to \"Sales\" role"
    history = []
    
    print("SOP Context length:", len(sop_context))
    print("Calling check_missing_info...")
    
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
