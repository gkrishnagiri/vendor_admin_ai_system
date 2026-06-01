from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import os
from dotenv import load_dotenv

# IMPORTANT: Load environment before importing internal modules that use them
load_dotenv()

from orchestrator.supervisor import run_chat_v2
from api.admin_router import router as admin_router

app = FastAPI(title="Generic AI Automation Framework v2")

# Add CORS so our frontend Vite app on a different port can communicate successfully
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BROWSER PRE-WARM ---
@app.on_event("startup")
async def startup_event():
    print("⏳ Pre-warming Playwright browser in the background...")
    from engine.browser_manager import get_browser
    asyncio.create_task(get_browser())

# --- RE-USE MODELS ---
class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[HistoryMessage]] = []

# --- V2 CHAT ROUTER ---
v2_router = APIRouter()

@v2_router.post("/chat")
async def chat(request: ChatRequest):
    queue = asyncio.Queue()
    history = [{"role": m.role, "content": m.content} for m in (request.history or [])]

    async def run_logic():
        try:
            # run_chat_v2 is the core ADK + LangGraph logic
            result = await run_chat_v2(request.query, history, queue)
            await queue.put({"type": "result", "payload": result})
        except Exception as e:
            await queue.put({"type": "error", "error": str(e)})

    asyncio.create_task(run_logic())

    async def event_generator():
        while True:
            msg = await queue.get()
            yield f"data: {json.dumps(msg)}\n\n"
            if msg.get("type") in ["result", "error"]:
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- REGISTER ROUTERS ---

# /api/v2/chat
app.include_router(v2_router, prefix="/api/v2")

# /api/taxonomy, /api/documents, /api/settings
app.include_router(admin_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "AI Agent Backend v2 Running"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Standardize on port 8002 for the frontend
    uvicorn.run(app, host="0.0.0.0", port=8002)
