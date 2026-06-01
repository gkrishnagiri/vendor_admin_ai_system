import asyncio
import os
import sys

# Add backend_v2 to path
sys.path.append(os.path.abspath('backend_v2'))

from agents.query_decomposer import decomposer

async def main():
    query = 'I need to create a new user ID for John. User id or Username: john123; Email ID: john123@test.com; pwd: Welcome123. Create a new role called "HR". Then add "View Dashboard" permission to the newly created HR role.'
    try:
        res, usage = await decomposer.decompose(query)
        print("RESULT:", res)
    except Exception as e:
        print("EXCEPTION:", e)

asyncio.run(main())
