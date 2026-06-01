# Universal UI Automation AI Agents — Project Document

> **Version:** 1.0 — POC Stage  
> **Date:** April 2026  
> **Classification:** Internal / Working Document

---

## 1. Executive Summary

This document describes the **Universal UI Automation AI Agents** system — a multi-agent, LLM-powered platform designed to automate end-to-end Application Support & Maintenance (ASM) tasks that today require repetitive human interaction with web-based administrative user interfaces across any application.

The system is currently at a **Proof-of-Concept (POC)** stage and targets one of the most pervasive and expensive categories of IT operational work: *front-end service requests* — the class of support tickets where a human agent must log into an application, navigate its UI, and perform a predefined sequence of actions (create a user, update a record, reset a configuration, etc.) on behalf of a business user.

The document articulates the business case, the architecture, ROI potential, and the path to a fully productionised, enterprise-grade generic platform that can address any application, any kind of UI, and any scenario.

---

## 2. Project Objective and Purpose

### 2.1 Objective

To build a **universally applicable, application-agnostic, conversational AI agent system** capable of:

1. **Understanding** natural-language service requests from support staff or end users regardless of the target application.
2. **Retrieving** the correct procedural knowledge from an internal knowledge base (documentation, SOPs, runbooks for any integrated system).
3. **Planning** a deterministic, step-by-step sequence of UI interactions to fulfil the request based strictly on retrieved documentation.
4. **Executing** those interactions autonomously against the target web application using a headless browser.
5. **Reporting** the outcome in plain language back to the requester.

The system acts as an autonomous **L1/L2 support agent** that can interpret intent, resolve informational queries (RAG), and physically execute UI-based tasks (Action) — all without requiring manual intervention from a human support engineer or application-specific API integrations.

### 2.2 Purpose

The core purpose is threefold:

| Purpose | Description |
|---|---|
| **Toil Elimination** | Automate repetitive, low-cognitive-value UI tasks that occupy a large share of support engineers' working hours across all enterprise software. |
| **Cost Reduction** | Reduce the per-ticket labour cost and overall headcount required for ASM delivery globally. |
| **Human Capacity Reallocation** | Free engineers from mechanical execution work, enabling them to focus on complex incidents, innovation, and system improvement. |

### 2.3 Design Philosophy

- **Application-agnostic**: The system targets any web UI without requiring application-specific code or API access. It "sees" and interacts with UIs exactly like a human does.
- **Knowledge-grounded**: Every action plan is derived from documentation retrieved via RAG — the LLM is not allowed to hallucinate steps.
- **Deterministic execution**: Each UI step is an atomic, verifiable action. The agent confirms outcomes via DOM inspection.
- **Conversational interface**: Support staff interact through a natural-language chat interface — no scripting knowledge or coding required.

---

## 3. Market Context — The ASM Cost Problem

### 3.1 How Much Do Organisations Spend on ASM?

Application Support and Maintenance is one of the largest and most persistent line items in enterprise IT budgets:

| Benchmark | Industry Figure |
|---|---|
| Share of IT budget on "keep the lights on" (KTLO) operations | **40–45%** of total IT budget (Gartner) |
| Share of total IT spend on maintaining existing systems | **55–80%** (broad industry, Gartner) |
| Annual maintenance cost per application | **15–25%** of original development cost |
| First year post-launch maintenance spike | Up to **50%** of build cost |
| Legacy / mature application maintenance cost | **20–40%+** of original cost |

For a mid-to-large enterprise with an IT budget of $50M, this translates to **$20M–$40M** per year in pure maintenance and operational support costs.

### 3.2 The Structure of ASM Work

ASM expenditure broadly maps to three tiers:

```
+----------------------------------------------------------+
|  L3 -- Engineering / Architectural Changes (5-10%)       |
|  High cost per ticket, code changes required             |
+----------------------------------------------------------+
|  L2 -- Technical Application Support (20-30%)            |
|  Complex configs, integrations, database diagnosis       |
+----------------------------------------------------------+
|  L1 -- Frontline Support (60-75% of ticket volume)       |
|  Password resets, access grants, UI navigation,          |
|  standard data entry, user management, etc.              |
+----------------------------------------------------------+
```

L1 handles **60–75% of all incoming ticket volume** and is characterised by high volume, low complexity, and highly repeatable scripted workflows — predominantly *service requests* (planned, predictable fulfilment) rather than *incidents* (unplanned breaks).

### 3.3 What Portion Is Attributable to Frontend Service Requests?

Within the L1 tier, **service requests** — distinct from incidents — represent structured, predictable, user-initiated tasks. A significant fraction involve direct interaction with a web-based admin UI across various enterprise systems (ERP, CRM, HRIS, bespoke tools):

| Category | Typical Share of L1 SR Volume |
|---|---|
| User account management (create, deactivate, reset) | 20–30% |
| Access / permission management via UI | 15–25% |
| Data entry and record updates through forms | 10–20% |
| Configuration and settings changes in UI | 10–15% |
| "How do I do X?" informational queries | 15–20% |
| Reporting / data pull via admin screens | 5–10% |

Aggregating the directly executable UI tasks (user management, access, data entry, config), approximately **40–65% of L1 service requests involve an agent physically interacting with a web application's admin interface** on behalf of the requester.

### 3.4 Translating This to Dollar Impact

Using conservative industry figures for a mid-size enterprise:

| Parameter | Value |
|---|---|
| Total IT budget | $50M |
| Share on KTLO / ASM (40%) | $20M |
| Share attributable to L1 support (35% of ASM) | $7M |
| Share of L1 that is SRs with UI interaction (50%) | **$3.5M** |

> **Conservative estimate: $2.5M–$5M per year in a mid-size enterprise is spent on frontend-driven service request execution that is, in principle, fully automatable with a universal UI agent.**

For large enterprises with $500M+ IT budgets, this scales to **$25M–$50M annually**.

### 3.5 The AI Agent Opportunity

Industry data from organisations piloting AI agents in ITSM contexts shows:

| Metric | Observed Result |
|---|---|
| Reduction in cost-per-ticket | 25–40% |
| Ticket deflection rate (fully automated) | 30–60% |
| Reduction in Mean Time to Resolution (MTTR) | 50–70% |
| Average ROI on AI agent investment | **3.5x** (top quartile: >8x) |
| Overall operational cost reduction in IT support | Up to 30% |
| Large enterprise annual savings (routine workflow automation) | $5M+ |

---

## 4. Benefits of This Multi-Agent System

### 4.1 Operational Benefits

| Benefit | Description |
|---|---|
| **Toil Elimination** | Repetitive L1 SR tasks (user provisioning, data entry, access management) are executed automatically, eliminating the need for a human to manually click through admin UIs. |
| **24/7 Autonomous Operation** | The system operates continuously without fatigue, shift constraints, or time-zone limitations. |
| **Consistent Execution** | Every action follows documented SOPs retrieved from the knowledge base — no deviation, no missed steps, no human error. |
| **Reduced MTTR** | Service requests are fulfilled within seconds of submission rather than hours or days awaiting human bandwidth. |
| **Audit Trail** | Every action, DOM interaction, and verification step is logged and auditable. |

### 4.2 Strategic Benefits

| Benefit | Description |
|---|---|
| **Human Capital Reallocation** | Engineers freed from mechanical execution can focus on incident analysis, process improvement, and system reliability. |
| **Scalability Without Linear Headcount Growth** | The system scales horizontally to handle increased ticket volume without proportionally increasing headcount. |
| **Knowledge Capture** | The RAG knowledge base becomes a living repository of SOPs, runbooks, and procedural knowledge — improving organisational memory. |
| **Application-Agnostic Scalability** | Because the agent interacts via the UI (not APIs), it works against any web application without requiring custom integration development. This allows IT to rapidly onboard new platforms for automation simply by uploading SOP documents. |
| **Reduced Training Overhead** | New team members do not need deep application knowledge across dozens of systems; the AI handles execution while humans handle exceptions. |

---

## 5. System Architecture — POC Design

### 5.1 High-Level Architecture

```
+------------------------------------------------------------------+
|                  FRONTEND  (React / Vite)                        |
|  Chat UI | Debug Pane | Token/Cost Meter | Doc Upload | Settings |
+------------------------------|-----------------------------------+
                               | HTTP / SSE
+------------------------------|-----------------------------------+
|                   API LAYER  (FastAPI)                           |
|   POST /rag/query -- Streaming SSE                               |
|   GET/POST /api/settings -- Dynamic config                       |
|   GET/POST /api/documents -- Document management                 |
+------------------------------|-----------------------------------+
                               |
+------------------------------|-----------------------------------+
|                  ORCHESTRATOR                                    |
|  1. Receive query + conversation history                         |
|  2. Load dynamic settings (LLM model, embedding model)          |
|  3. Call Intent Classifier --> RAG or ACTION                     |
|  4. Route to pipeline; aggregate token usage                     |
+---------------|------------------------|-------------------------+
                |                        |
    +-----------v---------+  +-----------v----------+
    |     RAG PATH        |  |    ACTION PATH       |
    |                     |  |                      |
    |  Query Rewriter     |  |  RAG Context Lookup  |
    |       |             |  |        |             |
    |  Retriever          |  |  Value Extractor     |
    |  (pgvector)         |  |        |             |
    |       |             |  |  Planner Agent       |
    |  LLM Service        |  |        |             |
    |  (Generate Answer)  |  |  Executor Agent      |
    +-----------|---------+  |  (Playwright)        |
                |            +----------|-----------+
    +-----------v------------------------------v----+
    |           SHARED SERVICES                     |
    |  OpenAI LLM  (configurable model)            |
    |  PostgreSQL + pgvector  (RAG store)          |
    |  Playwright  (headless browser)              |
    |  Settings Service  (dynamic config)          |
    +-----------------------------------------------+
```

### 5.2 Component Descriptions

#### 5.2.1 Frontend — Admin Console (React / Vite)

The human-facing interface for support staff to interact with the AI agent system.

**Key capabilities:**
- **Chat Panel** — Conversational interface supporting multi-turn dialogue. Maintains conversation history and sends it to the backend for context-aware responses.
- **Debug / Print Pane** — Split-pane real-time streaming view of the agent's internal reasoning, orchestration logs, and step-by-step execution output. Invaluable for verifying agent behaviour during POC.
- **Token & Cost Meter** — Per-message and cumulative conversation token counts and LLM cost estimates (prompt tokens, completion tokens, USD cost). Surfaces real-time cost transparency.
- **Document Upload & Management** — Allows admins to ingest new SOPs, runbooks, and procedural documents into the knowledge base without code changes. This is the primary mechanism for onboarding new applications.
- **Settings Panel** — Dynamic configuration for LLM model selection, embedding model, and feature flags (e.g., debug panel visibility). Changes take effect at runtime without server restart.

---

#### 5.2.2 API Layer — FastAPI Backend

Bridges the frontend and agent backend via HTTP and Server-Sent Events.

**Key endpoints:**
- `POST /rag/query` — Accepts a user query + conversation history and returns a **Server-Sent Events (SSE) stream**. Log events are streamed in real-time as the orchestrator runs; the final result is sent as the terminal event.
- `GET/POST /api/settings` — CRUD for dynamic system configuration stored in the database.
- `GET/POST /api/documents` — Document management (list, upload, delete) for the knowledge base.

`asyncio.Queue` is used as an in-process pub/sub channel between the orchestrator's synchronous print output and the async SSE generator — enabling real-time log streaming without polling.

---

#### 5.2.3 Orchestrator

The central routing and coordination layer. Receives every incoming query and decides which pipeline to invoke.

**Responsibilities:**
1. Loads dynamic settings (LLM model, embedding model) from the database at runtime.
2. Calls the Intent Classifier to determine query intent (`RAG` or `ACTION`).
3. Routes to the appropriate pipeline.
4. Captures all `print()` output from sub-agents and streams it to the frontend via the SSE queue.
5. Aggregates token usage across all LLM calls and returns it in the result payload.

---

#### 5.2.4 Intent Classifier

A zero-shot LLM classifier that categorises the user's query into one of two intents:

| Intent | Meaning | Example |
|---|---|---|
| `RAG` | Informational — the user wants knowledge, guidance, or steps explained | *"How do I create a new user account?"* |
| `ACTION` | Execution — the user wants the system to perform a UI task | *"Create user john123 in the HR portal"* |

Uses a small, fast, temperature-0 LLM call. Deliberately biased toward `RAG` on ambiguous inputs to prevent unintended execution actions.

---

#### 5.2.5 Query Rewriter

Improves semantic search recall by expanding the user's raw query before embedding it for vector search. A brief LLM call rewrites the query with synonyms and related terminology, without changing intent.

*Example:*
- Input: `"reset user access"`
- Rewritten: `"reset user account access permissions unlock deactivated account log in issue"`

---

#### 5.2.6 Retriever and RAG Store (PostgreSQL + pgvector)

Retrieves the most semantically relevant knowledge chunks from the document store.

**Process:**
1. The rewritten query is embedded using the configured embedding model (default: `text-embedding-3-small`).
2. A cosine-similarity vector search (`<->` operator) runs against the `chunks` table in PostgreSQL with the pgvector extension.
3. The top-K matching chunks and their source document names are returned.

For POC scale, PostgreSQL + pgvector provides sufficient performance with zero additional infrastructure. At production scale, this migrates to a dedicated vector store (Pinecone, Weaviate).

---

#### 5.2.7 LLM Service — RAG Answer Generator

Given the user's query, conversation history, and retrieved context chunks, generates a final natural-language answer.

- Conversation history is injected into the message list to support multi-turn, context-aware responses.
- The system prompt instructs the LLM to merge all relevant context sections — preventing it from copying a single chunk.
- Returns `NO_RELEVANT_CONTEXT` as a sentinel if no useful information exists, triggering a graceful "I don't know" response.
- Token usage (`prompt_tokens`, `completion_tokens`, `total_tokens`) is captured from the OpenAI response object and returned for cost accounting.

---

#### 5.2.8 Value Extractor

For `ACTION` intent queries, extracts the structured entity data needed to ground the action plan.

**Example output:**
```json
{
  "entity_type": "user",
  "identifier": "john123",
  "attributes": {
    "email": "john@example.com",
    "role": "admin"
  }
}
```

**Critical rule:** The `identifier` field must be the *exact* value provided by the user. The LLM is explicitly instructed not to substitute or infer values from context — preventing hallucination of entity identifiers.

---

#### 5.2.9 Planner Agent

Converts the user's action request into a minimal, ordered list of atomic, executable UI steps — drawing strictly from RAG context.

**Key constraints enforced:**
- Each step represents exactly one UI action (no compound steps).
- Steps are grounded exclusively in the retrieved SOP context.
- The exact `identifier` from Value Extractor must appear verbatim in each relevant step.
- No "wait", "review", or "check visually" steps — only deterministic, executable actions.
- Actions on repeated UI elements (Delete, Edit buttons in tables) are contextualised to the specific entity.

**Example output:**
```json
[
  "Navigate to http://app.example.com/admin/users",
  "Verify user john123 does not exist",
  "Click Create New User",
  "Enter username john123",
  "Enter email john@example.com",
  "Click Save",
  "Verify user john123 exists"
]
```

---

#### 5.2.10 Executor Agent

The physical execution engine. Translates each planned step into a browser action and drives the target web application.

**Execution loop:**
1. Reads the live DOM of the current browser page.
2. Passes the step description + DOM to the LLM Interpreter to generate a Playwright action JSON.
3. Executes the action against the headless browser.
4. Detects success by monitoring DOM change (content diff or URL change) post-action.
5. Supports configurable retry logic (default: 2 retries before marking a step failed).
6. Activates skip mode if a pre-check verification reveals the target state already exists (idempotency guard).

**Supported actions:**

| Action | Description |
|---|---|
| `click` | Click a UI element by Playwright selector |
| `fill` | Type text into an input field |
| `navigate` | Navigate the browser to a URL |
| `verify_present` | Assert text is visible on the page |
| `verify_not_present` | Assert text is absent from the page |
| `error` | Explicit abort if target element not found |

---

#### 5.2.11 LLM Interpreter

Translates each natural-language step into one structured Playwright action JSON — using the live DOM as grounding context.

**Key rules enforced:**
- Returns exactly one JSON object per call — never a list or compound action.
- Strict target matching: if the instruction references "john123" but it is not in the DOM, returns `{"action": "error"}` — never guesses a substitute.
- Selector priority: `data-testid` attributes > placeholder > visible text on interactive elements.
- For repeated elements (Delete/Edit buttons in tables), uses Playwright relational selectors: `tr:has-text("john123") >> button:has-text("Delete")`.

---

#### 5.2.12 Browser Tools (Playwright)

Manages the headless Chromium browser session used for UI interaction. A singleton pattern ensures a single browser instance is shared across requests to avoid startup latency.

**Capabilities:** Full DOM extraction, DOM snapshots for change detection, click/fill/navigate actions, inner text extraction for verification steps.

---

#### 5.2.13 Settings Service and Dynamic Configuration

Allows runtime reconfiguration of the AI system without redeployment.

**Configurable parameters (stored in DB):**
- `llm_model` — Which OpenAI model to use (e.g., `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`)
- `embedding_model` — Embedding model for RAG
- `show_debug_panel` — Feature flag for the debug pane

This enables A/B testing of models, cost-quality tradeoff tuning, and feature rollout — all from the admin UI, with no server restarts.

---

### 5.3 Request Data Flow Summary

```
User types natural-language query
  |
  +--> Chat UI --> POST /rag/query  (query + conversation history)
                         |
                 Orchestrator
                    |
                    +-- Intent Classifier --> "RAG" or "ACTION"
                    |
                    +-- [RAG path]
                    |     QueryRewriter --> expanded query
                    |     Retriever (pgvector) --> top-K chunks
                    |     LLMService.generate_answer() --> answer + usage
                    |     Return {answer, sources, usage}
                    |
                    +-- [ACTION path]
                          RAG retrieval --> SOP context (any application SOP)
                          ValueExtractor --> {entity_type, identifier, attributes}
                          PlannerAgent --> ["step1", "step2", ...]
                          Executor loop:
                            DOM read
                              --> LLMInterpreter --> Playwright action JSON
                              --> Execute in browser
                              --> DOM change verification
                          LLMService.summarize_execution() --> summary + usage
                          Return {answer, plan, execution_log, usage}
                    |
              SSE stream:
                    log events (real-time, streamed line-by-line)
                    result event (final payload)
                    |
              Chat UI renders:
                    answer text (markdown)
                    source document badges
                    token count (input / output / total)
                    LLM cost (current exchange + conversation total)
```

---

## 6. Technology Stack (POC)

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React + Vite | Fast dev iteration, hot reload, component model |
| Styling | Vanilla CSS | Full control, no framework overhead |
| API Server | FastAPI + Python | Async-native, SSE streaming, Pydantic validation |
| LLM Provider | OpenAI GPT (configurable) | Best-in-class reasoning for agent tasks |
| Embedding | text-embedding-3-small | Cost-effective, high-quality semantic search |
| Vector Store | PostgreSQL + pgvector | Zero additional infra for POC |
| Browser Automation | Playwright (Chromium) | Battle-tested, supports modern SPAs universally |
| Database | PostgreSQL | Unified store for RAG chunks, settings, documents |
| Containerisation | Docker Compose | Local dev environment parity |
| Tracing | OpenAI Agents SDK | LLM call visibility and trace inspection |

---

## 7. Production Readiness Considerations

Moving from a POC to an enterprise-grade platform requires addressing the following dimensions:

### 7.1 Reliability and Resilience

| Concern | POC State | Production Requirement |
|---|---|---|
| Browser session management | Single shared Playwright session | Per-session browser isolation; session pooling; crash recovery |
| Error handling | Basic retry with max attempts | Circuit breakers; dead-letter queues; human escalation triggers |
| LLM API failures | Exceptions propagate | Retry with exponential backoff; fallback models; graceful degradation |
| Concurrent requests | Sequential (single-threaded browser) | Parallel execution with worker pool; queue-based job dispatch |
| Execution state | In-memory / per-request | Persistent execution state in DB; resumable workflows |

### 7.2 Security

| Concern | Production Requirement |
|---|---|
| Browser isolation | Each execution in an isolated containerised browser to prevent cross-session contamination |
| LLM prompt injection | Input sanitisation; context isolation; output schema validation before execution |
| Credential management | Never expose admin credentials in logs or prompts; use HashiCorp Vault or equivalent |
| Access control | RBAC on the admin UI; full audit logging of every action and every actor |
| PII / data governance | Ensure sensitive data in queries/responses is not persisted in raw LLM call logs |

### 7.3 Scalability

| Concern | Production Requirement |
|---|---|
| Throughput | Kubernetes-based horizontal scaling of executor worker pods |
| Vector search | Migrate from pgvector to Pinecone / Weaviate for millions of chunks |
| LLM cost | Per-request cost budgets; caching of common RAG responses; smaller models for classification tasks |
| Queue system | RabbitMQ or Kafka for async job dispatch with reliable at-least-once delivery |

### 7.4 Observability

| Requirement | Recommended Tooling |
|---|---|
| Structured logging | OpenTelemetry -> Datadog / Elastic |
| LLM call tracing | LangSmith or custom OpenTelemetry span instrumentation |
| Per-request cost tracking | Already in POC; persist to time-series DB for dashboarding |
| Execution audit trail | Immutable log of every planned step, interpreted action, and DOM verification result |
| Alerting | PagerDuty / OpsGenie for execution failure rates above SLA threshold |

### 7.5 Multi-Tenancy

For a platform product supporting multiple disparate applications:
- Tenant/App-isolated knowledge bases (separate pgvector namespaces or Pinecone indices)
- Per-tenant LLM model configuration and monthly cost budgets
- Tenant-scoped browser sessions with session isolation
- SSO and SAML integration

### 7.6 Human-in-the-Loop (HITL)

Production deployments should include graduated guardrails:
- **Confidence threshold**: If the planner or interpreter confidence is below a configured threshold, pause and request human confirmation before proceeding.
- **High-risk action review**: Destructive operations (delete, deactivate, bulk changes) require explicit human approval in the UI before execution.
- **Escalation workflow**: Failed executions auto-create a ticket in the ITSM system and route to a human agent with full execution context attached.

---

## 8. Evolution to a Production Platform — LangGraph, LangChain, MCP, and A2A

### 8.1 Why Rewrite?

The POC has several architectural limitations that need to be addressed at production scale:

| Limitation | Impact |
|---|---|
| No formal state machine | Workflow branching, retries, and human-in-the-loop are ad hoc and hard to extend |
| No inter-agent communication standard | Adding a new specialised agent requires tight internal coupling |
| No standardised tool interface | Each tool (browser, search, DB) is directly integrated — hard to extend or swap |
| No checkpointing | Long-running executions cannot be resumed if interrupted mid-flight |
| Single LLM provider coupling | Swapping providers requires widespread code changes across all services |

### 8.2 The Target Architecture Stack

The production architecture maps cleanly to three industry-standard layers, each with a clear role:

```
+--------------------------------------------------------------+
|                    A2A PROTOCOL LAYER                        |
|  Agent-to-Agent communication between independent agent      |
|  microservices. Each agent exposes an A2A Agent Card.       |
+--------------------------------------------------------------+
|                  LANGGRAPH ORCHESTRATION                     |
|  StateGraph defines workflow nodes, routing edges,          |
|  checkpointing, and human-in-the-loop pauses                |
+--------------------------------------------------------------+
|                   MCP TOOL / CONTEXT LAYER                  |
|  Every tool (browser, RAG, DB, APIs) is an MCP server.     |
|  Agents discover and invoke tools via standard interface.   |
+--------------------------------------------------------------+
```

| Layer | Primary Function | Analogy |
|---|---|---|
| **LangGraph** | Orchestrates state, workflow logic, routing, and checkpointing | The "Brain" |
| **MCP** | Standardises connection to tools, data sources, and external context | The "Hands" |
| **A2A** | Enables peer-to-peer communication between independent agent services | The "Network" |

### 8.3 LangGraph — Orchestration Layer

Replaces the custom `orchestrator.py` with a formally modelled StateGraph:

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)

graph.add_node("intent_classifier", intent_classifier_node)
graph.add_node("rag_pipeline",      rag_pipeline_node)
graph.add_node("value_extractor",   value_extractor_node)
graph.add_node("planner",           planner_node)
graph.add_node("executor",          executor_node)
graph.add_node("human_review",      human_review_node)
graph.add_node("summariser",        summariser_node)

graph.add_conditional_edges("intent_classifier", route_intent, {
    "RAG":    "rag_pipeline",
    "ACTION": "value_extractor"
})
graph.add_edge("value_extractor", "planner")
graph.add_conditional_edges("planner", check_risk_level, {
    "low":  "executor",
    "high": "human_review"
})
graph.add_edge("executor",   "summariser")
graph.add_edge("summariser", END)
```

**Production benefits:**
- Every workflow state is explicitly modelled, logged, and traceable end-to-end
- Native **checkpointing** — long multi-step executions survive crashes and can be resumed from the last successful checkpoint
- **Human-in-the-loop** is a first-class graph edge, not a special-case workaround
- **Parallel branches** — the planner can dispatch independent sub-tasks concurrently using the `Send` API
- **LangSmith** integration provides full execution replay, step-level timing, and token accounting

### 8.4 Model Context Protocol (MCP) — Tool Layer

Each tool becomes a self-contained, independently deployable **MCP Server**:

| MCP Server | Exposes | Replaces |
|---|---|---|
| `browser-mcp-server` | `navigate`, `click`, `fill`, `get_dom`, `screenshot` | `browser_tools.py` + direct Playwright calls |
| `rag-mcp-server` | `search_knowledge_base`, `ingest_document` | `retriever.py` + pgvector calls |
| `settings-mcp-server` | `get_settings`, `update_settings` | `settings_service.py` |
| `itsm-mcp-server` | `create_ticket`, `update_ticket`, `escalate` | **New** — ITSM integration (ServiceNow, Jira) |
| `audit-mcp-server` | `log_action`, `get_execution_history` | **New** — immutable audit trail |

```python
# Agent discovers and calls tools at runtime without hardcoded imports
from langchain_mcp_adapters import MCPToolkit

toolkit = MCPToolkit(server_url="http://browser-mcp-server:8001")
tools = await toolkit.get_tools()
# Returns: [navigate_tool, click_tool, fill_tool, get_dom_tool, ...]
```

**Production benefits:**
- Tools are independently deployable, testable, versioned, and replaceable
- New application connectors (Salesforce, SAP, Workday, bespoke internal apps) are added as new MCP servers without touching agent code
- Standard interface means any LangChain / LangGraph agent can use any MCP tool
- Each tool enforces its own rate limits, authentication, and access control

### 8.5 Agent-to-Agent Protocol (A2A) — Communication Layer

Each major agent becomes an autonomous **A2A Agent Service** deployed independently and communicating over standard HTTP:

```
+------------------+   A2A    +--------------------+
|  Orchestrator    |<-------->|  Planner Agent     |
|  (LangGraph)     |          |  Service           |
+---------|--------+          +--------------------+
          | A2A
          v
+------------------+   A2A    +--------------------+
|  Executor Agent  |<-------->|  Verification      |
|  Service         |          |  Agent Service     |
+------------------+          +--------------------+
          |
          | A2A (3rd party)
          v
+------------------+
|  Platform-Native |
|  Agent (Vendor)  |
+------------------+
```

Each A2A service exposes:
- An **Agent Card** (JSON) — machine-readable description of capabilities, inputs/outputs, authentication, and SLA
- A `tasks/send` endpoint — to receive delegated work items
- A `tasks/get` endpoint — to poll for async task completion

**Production benefits:**
- Agents can be written in **different languages or frameworks** and still interoperate via the standard protocol
- **Independent scaling** — the executor can scale to 50 replicas independently of the planner (3 replicas)
- **Independent deployment** — upgrade the planner without touching or redeploying the executor
- **Ecosystem Extensibility** — third-party specialist agents (a validated SAP-native AI, an HR desk agent) can participate in the workflow via A2A with no integration code

### 8.6 Recommended Production Technology Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph (StateGraph + PostgreSQL checkpointer) |
| Agent Framework | LangChain (tool calling, LCEL, memory) |
| Tool Connectivity | MCP Servers (FastMCP or Anthropic MCP SDK) |
| Inter-Agent Protocol | Google A2A (Agent-to-Agent) |
| LLM Provider | OpenAI / Anthropic / Google Gemini (provider-agnostic via LangChain) |
| Embedding | LangChain embeddings abstraction |
| Vector Store | Pinecone or Weaviate (production scale) |
| Browser Automation | Playwright running inside MCP Server container |
| Async Queue | Apache Kafka or RabbitMQ |
| State Persistence | PostgreSQL (workflow checkpointing) + Redis (response cache) |
| Observability | LangSmith + OpenTelemetry + Datadog |
| Container Orchestration | Kubernetes with HPA for executor pods |
| Authentication | OAuth2 / SAML 2.0 + RBAC |
| Secrets Management | HashiCorp Vault |
| CI/CD | GitHub Actions + ArgoCD |

### 8.7 Phased Migration Roadmap from POC to Production

```
Phase 1 -- Harden POC                       [0 -> 3 months]
  - Add HITL approval gates for destructive actions
  - Add robust error handling, retry queues, operational alerting
  - Add structured audit logging and OpenTelemetry instrumentation
  - Browser session pooling with isolation between requests

Phase 2 -- LangGraph Migration              [3 -> 6 months]
  - Rewrite orchestrator as LangGraph StateGraph
  - Integrate LangSmith for workflow observability
  - Add checkpointing (PostgreSQL LangGraph checkpointer)
  - Model HITL as a first-class graph pause node

Phase 3 -- MCP Tool Extraction              [6 -> 9 months]
  - Wrap browser, RAG, settings into standalone MCP servers
  - Decouple all agents from direct tool implementations
  - Add MCP-based connectors for first target applications
  - Introduce per-tool rate-limiting and auth policies

Phase 4 -- A2A Decomposition               [9 -> 12 months]
  - Deploy Planner, Executor, Verifier as A2A microservices
  - Implement Agent Card discovery and routing
  - Enable third-party specialist agents via A2A
  - Kubernetes HPA for executor pods based on queue depth

Phase 5 -- Universal Platform Product      [12 -> 18 months]
  - Full multi-app multi-tenancy: isolated namespaces, RBAC, SSO
  - Self-service knowledge base management (universal SOP ingestion)
  - SLA dashboards, per-tenant cost analytics, ROI reporting
  - MCP connector marketplace for enterprise application adapters
  - SLA-backed execution guarantee with human escalation SLA
```

---

## 9. Summary ROI Case

| Scenario | Conservative | Moderate | Optimistic |
|---|---|---|---|
| Enterprise IT Budget | $50M | $100M | $200M |
| ASM Spend (40%) | $20M | $40M | $80M |
| L1 SR with UI interaction (17.5% of ASM) | $3.5M | $7M | $14M |
| Automation coverage achievable (50% of eligible SRs across apps) | $1.75M | $3.5M | $7M |
| Cost reduction realised (30%) | **$525K/yr** | **$1.05M/yr** | **$2.1M/yr** |
| Platform investment estimate | $300K | $600K | $1.2M |
| **Year 1 Net Benefit** | **$225K** | **$450K** | **$900K** |
| **3-Year Cumulative Benefit** | **$1.3M** | **$2.6M** | **$5.1M** |

*Note: These figures represent recoverable spend on L1 UI-based service requests only. Indirect benefits — MTTR reduction, engineer reallocation value, error rate reduction, reduced onboarding and training costs across multiple business portals — are additive to these numbers and often comparable in magnitude.*

---

## 10. Conclusion

The Universal UI Automation AI Agents system represents an early but technically sound proof-of-concept for a class of solutions that will fundamentally change how IT service management organisations deliver L1 and L2 support across their entire software portfolio.

The key insight is that a large, measurable, and addressable portion of ASM expenditure globally — **frontend service request execution** — is uniquely amenable to automation via the powerful combination of:

1. **RAG** to ground every action in verified, organisation-specific documentation for any given application.
2. **LLM planning** to convert natural-language intent into deterministic, auditable steps.
3. **Browser automation** to physically execute those steps against any web application without requiring expensive custom API integration development.

The POC demonstrates that this is technically viable today with off-the-shelf LLMs and open-source tooling. The path to a production platform is clear, well-aligned with emerging industry standards (LangGraph, MCP, A2A), and delivers measurable ROI within the first year for organisations of meaningful scale. 

By building a system that natively understands UIs rather than APIs, the organisation secures a highly extensible automation workforce that can operate any existing or future software platform out of the box.

Most importantly, beyond the cost numbers, this system enables a qualitative shift in how human expertise is deployed — from repetitive, mechanical execution toward genuinely high-value problem-solving, complex incident analysis, knowledge creation, and process innovation across the enterprise.

---

*Document prepared for internal review. All benchmark figures are derived from published industry research (Gartner, ITSM industry surveys, Ivanti, AI vendor case studies). Specific financial projections should be validated against organisation-specific ticket volumes, labour cost data, and actual ITSM categorisation reports.*
