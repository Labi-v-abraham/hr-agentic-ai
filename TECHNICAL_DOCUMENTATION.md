# HR Agentic AI — Complete Technical Documentation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Architecture](#3-architecture)
4. [Project Folder Structure](#4-project-folder-structure)
5. [Workflow — How a Query is Processed](#5-workflow--how-a-query-is-processed)
6. [Agent System (LangGraph)](#6-agent-system-langgraph)
7. [RAG Pipeline (Retrieval-Augmented Generation)](#7-rag-pipeline-retrieval-augmented-generation)
8. [Authentication & Authorization (RBAC)](#8-authentication--authorization-rbac)
9. [Database Schema (Supabase / PostgreSQL)](#9-database-schema-supabase--postgresql)
10. [Prompt Template System (Jinja2)](#10-prompt-template-system-jinja2)
11. [Dependency Injection Container](#11-dependency-injection-container)
12. [Pydantic Models (Structured LLM Output)](#12-pydantic-models-structured-llm-output)
13. [Frontend Pages (Streamlit)](#13-frontend-pages-streamlit)
14. [Environment Variables](#14-environment-variables)
15. [Key Python Dependencies](#15-key-python-dependencies)

---

## 1. Project Overview

**HR Agentic AI** is an intelligent, multi-agent HR assistant that uses autonomous AI agents to handle HR tasks through natural language. The system routes user queries through a **Supervisor-Worker** pattern built with LangGraph, where a supervisor agent detects intent and delegates work to specialized agents:

- **Resume Screening** — AI-powered evaluation with match scores, scorecards, and interview questions
- **HR Policy Q&A** — RAG-powered answers using uploaded employee handbooks
- **Interview Email Drafting** — Auto-generates professional interview invitation emails
- **Onboarding Tracking** — Create, update, and view onboarding checklists
- **Leave Management** — Apply for leave, check status, approve/reject requests
- **General Assistant** — Handles casual conversation

All of this is wrapped in a Streamlit web app with role-based access control (RBAC), Supabase authentication, and persistent chat history.

---

## 2. Technology Stack

### 2.1 Core Frameworks

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | Streamlit | 1.59.2 | Interactive web UI (chat, file uploads, dashboards) |
| **Agent Orchestration** | LangGraph | 1.2.9 | State machine for multi-agent workflow routing |
| **Agent Framework** | LangChain | 1.3.14 | LLM abstractions, chains, structured output, retrievers |
| **Data Validation** | Pydantic | 2.13.4 | Structured LLM output schemas + data models |

### 2.2 LLM Providers

| Provider | Model | Role | Temperature |
|---|---|---|---|
| **Google Gemini** | `gemini-2.5-flash` | Primary LLM | 0 |
| **Groq** | `llama-3.3-70b-versatile` | Fallback LLM | 0 |

The system uses LangChain's `.with_fallbacks()` mechanism. If Gemini fails (API error, rate limit), it automatically falls back to Groq:

```python
primary = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
fallback = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm = primary.with_fallbacks([fallback])
```

### 2.3 Vector Database & Embeddings

| Component | Technology | Details |
|---|---|---|
| **Vector Store** | ChromaDB 1.5.9 | Persistent local storage in `vectorstore/` directory |
| **Embeddings** | Google `gemini-embedding-2` | Via `GoogleGenerativeAIEmbeddings` |
| **Retrieval** | MMR (Maximal Marginal Relevance) | `k=10`, `fetch_k=30` for diversity |
| **Text Splitter** | `RecursiveCharacterTextSplitter` | `chunk_size=1000`, `chunk_overlap=200` |
| **PDF Parser** | `PyPDFLoader` (pypdf) | Extracts text from uploaded PDFs |

### 2.4 Backend & Database

| Component | Technology | Purpose |
|---|---|---|
| **Database** | Supabase (PostgreSQL) | User profiles, documents metadata, chat history, evaluations, leave requests, onboarding checklists |
| **Authentication** | Supabase Auth | Email/password login with JWT tokens |
| **File Storage** | Supabase Storage | PDF document storage in `hr_documents` bucket |
| **Row-Level Security** | PostgreSQL RLS | Enforced on `documents`, `chat_history`, `audit_logs` tables |

### 2.5 Prompt Management

| Component | Technology | Purpose |
|---|---|---|
| **Template Engine** | Jinja2 3.1.6 | Externalized LLM prompts in `.j2` template files |
| **Loader** | Custom `render_prompt()` | Renders templates with variable substitution |

---

## 3. Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                           │
│   ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│   │  Login   │ │  💬 Chat     │ │ 📚 Knowledge │ │ ⚙️ Admin     │  │
│   │  Page    │ │  Interface   │ │    Base Mgmt  │ │  Dashboard   │  │
│   └──────────┘ └──────┬───────┘ └──────┬───────┘ └──────────────┘  │
└────────────────────────┼───────────────┼───────────────────────────┘
                         │               │
    ┌────────────────────▼───────────────▼──────────────────────┐
    │              DEPENDENCY INJECTION CONTAINER               │
    │                                                           │
    │  Backend (cached):   │  Frontend (per-reload):            │
    │  • SupabaseService   │  • SessionManager                  │
    │  • ProfileRepository │  • AuthService                     │
    │  • ChatRepository    │  • AuthorizationService            │
    │  • UserService       │                                    │
    │  • KnowledgeBaseSvc  │                                    │
    └──────────┬───────────┴────────────────────────────────────┘
               │
    ┌──────────▼──────────────────────────────────────────────┐
    │                    LANGGRAPH AGENT SYSTEM                │
    │                                                         │
    │  ┌─────────────┐    ┌───────────────────────────────┐   │
    │  │  Supervisor  │───▶│  Intent Router (LLM+Keyword) │   │
    │  └─────────────┘    └──────────────┬────────────────┘   │
    │                                    │                    │
    │  ┌─────────────────────────────────┼──────────────┐     │
    │  │                │               │              │     │
    │  ▼                ▼               ▼              ▼     │
    │ Candidate      HR Policy     Onboarding       Leave    │
    │ Evaluator      Specialist    Specialist      Specialist │
    │  │                │               │              │     │
    │  ▼                │               │              │     │
    │ Supervisor        │               │              │     │
    │ Decision          │               │              │     │
    │  │                │               │              │     │
    │  ▼                │               │              │     │
    │ Interview         │               │              │     │
    │ Email Gen         │               │              │     │
    │  │                │               │              │     │
    │  └────────────────┼───────────────┼──────────────┘     │
    │                   ▼               ▼                    │
    │              Final Response                             │
    └──────────┬─────────────────────────┬───────────────────┘
               │                         │
    ┌──────────▼──────────┐   ┌──────────▼──────────┐
    │  ChromaDB           │   │  Supabase            │
    │  (Vector Store)     │   │  (PostgreSQL +       │
    │  • Document chunks  │   │   Auth + Storage)    │
    │  • Embeddings       │   │  • Profiles          │
    │  • Similarity search│   │  • Documents         │
    └─────────────────────┘   │  • Evaluations       │
                              │  • Chat History      │
                              │  • Leave Requests    │
                              │  • Onboarding Lists  │
                              │  • Knowledge Bases   │
                              └─────────────────────┘
```

### 3.2 Design Patterns Used

| Pattern | Where | Description |
|---|---|---|
| **Supervisor-Worker** | LangGraph workflow | Supervisor detects intent, routes to specialist agent nodes |
| **Dependency Injection** | `app/utils/dependencies.py` | Centralized service construction, cached backend + per-reload frontend |
| **Singleton** | `SupabaseService` | Single shared database connection across the app |
| **Repository Pattern** | `ProfileRepository`, `ChatRepository` | Database access abstraction layer |
| **Template Method** | Jinja2 prompt templates | LLM prompts externalized from Python logic |
| **Structured Output** | Pydantic + LangChain `.with_structured_output()` | LLM forced to return validated JSON matching Pydantic schemas |
| **Strategy (Fallback)** | `primary.with_fallbacks([fallback])` | Automatic LLM provider fallback |
| **State Machine** | LangGraph `StateGraph` | Directed graph with conditional edges for agent routing |

---

## 4. Project Folder Structure

```
hr-agentic-ai/
│
├── main.py                              # App entry point: page config, navigation, auth guard
├── requirements.txt                     # All Python dependencies (pinned versions)
├── setup_supabase.py                    # Seeds the default admin user into Supabase
├── .env                                 # Environment variables (API keys, Supabase config)
├── .gitignore                           # Ignores .env, __pycache__/, *.pyc, vectorstore/
│
├── data/                                # Sample data files for testing
│   ├── employee_handbook.pdf            # Sample Employee Handbook
│   └── software engineer.pdf            # Sample resume
│
├── database/                            # Database setup files
│   ├── __init__.py
│   └── schema.sql                       # Full Supabase PostgreSQL schema (290 lines)
│                                        #   → Tables, indexes, triggers, RLS policies,
│                                        #   → Security-definer functions, auto-profile creation
│
├── vectorstore/                         # ChromaDB persistent storage (auto-generated, gitignored)
├── uploads/                             # Temporary uploaded file storage
│
├── app/                                 # Main application package
│   │
│   ├── agents/                          # AI Agent System
│   │   ├── graph/                       # LangGraph State Machine
│   │   │   ├── workflow.py              # Graph builder: nodes, edges, conditional routing
│   │   │   ├── node.py                  # All specialist agent functions (931 lines):
│   │   │   │                            #   → candidate_evaluator, interview_email_generator,
│   │   │   │                            #   → hr_policy_specialist, general_assistant,
│   │   │   │                            #   → onboarding_specialist, leave_specialist,
│   │   │   │                            #   → supervisor_decision, final_response
│   │   │   ├── router.py               # Intent detection (LLM-based + keyword fallback)
│   │   │   └── state.py                # AgentState TypedDict (shared state schema)
│   │   │
│   │   └── rag/                         # Retrieval-Augmented Generation
│   │       ├── build_vectorstore.py     # Legacy adapter → delegates to KnowledgeBaseService
│   │       ├── retriever.py             # ChromaDB retriever: embeddings, vectorstore, MMR search
│   │       ├── vectorstore.py           # Utility: direct Chroma.from_documents
│   │       └── loader.py               # PDF loading + text chunking (RecursiveCharacterTextSplitter)
│   │
│   ├── auth/                            # Authentication & Authorization
│   │   ├── auth_service.py              # Login/logout via Supabase Auth (email + password)
│   │   ├── authorization.py             # RBAC middleware (require_admin, require_manager, can_*)
│   │   └── session_manager.py           # Streamlit session state management (no cookies)
│   │
│   ├── database/                        # Data Access Layer
│   │   ├── supabase_service.py          # Singleton Supabase client (anon + admin/service-role)
│   │   ├── profile_repository.py        # CRUD for profiles table
│   │   └── chat_repository.py           # CRUD for chat_history table
│   │
│   ├── models/                          # Pydantic Data Models
│   │   ├── models.py                    # CandidateEvaluation, ScorecardItem, LeaveExtraction
│   │   └── user.py                      # Profile, Role (enum), UserStatus (enum)
│   │
│   ├── pages/                           # Streamlit UI Pages
│   │   ├── login.py                     # Login form (email + password)
│   │   ├── chat.py                      # Main chat interface (1109 lines):
│   │   │                                #   → Single/bulk resume evaluation, PDF upload,
│   │   │                                #   → Auto-detect document type & role, chat sessions,
│   │   │                                #   → Execution log, recruitment dashboard
│   │   ├── knowledge_base.py            # Upload & manage documents per knowledge base
│   │   ├── knowledge_base_types.py      # CRUD for knowledge base categories (Admin only)
│   │   └── admin.py                     # User management: view, create, change roles
│   │
│   ├── services/                        # Business Logic Layer
│   │   ├── knowledge_base.py            # Full document lifecycle:
│   │   │                                #   → Upload to Supabase Storage → metadata to Postgres
│   │   │                                #   → Extract text → chunk → embed into ChromaDB
│   │   │                                #   → Document versioning, reindexing, soft-delete
│   │   └── user_service.py              # Create users (Admin API or signup), role changes
│   │
│   ├── prompts/                         # LLM Prompt Template System
│   │   ├── __init__.py
│   │   ├── loader.py                    # Jinja2 Environment + render_prompt() function
│   │   └── templates/                   # 8 externalized .j2 prompt templates:
│   │       ├── resume_evaluation.j2     # Candidate evaluator prompt
│   │       ├── bulk_resume_evaluation.j2 # Bulk resume screening prompt
│   │       ├── interview_email.j2       # Interview invitation email prompt
│   │       ├── hr_policy.j2             # RAG-powered policy Q&A prompt
│   │       ├── leave_extraction.j2      # Leave request detail extraction
│   │       ├── intent_classification.j2 # User intent classification
│   │       ├── document_classification.j2 # PDF type detection
│   │       └── role_detection.j2        # Resume-to-role matching
│   │
│   ├── utils/                           # Utilities
│   │   ├── config.py                    # LLM initialization (Gemini + Groq fallback)
│   │   └── dependencies.py             # Dependency injection container
│   │
│   └── components/                      # Reusable Streamlit UI components (empty)
│
└── test_*.py                            # Various test/debug scripts (DB, LLM, models, schema)
```

---

## 5. Workflow — How a Query is Processed

### 5.1 End-to-End Flow

```
User types a query in the Chat interface
            │
            ▼
  ┌──────────────────────┐
  │  1. CHAT PAGE        │  → Constructs AgentState dict with:
  │     (chat.py)        │     query, resume_text, current_role,
  │                      │     active_kbs, execution_log: []
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  2. LANGGRAPH        │  → get_graph().invoke(state)
  │     STATE MACHINE    │     Runs the compiled StateGraph
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  3. SUPERVISOR       │  → Calls detect_intent(query)
  │     (workflow.py)    │     Uses LLM + keyword fallback
  │                      │     Sets state["intent"]
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  4. ROUTE INTENT     │  → Conditional edge based on intent:
  │     (workflow.py)    │     resume/recruitment → candidate_evaluator
  │                      │     policy → hr_policy_specialist
  │                      │     email → interview_email_generator
  │                      │     onboarding → onboarding_specialist
  │                      │     leave → leave_specialist
  │                      │     general → general_assistant
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  5. SPECIALIST       │  → Executes the appropriate agent
  │     AGENT NODE       │     Calls LLM with rendered prompt
  │     (node.py)        │     Updates AgentState with results
  └──────────┬───────────┘
             │
             ▼ (if resume/recruitment)
  ┌──────────────────────┐
  │  6. SUPERVISOR       │  → If match_percentage >= 80%:
  │     DECISION         │     route to interview_email
  │     (node.py)        │     else: route to final
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  7. FINAL RESPONSE   │  → Compiles response from state fields
  │     (node.py)        │     Adds RAG confidence badges
  │                      │     Saves evaluation to Supabase
  │                      │     Sets state["final_answer"]
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  8. DISPLAY          │  → Chat page renders final_answer
  │     (chat.py)        │     Shows evaluation dashboard
  │                      │     Shows execution log
  │                      │     Saves to chat_history
  └──────────────────────┘
```

### 5.2 Intent Detection Strategy

The system uses a **two-tier intent classification**:

**Tier 1 — LLM-Based (Primary)**:
- The query is sent to the LLM with a structured output schema (`IntentClassification`)
- The LLM returns one of: `recruitment`, `resume`, `email`, `policy`, `onboarding`, `leave`, `general`

**Tier 2 — Keyword Fallback**:
If the LLM fails or returns an invalid intent, keyword-based pattern matching kicks in:

```
"resume" + ("interview" | "email" | "invite")  →  recruitment
"resume"                                        →  resume
"email" | "offer" | "welcome" | "rejection"    →  email
"apply for leave" | "request time off" | ...    →  leave
"leave" | "policy" | "benefits" | "holiday"    →  policy
"start onboarding" | "onboarding status" | ... →  onboarding
(everything else)                              →  general
```

---

## 6. Agent System (LangGraph)

### 6.1 State Schema (`AgentState`)

All agents share a single `TypedDict` state that flows through the graph:

```python
class AgentState(TypedDict):
    query: str                        # User's input query
    resume_text: str                  # Extracted resume text (if uploaded)
    intent: str                       # Detected intent from supervisor
    next_node: str                    # Next node (set by supervisor_decision)
    current_role: Optional[str]       # Selected knowledge base / role name
    active_kbs: list[str]             # Active knowledge base IDs
    evaluation_data: dict             # Full CandidateEvaluation as dict
    match_percentage: int             # 0-100 match score
    recommendation: str               # "Selected" | "Rejected" | "Hold"
    analysis: str                     # Executive summary
    suggested_questions: List[str]    # Interview questions
    email: str                        # Generated interview email
    policy: str                       # Policy answer from RAG
    final_answer: str                 # Final compiled response
    execution_log: list[str]          # Agent activity log (displayed in UI)
    onboarding_result: Optional[str]  # Onboarding checklist markdown
    candidate_id: Optional[str]       # DB ID for onboarding lookup
    source_files: Optional[list]      # RAG source filenames
    confidence_badge: Optional[str]   # "🟢 High" | "🟡 Medium" | "🔴 Low"
    knowledge_gap: Optional[bool]     # True if RAG context is insufficient
    leave_result: Optional[str]       # Leave action result markdown
```

### 6.2 Graph Topology

```python
builder = StateGraph(AgentState)

# Nodes (9 total)
builder.add_node("supervisor", supervisor)
builder.add_node("candidate_evaluator", candidate_evaluator)
builder.add_node("supervisor_decision", supervisor_decision)
builder.add_node("interview_email", interview_email_generator)
builder.add_node("policy", hr_policy_specialist)
builder.add_node("general", general_assistant)
builder.add_node("onboarding", onboarding_specialist)
builder.add_node("leave", leave_specialist)
builder.add_node("final", final_response)

# Edges
START → supervisor
supervisor → [conditional: route_intent]
candidate_evaluator → supervisor_decision
supervisor_decision → [conditional: decision_router]
interview_email → final
policy → final
general → final
onboarding → final
leave → final
final → END
```

### 6.3 Agent Descriptions

| Agent | Function | What It Does |
|---|---|---|
| **Supervisor** | `supervisor()` | Calls `detect_intent()`, stores intent in state |
| **Candidate Evaluator** | `candidate_evaluator()` | Retrieves role-specific KB chunks via RAG, evaluates resume with LLM, returns structured `CandidateEvaluation` |
| **Supervisor Decision** | `supervisor_decision()` | If `match_percentage >= 80%` → route to `interview_email`, else → `final` |
| **Interview Email** | `interview_email_generator()` | Generates professional interview invitation with placeholders |
| **HR Policy** | `hr_policy_specialist()` | Retrieves policy chunks from ChromaDB, answers using RAG context |
| **General Assistant** | `general_assistant()` | Passes query directly to LLM (no prompt template, no RAG) |
| **Onboarding** | `onboarding_specialist()` | Three sub-cases: START (seed 5 default tasks), UPDATE (mark task done), STATUS (display checklist) |
| **Leave** | `leave_specialist()` | Four sub-cases: APPLY (LLM extracts dates → insert), STATUS (own requests), PENDING (all pending), APPROVE/REJECT |
| **Final Response** | `final_response()` | Compiles all results, adds RAG badges, saves evaluation to DB |

---

## 7. RAG Pipeline (Retrieval-Augmented Generation)

### 7.1 Document Ingestion Pipeline

```
PDF Upload (via Knowledge Base page)
        │
        ▼
┌─────────────────────────┐
│ 1. Supabase Storage     │  Upload PDF bytes to hr_documents bucket
│    (file storage)       │  Generate unique storage_path
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 2. Postgres Metadata    │  Insert row into documents table
│    (documents table)    │  Status: PROCESSING
│                         │  Link to knowledge_base_id
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 3. PDF Text Extraction  │  PyPDFLoader → raw text
│    (PyPDFLoader)        │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 4. Text Chunking        │  RecursiveCharacterTextSplitter
│                         │  chunk_size=1000, overlap=200
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 5. Embedding            │  Google gemini-embedding-2
│                         │  via GoogleGenerativeAIEmbeddings
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ 6. ChromaDB Upsert      │  Deterministic IDs: {doc_id}_chunk_{i}
│    (vectorstore/)       │  Metadata: knowledge_base_id, filename,
│                         │  document_id, knowledge_base_name
└─────────────────────────┘
```

### 7.2 Retrieval at Query Time

```
User query (policy or resume intent)
        │
        ▼
┌─────────────────────────┐
│ Similarity Search       │  ChromaDB similarity_search_with_score()
│                         │  k=10, filtered by knowledge_base_id
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Confidence Scoring      │  avg_score >= 0.75 → 🟢 High
│                         │  avg_score >= 0.50 → 🟡 Medium
│                         │  avg_score <  0.50 → 🔴 Low
│                         │  No results or <0.4 → ⚠️ Knowledge Gap
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ Context Assembly        │  Join retrieved chunks with metadata
│                         │  Pass as context to LLM prompt
└─────────────────────────┘
```

### 7.3 Document Versioning

When a document with the same name is re-uploaded to the same knowledge base:
1. The new document gets `version_number = prev_version + 1` and `parent_document_id` pointing to the old one
2. The old document's `is_latest` is set to `false`
3. The old document's ChromaDB chunks are **purged** to avoid stale context
4. All version logic is **fail-open** — errors don't block the upload

---

## 8. Authentication & Authorization (RBAC)

### 8.1 Authentication Flow

```
User enters email + password
        │
        ▼
  AuthService.login()
        │
        ▼
  Supabase Auth: sign_in_with_password()
        │
        ▼
  SessionManager.persist_session()
        │  → Loads profile from profiles table
        │  → Checks status == ACTIVE
        │  → Updates last_login
        │  → Stores in st.session_state.session:
        │     {current_user, profile, role, access_token, refresh_token, expires_at}
        ▼
  Session restored on every Streamlit rerun
```

### 8.2 Session Management

- **No cookies, no external packages** — uses Streamlit's native `st.session_state`
- **Auto-restore**: On page reload, `SessionManager.restore_session()` checks:
  1. First: `st.session_state.session` (if still in memory)
  2. Fallback: Supabase client's inherent session (if retained)

### 8.3 Role-Based Access Control (RBAC)

Three roles with hierarchical permissions:

| Capability | `HR_ADMIN` | `HR_MANAGER` | `EMPLOYEE` |
|---|:---:|:---:|:---:|
| Chat with HR Agent | ✅ | ✅ | ✅ |
| Upload Documents | ✅ | ✅ | ❌ |
| Review Resumes | ✅ | ✅ | ❌ |
| Apply for Leave | ✅ | ✅ | ✅ |
| Approve/Reject Leave | ✅ | ✅ | ❌ |
| Manage KB Types | ✅ | ❌ | ❌ |
| Admin Dashboard | ✅ | ❌ | ❌ |
| View System Logs | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ |

Authorization is enforced via `AuthorizationService` middleware:

```python
authz.require_auth()          # Stops if not logged in
authz.require_admin()         # Stops if not HR_ADMIN
authz.require_manager()       # Stops if not HR_ADMIN or HR_MANAGER
authz.can_upload_documents()  # Returns bool
authz.can_approve_leave()     # Returns bool
```

---

## 9. Database Schema (Supabase / PostgreSQL)

### 9.1 Tables

```
┌──────────────────────────────────────────┐
│                 profiles                  │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ auth_user_id     UUID  FK→auth.users     │
│ name             TEXT                    │
│ email            TEXT  UNIQUE            │
│ role             user_role ENUM          │
│ department       TEXT                    │
│ status           user_status ENUM        │
│ created_at       TIMESTAMPTZ            │
│ updated_at       TIMESTAMPTZ            │
│ last_login       TIMESTAMPTZ            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│               documents                   │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ name             TEXT                    │
│ file_path        TEXT                    │
│ mime_type        TEXT                    │
│ file_size        BIGINT                  │
│ storage_bucket   TEXT                    │
│ storage_path     TEXT                    │
│ uploaded_by      UUID  FK→profiles       │
│ status           document_status ENUM    │
│ is_deleted       BOOLEAN                │
│ knowledge_base_id UUID  FK→knowledge_bases│
│ version_number   INTEGER                │
│ parent_document_id UUID                  │
│ is_latest        BOOLEAN                │
│ created_at       TIMESTAMPTZ            │
│ updated_at       TIMESTAMPTZ            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│             chat_history                  │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ user_id          UUID  FK→profiles       │
│ session_id       UUID                    │
│ question         TEXT                    │
│ response         TEXT                    │
│ agent_used       agent_type ENUM         │
│ llm_used         TEXT                    │
│ created_at       TIMESTAMPTZ            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│             evaluations                   │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ candidate_name   TEXT                    │
│ applied_role     TEXT                    │
│ ats_score        INTEGER                │
│ overall_score    INTEGER                │
│ recommendation   TEXT                    │
│ strengths        JSONB                   │
│ weaknesses       JSONB                   │
│ missing_skills   JSONB                   │
│ interview_questions JSONB               │
│ evaluation_json  JSONB                   │
│ created_by       UUID  FK→auth.users     │
│ created_at       TIMESTAMPTZ            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│           knowledge_bases                 │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ name             TEXT  UNIQUE            │
│ type             TEXT                    │
│ description      TEXT                    │
│ is_active        BOOLEAN                │
│ created_at       TIMESTAMPTZ            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│        onboarding_checklists              │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ candidate_id     UUID  FK→evaluations    │
│ task_name        TEXT                    │
│ status           TEXT  (PENDING/DONE)    │
│ completed_at     TIMESTAMPTZ            │
│ created_at       TIMESTAMPTZ            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│           leave_requests                  │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ employee_id      UUID  FK→profiles       │
│ leave_type       TEXT                    │
│ start_date       DATE                   │
│ end_date         DATE                   │
│ reason           TEXT                    │
│ status           TEXT  (PENDING/APPROVED │
│                        /REJECTED)        │
│ reviewed_by      UUID  FK→profiles       │
│ reviewed_at      TIMESTAMPTZ            │
│ created_at       TIMESTAMPTZ            │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│             audit_logs                    │
├──────────────────────────────────────────┤
│ id               UUID  PK               │
│ user_id          UUID  FK→profiles       │
│ action           TEXT                    │
│ details          JSONB                   │
│ created_at       TIMESTAMPTZ            │
└──────────────────────────────────────────┘
```

### 9.2 Enums

```sql
user_role:       'HR_ADMIN', 'HR_MANAGER'
user_status:     'ACTIVE', 'INACTIVE'
document_status: 'UPLOADED', 'PROCESSING', 'PROCESSED', 'FAILED'
agent_type:      'GENERAL', 'HR_POLICY', 'RESUME', 'EMAIL'
```

### 9.3 Key Database Features

- **Auto Profile Creation**: A trigger on `auth.users` automatically creates a `profiles` row when a user signs up. The default admin email (`admin@hragent.ai`) gets `HR_ADMIN` role; all others get `HR_MANAGER`.
- **Row-Level Security (RLS)**: Enabled on `documents`, `chat_history`, and `audit_logs`. Uses `SECURITY DEFINER` helper functions (`current_profile_id()`, `is_admin()`, `is_manager()`) to avoid recursive RLS.
- **Profiles RLS Disabled**: `profiles` table has RLS explicitly disabled — access is controlled by the Python backend via the service-role key.
- **Auto-Updated Timestamps**: Triggers on `profiles` and `documents` auto-update the `updated_at` column.

---

## 10. Prompt Template System (Jinja2)

All LLM prompts are externalized into `.j2` files in `app/prompts/templates/`. This separates prompt engineering from Python logic.

### 10.1 Loader

```python
# app/prompts/loader.py
from jinja2 import Environment, FileSystemLoader

_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

def render_prompt(template_name: str, **kwargs) -> str:
    return _env.get_template(template_name).render(**kwargs)
```

### 10.2 Templates

| Template | Variables | Used By |
|---|---|---|
| `resume_evaluation.j2` | `current_role`, `resume_text`, `kb_context`, `query` | `candidate_evaluator()` |
| `bulk_resume_evaluation.j2` | `role_name`, `resume_text`, `kb_context` | `evaluate_resumes_bulk()` |
| `interview_email.j2` | `analysis`, `match_percentage`, `recommendation` | `interview_email_generator()` |
| `hr_policy.j2` | `context`, `query` | `hr_policy_specialist()` |
| `leave_extraction.j2` | `query` | `leave_specialist()` |
| `intent_classification.j2` | `query` | `detect_intent()` |
| `document_classification.j2` | `text` | PDF upload classifier in `chat.py` |
| `role_detection.j2` | `available_roles`, `resume_text` | Resume-to-role matching in `chat.py` |

### 10.3 Usage Pattern

```python
from app.prompts.loader import render_prompt

prompt = render_prompt(
    "resume_evaluation.j2",
    current_role="Software Engineer",
    resume_text=resume_content,
    kb_context=rag_context,
    query=user_query,
)
result = structured_llm.invoke(prompt)
```

---

## 11. Dependency Injection Container

The `app/utils/dependencies.py` module implements a two-tier DI container:

### 11.1 Backend Container (Cached — runs once per server start)

```python
@st.cache_resource
def get_backend_container():
    return {
        "supabase_service":  SupabaseService(),        # Singleton DB client
        "profile_repo":      ProfileRepository(...),    # User CRUD
        "chat_repo":         ChatRepository(...),       # Chat history CRUD
        "user_service":      UserService(...),           # User management
        "knowledge_base":    KnowledgeBaseService(...),  # Full KB lifecycle
    }
```

### 11.2 Frontend Factory (Uncached — runs every Streamlit rerun)

```python
def get_frontend_factory():
    return {
        "session_manager":        SessionManager(...),        # Session state
        "auth_service":           AuthService(...),            # Login/logout
        "authorization_service":  AuthorizationService(...),   # RBAC middleware
    }
```

### 11.3 Getter Functions (Used in pages)

```python
get_auth_service()            # → AuthService
get_session_manager()         # → SessionManager
get_authorization_service()   # → AuthorizationService
get_user_service()            # → UserService
get_chat_repo()               # → ChatRepository
get_knowledge_base_service()  # → KnowledgeBaseService
```

---

## 12. Pydantic Models (Structured LLM Output)

### 12.1 `CandidateEvaluation`

The LLM is forced to return this exact schema via `.with_structured_output()`:

```python
class CandidateEvaluation(BaseModel):
    candidate_name: str               # Extracted from resume
    match_percentage: int              # 0-100 overall match
    recommendation: Literal["Selected", "Rejected", "Hold"]
    analysis: str                      # 2-4 sentence executive summary
    suggested_questions: List[str]     # Up to 5 interview questions
    scorecard: List[ScorecardItem]     # 3-6 role-specific criteria
    final_answer: str                  # One-line chat response (max 25 words)

class ScorecardItem(BaseModel):
    criterion: str         # e.g., "Technical Skills", "Experience"
    score: int             # 0-100
    justification: str     # One sentence explaining the score
```

### 12.2 `LeaveExtraction`

```python
class LeaveExtraction(BaseModel):
    leave_type: str                # e.g., "Sick Leave", "Vacation"
    start_date: Optional[str]      # YYYY-MM-DD or null
    end_date: Optional[str]        # YYYY-MM-DD or null
    reason: Optional[str]          # Extracted from query
```

### 12.3 `IntentClassification`

```python
class IntentClassification(BaseModel):
    intent: str   # One of: recruitment, resume, email, policy,
                  #         general, onboarding, leave
```

### 12.4 User Models

```python
class Role(str, Enum):
    HR_ADMIN = "HR_ADMIN"
    HR_MANAGER = "HR_MANAGER"
    EMPLOYEE = "EMPLOYEE"

class Profile(BaseModel):
    id: str
    auth_user_id: str
    name: str
    email: str
    role: Role
    department: Optional[str]
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
```

---

## 13. Frontend Pages (Streamlit)

### 13.1 Page Navigation

```python
# main.py
login_page = st.Page("app/pages/login.py", title="Log in")
chat_page  = st.Page("app/pages/chat.py", title="💬 Chat", default=True)
kb_page    = st.Page("app/pages/knowledge_base.py", title="📚 Knowledge Base")
kb_types   = st.Page("app/pages/knowledge_base_types.py", title="📑 KB Types")
admin_page = st.Page("app/pages/admin.py", title="⚙️ Admin Dashboard")

# Pages shown based on role:
# All authenticated users:  chat_page
# HR_ADMIN + HR_MANAGER:    chat_page + kb_page
# HR_ADMIN only:            chat_page + kb_page + kb_types + admin_page
```

### 13.2 Page Details

| Page | File | Key Features |
|---|---|---|
| **Login** | `login.py` | Email/password form, Supabase auth |
| **Chat** | `chat.py` | Main AI chat, single/bulk resume upload, auto-detect doc type & role, session management, execution log, recruitment dashboard with scorecard charts |
| **Knowledge Base** | `knowledge_base.py` | Upload PDFs to specific KB categories, view/delete/reindex indexed documents |
| **KB Types** | `knowledge_base_types.py` | CRUD for knowledge base categories (e.g., "Software Engineer", "Data Scientist", "General HR") |
| **Admin** | `admin.py` | View all users table, change user roles, create new users |

---

## 14. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | ✅ | Google AI Studio API key for Gemini LLM + embeddings |
| `GROQ_API_KEY` | ✅ | Groq API key for fallback LLM (Llama 3.3 70B) |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anonymous/public key (for auth) |
| `SUPABASE_SERVICE_KEY` | ⚠️ Recommended | Supabase service role key (bypasses RLS for admin operations) |

---

## 15. Key Python Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | 1.59.2 | Web UI framework |
| `langchain` | 1.3.14 | LLM orchestration framework |
| `langgraph` | 1.2.9 | State machine for agent workflows |
| `langchain-google-genai` | 4.2.7 | Google Gemini LLM + embeddings integration |
| `langchain-groq` | 1.1.3 | Groq LLM integration (fallback) |
| `langchain-chroma` | 1.1.0 | ChromaDB vector store integration |
| `chromadb` | 1.5.9 | Local vector database |
| `supabase` | 2.31.0 | Supabase Python client (Auth + DB + Storage) |
| `pydantic` | 2.13.4 | Data validation & structured LLM output |
| `pypdf` | 6.14.2 | PDF text extraction |
| `jinja2` | 3.1.6 | LLM prompt templates |
| `sentence-transformers` | 5.6.0 | HuggingFace embedding models (legacy) |
| `torch` | 2.13.0 | PyTorch (required by sentence-transformers) |
| `pandas` | 3.0.3 | Data manipulation for admin dashboard tables |

---

*This document reflects the complete state of the HR Agentic AI codebase as of September 2026.*
