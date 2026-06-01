from fastapi import FastAPI
from api.rag import router as rag_router
from api.admin import router as admin_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Vendor Admin AI Agents")

# Add CORS so our frontend Vite app on a different port can communicate successfully
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router, prefix="/rag")
app.include_router(admin_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "AI Agent Backend Running"}

@app.get("/health")
def health():
    return {"status": "ok"}