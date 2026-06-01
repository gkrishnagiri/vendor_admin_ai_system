# 🚀 Vendor Admin AI Agent System

## 🧠 Overview

This project is a **generic multi-agent AI system** designed to:

- Understand natural language queries
- Retrieve knowledge using RAG (Retrieval Augmented Generation)
- Generate step-by-step execution plans
- Execute actions on a UI (browser automation via Playwright)

---

## 🎯 Goal

Enable users to interact with any application using natural language:

```

User: Create a new user john123

System:
→ Understand intent
→ Retrieve relevant documentation
→ Generate UI steps
→ Execute actions in browser

```

---

## 🏗️ Architecture

```

User Query
↓
Orchestrator
↓
Intent Classifier
↓
-

| RAG Flow   | ACTION Flow |
| ---------- | ----------- |
| Retriever  | Planner     |
| LLM Answer | Executor    |

---

```

---

## 🧩 Key Components

### 🔹 Intent Classifier
- Classifies query into:
  - `RAG` → informational
  - `ACTION` → executable

---

### 🔹 Retriever (RAG)
- Uses:
  - OpenAI embeddings (`text-embedding-3-small`)
  - PostgreSQL + pgvector
- Retrieves relevant documents

---

### 🔹 Planner Agent
- Converts query + context into:
```

["Step 1", "Step 2", ...]

````

---

### 🔹 Executor
- Uses Playwright
- Executes:
- click
- fill
- navigate
- wait
- Includes:
- retry logic
- fail-fast behavior

---

### 🔹 Orchestrator
- Controls full pipeline
- Ensures:
- no execution without context
- proper routing

---

## 🗄️ Database

### Tables:
- `documents`
- `chunks`
- `settings`
- `chat_sessions`
- `messages`

---

## ⚙️ Setup & Commands

---

# 🐳 DOCKER COMMANDS

---

## 🔹 Start Docker Containers

```bash
docker compose --env-file ../.env up -d
OR
docker compose up -d
````

👉 Starts PostgreSQL with pgvector in background

---

## 🔹 Check Running Containers

```bash
docker ps
```

👉 Shows running containers

---

## 🔹 Check All Containers (including stopped)

```bash
docker ps -a
```

---

## 🔹 View Logs

```bash
docker logs ai_agents_postgres
```

👉 Replace container name if needed

---

## 🔹 Stop Containers

```bash
docker compose down
```

👉 Stops containers but keeps data

---

## 🔹 Stop + Remove Volumes (⚠️ deletes DB data)

```bash
docker compose down -v
```

---

## 🔹 Restart Containers

```bash
docker compose restart
```

---

## 🔹 Remove Specific Container

```bash
docker rm -f ai_agents_postgres
```

---

# 🧠 DATABASE COMMANDS

---

## 🔹 Connect to PostgreSQL

```bash
docker exec -it ai_agents_postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

Example:

```bash
docker exec -it ai_agents_postgres psql -U admin -d ai_agents_db
```

---

## 🔹 Show Tables

```sql
\dt
```

---

## 🔹 Describe Table

```sql
\d documents
```

---

## 🔹 Run SELECT Query

```sql
SELECT * FROM documents;
```

---

## 🔹 Exit DB

```sql
\q
```

---

# 🚀 BACKEND COMMANDS

---

## 🔹 Start Backend Server

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8002 --reload --log-level debug

or

uv run uvicorn main:app --port 8010 --reload
```

👉 Starts FastAPI server with auto-reload

---

## 🔹 Alternative (if uv not available)

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

---

## 🔹 Check if Backend is Running

Open browser:

```
http://localhost:8000/docs
```

👉 Swagger UI

---

## 🔹 Test API via curl

```bash
curl -X POST "http://127.0.0.1:8000/query" \
-H "Content-Type: application/json" \
-d '{"query": "how to create a user"}'
```

---

# 📥 DOCUMENT INGESTION

---

## 🔹 Load Real Documents

```bash
python load_real_docs.py
```

👉 Reads `.docx` and `.sql` files and stores embeddings

---

## 🔹 Test Ingestion

```bash
python load_test_docs.py
```

---

# 🔍 RAG TESTING

---

## 🔹 Run RAG Test

```bash
python test_real_rag.py
```

---

## 🔹 Debug Retrieval

```bash
python test_rag.py
```

---

# 🧪 DB INITIALIZATION

---

## 🔹 Initialize RAG Tables

```bash
python init_rag_db.py
```

---

## 🔹 Initialize App Tables

```bash
python init_db.py
```

---

## 🔹 Test DB Connection

```bash
python db_test.py
```

---

# ⚠️ TROUBLESHOOTING

---

## 🔹 Docker Not Starting

```bash
docker compose build --no-cache
docker compose up -d
```

---

## 🔹 Port Already in Use

Check:

```bash
lsof -i :5434
```

Kill process if needed

---

## 🔹 DB Connection Issues

* Check `.env`
* Ensure container is running:

  ```bash
  docker ps
  ```

---

## 🔹 Playwright Issues

```bash
npx playwright install
```

---

# 🚨 CURRENT LIMITATIONS

* No DOM awareness
* Limited selector reliability
* No UI state tracking

---

# 🚀 NEXT STEPS

* DOM-aware execution
* Self-healing selectors
* State-aware agent
* Admin UI + Chat UI
* Cost tracking improvements

---

# 🎯 One-Line Summary

```
RAG-powered, planner-driven, browser-executing AI agent system — moving toward autonomous UI automation
```

---

# 📌 Notes

* System is designed to be **generic**
* No hardcoded UI logic
* Can be extended to any application

---

```

---

## ✅ What You Now Have

This README gives you:

✔ All commands in one place  
✔ DB access steps  
✔ Docker lifecycle control  
✔ Backend execution flow  
✔ Testing commands  
✔ Troubleshooting  

---

## 🚀 Next

When you're ready, we’ll extend this with:

- Admin UI usage
- Chat UI usage
- Cost tracking dashboards
- Deployment (Docker + Cloud)

---

If you want, I can next:
👉 Generate **folder structure + architecture diagram README section**  
👉 Or build **Admin UI APIs + schema layer**
```
