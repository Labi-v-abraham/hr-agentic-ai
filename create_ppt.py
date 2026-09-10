#!/usr/bin/env python3
"""Generate a comprehensive PPT for HR Agentic AI project."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Colors
BG = RGBColor(0x0F, 0x17, 0x2A)
CARD = RGBColor(0x16, 0x21, 0x3E)
CARD2 = RGBColor(0x1A, 0x28, 0x48)
C1 = RGBColor(0x38, 0xBD, 0xF8)
C2 = RGBColor(0x81, 0x8C, 0xF8)
C3 = RGBColor(0x34, 0xD3, 0x99)
W = RGBColor(0xFF, 0xFF, 0xFF)
G = RGBColor(0xA0, 0xAE, 0xC0)
OR = RGBColor(0xFB, 0x92, 0x3C)
RD = RGBColor(0xF8, 0x71, 0x71)
YL = RGBColor(0xFA, 0xCC, 0x15)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SH = prs.slide_height

def bg(s):
    f = s.background.fill; f.solid(); f.fore_color.rgb = BG

def rect(s, l, t, w, h, c):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = c; sh.line.fill.background()
    try: sh.adjustments[0] = 0.06
    except: pass
    return sh

def bar(s, l, t, w, c):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, Inches(0.04))
    sh.fill.solid(); sh.fill.fore_color.rgb = c; sh.line.fill.background()

def vbar(s, l, t, h, c):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, Inches(0.06), h)
    sh.fill.solid(); sh.fill.fore_color.rgb = c; sh.line.fill.background()

def tb(s, l, t, w, h, txt, sz=18, b=False, c=W, a=PP_ALIGN.LEFT):
    bx = s.shapes.add_textbox(l, t, w, h)
    tf = bx.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = txt; p.font.size = Pt(sz)
    p.font.bold = b; p.font.color.rgb = c; p.font.name = "Calibri"; p.alignment = a
    return tf

def hdr(s, t, sub=""):
    bg(s); bar(s, Inches(0.8), Inches(0.6), Inches(2.5), C1)
    tb(s, Inches(0.8), Inches(0.75), Inches(11), Inches(1), t, 36, True, W)
    if sub: tb(s, Inches(0.8), Inches(1.55), Inches(11), Inches(0.6), sub, 18, False, G)

def bcard(s, l, t, w, h, title, bullets, tc=C1):
    r = rect(s, l, t, w, h, CARD)
    tf = r.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.25); tf.margin_right = Inches(0.25); tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]; p.text = title; p.font.size = Pt(18); p.font.bold = True
    p.font.color.rgb = tc; p.font.name = "Calibri"
    for b in bullets:
        bp = tf.add_paragraph(); bp.text = f"  {b}" if b else ""
        bp.font.size = Pt(14); bp.font.color.rgb = G; bp.font.name = "Calibri"; bp.space_before = Pt(4)

def icard(s, l, t, w, h, icon, title, desc, ac=C1):
    r = rect(s, l, t, w, h, CARD)
    tf = r.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.2); tf.margin_right = Inches(0.2); tf.margin_top = Inches(0.15)
    p = tf.paragraphs[0]; p.text = icon; p.font.size = Pt(28); p.alignment = PP_ALIGN.CENTER
    p2 = tf.add_paragraph(); p2.text = title; p2.font.size = Pt(15); p2.font.bold = True
    p2.font.color.rgb = ac; p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(4)
    p3 = tf.add_paragraph(); p3.text = desc; p3.font.size = Pt(12)
    p3.font.color.rgb = G; p3.alignment = PP_ALIGN.CENTER; p3.space_before = Pt(4)

# ═══ SLIDE 1: Title ═══
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
rect(s, Inches(0), Inches(0), Inches(0.08), SH, C1)
bar(s, Inches(1.5), Inches(2.4), Inches(3), C1)
bar(s, Inches(1.5), Inches(5.2), Inches(4), C2)
tb(s, Inches(1.5), Inches(2.55), Inches(10), Inches(1.2), "HR Agentic AI", 52, True, W)
tb(s, Inches(1.5), Inches(3.7), Inches(10), Inches(1), "An Intelligent Multi-Agent HR Assistant\npowered by RAG, LangGraph & Gemini AI", 22, False, G)
tb(s, Inches(1.5), Inches(5.35), Inches(10), Inches(0.5), "Presented by: Labi V Abraham", 18, True, C2)
tb(s, Inches(1.5), Inches(5.85), Inches(10), Inches(0.4), "Mentor Presentation  |  September 2026", 14, False, G)

# ═══ SLIDE 2: Agenda ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Agenda", "What we'll cover today")
agenda = [
    "Project Overview & Problem Statement", "Tech Stack & Architecture",
    "AI/ML - RAG, Agentic AI & LangGraph Workflow", "Key Features & Specialist Agents",
    "Database Design & Backend Services", "Authentication & Role-Based Access (RBAC)",
    "Knowledge Base Management & Document Pipeline", "UI/UX - Streamlit Frontend",
    "Challenges Faced & Solutions", "Key Learnings & Skill Improvements",
    "Future Enhancements", "Live Demo & Q&A",
]
for i, item in enumerate(agenda):
    x = Inches(0.8) if i < 6 else Inches(6.5)
    y = Inches(2.3) + Inches(0.42) * (i if i < 6 else i - 6)
    bd = rect(s, x, y, Inches(0.45), Inches(0.35), C1)
    tf = bd.text_frame; tf.margin_top = Inches(0.04)
    p = tf.paragraphs[0]; p.text = f"{i+1:02d}"; p.font.size = Pt(14); p.font.bold = True
    p.font.color.rgb = BG; p.alignment = PP_ALIGN.CENTER
    tb(s, x + Inches(0.55), y, Inches(4.8), Inches(0.35), item, 15, False, W)

# ═══ SLIDE 3: Project Overview ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Project Overview", "What is HR Agentic AI?")
tb(s, Inches(0.8), Inches(2.2), Inches(11.5), Inches(0.8),
   "An AI-powered HR Assistant that autonomously handles recruitment, policy queries,\nleave management, and onboarding using multiple specialized AI agents.", 17, False, G)
bcard(s, Inches(0.8), Inches(3.4), Inches(5.5), Inches(3.5), "Problem Statement", [
    "Manual resume screening is time-consuming",
    "HR policy queries require human intervention",
    "No centralized, intelligent HR assistant",
    "Leave management is fragmented",
    "Onboarding tracking is paper-based"], tc=RD)
bcard(s, Inches(6.8), Inches(3.4), Inches(5.5), Inches(3.5), "Our Solution", [
    "Multi-agent AI system with autonomous routing",
    "RAG-powered policy Q&A from company docs",
    "Automated resume evaluation with scorecards",
    "Natural language leave apply/approve workflow",
    "Onboarding checklist tracking per candidate"], tc=C3)

# ═══ SLIDE 4: Tech Stack ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Technology Stack", "Tools & frameworks powering the project")
tech = [
    ("Google Gemini 2.5 Flash", "Primary LLM for all\nagent intelligence", C1),
    ("LangChain + LangGraph", "Agent orchestration,\nstate machines, routing", C2),
    ("ChromaDB", "Vector database for\nRAG embeddings", C3),
    ("Streamlit", "Interactive web UI\nwith chat interface", OR),
    ("Supabase (PostgreSQL)", "Auth, profiles, evals,\nleave, chat history", C1),
    ("Pydantic", "Structured LLM output\n& data validation", C2),
    ("Gemini Embedding-2", "gemini-embedding-2\nfor document vectors", C3),
    ("PyPDF", "PDF parsing for\nresumes & handbooks", OR),
]
for i, (t, d, c) in enumerate(tech):
    icard(s, Inches(0.8) + (i%4)*Inches(3.1), Inches(2.4) + (i//4)*Inches(2.4),
          Inches(2.8), Inches(2.1), ["🧠","🔗","📊","🖥️","🗄️","📐","🔍","📄"][i], t, d, c)

# ═══ SLIDE 5: Architecture ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "System Architecture", "High-level overview of the application layers")
layers = [
    ("PRESENTATION LAYER", "Streamlit UI  |  Chat Interface  |  Knowledge Base Manager  |  Admin Dashboard", C1, Inches(2.4)),
    ("AUTHENTICATION & RBAC", "Supabase Auth  |  Session Manager  |  Authorization Service  |  Role-Based Access", C2, Inches(3.3)),
    ("AGENTIC AI LAYER", "LangGraph State Machine  |  Supervisor Agent  |  Intent Router  |  6 Specialist Agents", C3, Inches(4.2)),
    ("RAG & EMBEDDING LAYER", "ChromaDB Vector Store  |  Gemini Embeddings  |  Similarity Search  |  Confidence Scoring", OR, Inches(5.1)),
    ("DATA & STORAGE LAYER", "Supabase PostgreSQL  |  Supabase Storage (Buckets)  |  Chat History  |  Evaluations  |  Leave", YL, Inches(6.0)),
]
for t, d, c, y in layers:
    rect(s, Inches(0.8), y, Inches(11.7), Inches(0.75), CARD)
    vbar(s, Inches(0.8), y, Inches(0.75), c)
    tb(s, Inches(1.1), y + Inches(0.05), Inches(3), Inches(0.35), t, 13, True, c)
    tb(s, Inches(1.1), y + Inches(0.38), Inches(11), Inches(0.35), d, 12, False, G)
for i in range(4):
    tb(s, Inches(6.2), layers[i][3] + Inches(0.7), Inches(1), Inches(0.25), "▼", 14, False, G, PP_ALIGN.CENTER)

# ═══ SLIDE 6: LangGraph Workflow ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Agentic AI Workflow - LangGraph", "The core multi-agent state machine")
flow = [
    ("User Query", "User sends question\nvia chat interface", C1, Inches(0.5)),
    ("Supervisor", "Detects intent using\nstructured LLM output", C2, Inches(2.8)),
    ("Intent Router", "Routes to correct\nspecialist agent", C3, Inches(5.1)),
    ("Specialist Agent", "Executes domain task\n(RAG/Eval/etc.)", OR, Inches(7.4)),
    ("Final Response", "Formats & returns\nresult to user", YL, Inches(9.7)),
]
for t, d, c, x in flow:
    icard(s, x, Inches(2.4), Inches(2.1), Inches(1.8), "", t, d, c)
for i in range(4):
    tb(s, flow[i][3] + Inches(2.15), Inches(3.0), Inches(0.6), Inches(0.5), "->", 28, True, G, PP_ALIGN.CENTER)
tb(s, Inches(0.8), Inches(4.7), Inches(11), Inches(0.5), "Supported Intents:", 16, True, C1)
intents = [("resume","Resume Evaluation",C1),("recruitment","Resume + Interview Email",C2),
           ("policy","HR Policy (RAG)",C3),("email","Email Generation",OR),
           ("onboarding","Onboarding Tracker",YL),("leave","Leave Management",RD),
           ("general","General Chat",G)]
for i, (k, v, c) in enumerate(intents):
    x = Inches(0.8) + (i%4)*Inches(3.1)
    y = Inches(5.3) + (i//4)*Inches(0.8)
    bd = rect(s, x, y, Inches(2.8), Inches(0.6), CARD)
    tf = bd.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.15); tf.margin_top = Inches(0.08)
    p = tf.paragraphs[0]; p.text = f'"{k}" -> {v}'; p.font.size = Pt(13); p.font.color.rgb = c

# ═══ SLIDE 7: RAG Pipeline ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "RAG Pipeline - Retrieval-Augmented Generation", "How the system grounds LLM responses in company documents")
tb(s, Inches(0.8), Inches(2.2), Inches(5), Inches(0.4), "Document Ingestion Pipeline", 18, True, C1)
ingest = [("1", "Upload PDF", "Employee handbook or\nrole-specific docs"),
          ("2", "Parse & Chunk", "PyPDFLoader + LangChain\ntext splitters"),
          ("3", "Embed", "Gemini Embedding-2\nmodel generates vectors"),
          ("4", "Store", "ChromaDB persistent\nvector store")]
for i, (n, t, d) in enumerate(ingest):
    icard(s, Inches(0.8)+i*Inches(2.9), Inches(2.7), Inches(2.6), Inches(1.6), n, t, d, C1)
for i in range(3):
    tb(s, Inches(0.8)+(i+1)*Inches(2.9)-Inches(0.35), Inches(3.3), Inches(0.4), Inches(0.5), "->", 22, True, G, PP_ALIGN.CENTER)
tb(s, Inches(0.8), Inches(4.7), Inches(5), Inches(0.4), "Query-Time Retrieval Pipeline", 18, True, C3)
query = [("1", "User Query", "Natural language\nHR question"),
         ("2", "Vector Search", "MMR similarity search\nwith KB ID filtering"),
         ("3", "Confidence Score", "Average similarity\nscore -> badge"),
         ("4", "LLM + Context", "Gemini answers using\nretrieved chunks only")]
for i, (n, t, d) in enumerate(query):
    icard(s, Inches(0.8)+i*Inches(2.9), Inches(5.1), Inches(2.6), Inches(1.6), n, t, d, C3)
for i in range(3):
    tb(s, Inches(0.8)+(i+1)*Inches(2.9)-Inches(0.35), Inches(5.7), Inches(0.4), Inches(0.5), "->", 22, True, G, PP_ALIGN.CENTER)

# ═══ SLIDE 8: Specialist Agents ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Specialist Agents - Deep Dive", "Six autonomous AI agents handling different HR domains")
agents = [
    ("Candidate Evaluator", ["Evaluates resumes against job role","Computes match % using structured output","Generates scorecard (3-6 criteria)","Recommends: Selected / Rejected / Hold"], C1),
    ("Email Generator", ["Drafts interview invitation emails","Professional formatting with placeholders","Triggered when match >= 80%","Automated by Supervisor Decision"], C2),
    ("HR Policy Specialist", ["Answers policy questions via RAG","Queries ChromaDB vector store","Shows confidence badge & sources","Detects knowledge gaps"], C3),
    ("Onboarding Specialist", ["Starts onboarding for selected candidates","Creates 5-task checklist in Supabase","Marks tasks done via natural language","Shows onboarding status per candidate"], OR),
    ("Leave Specialist", ["Apply for leave via natural language","LLM extracts dates & leave type","Managers can approve/reject leaves","View pending & personal leave status"], YL),
    ("General Assistant", ["Handles small talk & greetings","Answers non-HR general queries","Fallback for unclassified intents","Direct LLM conversation"], G),
]
for i, (t, b, c) in enumerate(agents):
    bcard(s, Inches(0.5)+(i%3)*Inches(4.2), Inches(2.2)+(i//3)*Inches(2.8), Inches(3.9), Inches(2.5), t, b, tc=c)

# ═══ SLIDE 9: Supervisor & Decision ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Supervisor Agent & Decision Logic", "How the system makes autonomous decisions")
bcard(s, Inches(0.8), Inches(2.3), Inches(5.5), Inches(4.5), "Supervisor Agent", [
    "Entry point of the LangGraph workflow","Uses structured LLM output (IntentClassification)",
    "Pydantic model enforces valid intent values","Fallback keyword-based intent detection",
    "Supported: resume, recruitment, email,","  policy, onboarding, leave, general","",
    "Intent routing via conditional edges","in StateGraph - NOT if/else in code"], tc=C1)
bcard(s, Inches(6.8), Inches(2.3), Inches(5.5), Inches(2.2), "Supervisor Decision (Post-Evaluation)", [
    "Runs AFTER candidate evaluation completes","If match_percentage >= 80% -> Interview Email",
    "If match_percentage < 80% -> Final Response","Fully autonomous - no human intervention"], tc=C3)
bcard(s, Inches(6.8), Inches(4.8), Inches(5.5), Inches(2), "Structured LLM Output (Pydantic)", [
    "CandidateEvaluation: match %, recommendation,","  analysis, scorecard, suggested questions",
    "LeaveExtraction: leave_type, dates, reason","IntentClassification: validated intent string"], tc=C2)

# ═══ SLIDE 10: Database ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Database Design - Supabase PostgreSQL", "Tables, storage, and data flow")
tables = [
    ("profiles","User profiles with RBAC roles\n(HR_ADMIN, HR_MANAGER, EMPLOYEE)",C1),
    ("chat_history","Persisted chat messages\nuser_id, session_id, question, response",C2),
    ("evaluations","Resume evaluation results\ncandidate_name, score, recommendation",C3),
    ("knowledge_bases","Knowledge base categories\n(General HR, role-specific KBs)",OR),
    ("documents","Document metadata, versions,\nstorage paths, processing status",YL),
    ("onboarding_checklists","Per-candidate task tracking\ntask_name, status (PENDING/DONE)",RD),
    ("leave_requests","Leave applications with\nstatus, type, dates, approver",C1),
    ("Supabase Storage","File bucket (hr_documents)\nfor PDF binary storage",C2),
]
for i, (n, d, c) in enumerate(tables):
    icard(s, Inches(0.5)+(i%4)*Inches(3.15), Inches(2.3)+(i//4)*Inches(2.5), Inches(2.9), Inches(2.2), "DB", n, d, c)

# ═══ SLIDE 11: Auth & RBAC ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Authentication & RBAC", "Role-based access control with Supabase Auth")
roles = [
    ("HR_ADMIN", ["Full system access","Manage users & roles","Upload documents to any KB","View all chat logs","Approve/reject leave requests","Access admin dashboard"], C1),
    ("HR_MANAGER", ["Upload documents","Review resumes & evaluate","Approve/reject leave requests","Access knowledge base","Cannot manage users"], C2),
    ("EMPLOYEE", ["Chat with HR assistant","Ask policy questions","Apply for leave","View own leave status","Limited access scope"], C3),
]
for i, (r, p, c) in enumerate(roles):
    bcard(s, Inches(0.5)+i*Inches(4.2), Inches(2.3), Inches(3.9), Inches(4), r, p, tc=c)
tb(s, Inches(0.8), Inches(6.6), Inches(11), Inches(0.6),
   "Auth Stack: Supabase Auth -> SessionManager -> AuthorizationService -> Page-level require_auth() / require_roles()", 13, False, G)

# ═══ SLIDE 12: Knowledge Base ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Knowledge Base Management", "Document pipeline with versioning & reindexing")
bcard(s, Inches(0.8), Inches(2.3), Inches(5.5), Inches(4.5), "Upload Pipeline", [
    "1. Ensure storage bucket exists","2. Detect if document already exists (versioning)",
    "3. Insert metadata -> status: PROCESSING","4. Upload binary to Supabase Storage",
    "5. Extract text -> chunk -> embed -> ChromaDB","6. Update status -> PROCESSED",
    "7. If version 2+: retire old doc, purge old chunks","",
    "Features: Soft delete, reindex, version tracking,","deterministic chunk IDs (doc_id + chunk_index)"], tc=C1)
bcard(s, Inches(6.8), Inches(2.3), Inches(5.5), Inches(2.3), "Document Versioning", [
    "Detects existing doc by name + KB + is_latest","New upload gets version_number = prev + 1",
    "parent_document_id links to previous version","Old version's ChromaDB chunks are purged"], tc=C3)
bcard(s, Inches(6.8), Inches(4.9), Inches(5.5), Inches(1.9), "Fail-Open Design", [
    "Version detection errors are non-fatal","Upload proceeds even if versioning fails",
    "Storage rollback on upload failure","Graceful error handling at every step"], tc=OR)

# ═══ SLIDE 13: Resume Evaluation ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Resume Evaluation - Detailed View", "Structured AI-powered candidate assessment")
bcard(s, Inches(0.8), Inches(2.3), Inches(5.5), Inches(2.5), "Evaluation Process", [
    "Upload resume PDF -> Extract text via PyPDF","Query role-specific knowledge base via RAG",
    "LLM evaluates resume against role requirements","Uses with_structured_output(CandidateEvaluation)",
    "Results saved to Supabase evaluations table"], tc=C1)
bcard(s, Inches(6.8), Inches(2.3), Inches(5.5), Inches(2.5), "Structured Output Schema", [
    "candidate_name: Extracted from resume","match_percentage: 0-100 overall score",
    "recommendation: Selected / Rejected / Hold","analysis: 2-4 sentence executive summary",
    "scorecard: 3-6 role-specific criteria with scores","suggested_questions: Up to 5 interview questions"], tc=C2)
bcard(s, Inches(0.8), Inches(5.1), Inches(11.5), Inches(2), "RAG-Enhanced Evaluation", [
    "KB chunks retrieved using similarity_search_with_score (k=10) filtered by knowledge_base_id",
    "Confidence badge: High (>=0.75) | Medium (>=0.5) | Low (<0.5)",
    "Knowledge gap detection: flags when no relevant chunks found or avg score < 0.4",
    "Source files listed for transparency - full RAG citation chain"], tc=C3)

# ═══ SLIDE 14: Leave & Onboarding ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Leave Management & Onboarding Tracker", "End-to-end employee lifecycle features")
bcard(s, Inches(0.8), Inches(2.3), Inches(5.5), Inches(4.8), "Leave Management System", [
    "APPLY: Natural language -> LLM extracts dates",'  "Apply for sick leave from 2025-03-10 to 2025-03-12"',
    "  Uses LeaveExtraction Pydantic model","",
    "STATUS: View own leave requests with icons","  PENDING | APPROVED | REJECTED","",
    "PENDING LIST: Managers see all pending requests","  Joined with profiles for employee names","",
    "APPROVE/REJECT: Manager decision via chat",'  "Approve leave for John Doe"',
    "  RBAC enforced - employees cannot approve"], tc=YL)
bcard(s, Inches(6.8), Inches(2.3), Inches(5.5), Inches(4.8), "Onboarding Checklist Tracker", [
    "START: Creates 5 default checklist tasks","  IT Equipment | HR Paperwork | Welcome Meeting",
    "  Role Training | Team Introduction","","  Only for Selected candidates (validated)",
    "  Stores in onboarding_checklists table","","UPDATE: Mark tasks done via natural language",
    '  "Mark IT equipment done for Jane Doe"',"  Fuzzy matching on task names","",
    "STATUS: View checklist with status icons",'  "Onboarding status for Jane Doe"'], tc=OR)

# ═══ SLIDE 15: Streamlit UI ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Frontend - Streamlit UI", "Interactive multi-page application")
pages = [
    ("Chat Page", ["WhatsApp-style chat bubbles (custom CSS)","Resume PDF upload with text extraction",
     "Role-specific knowledge base selection","Evaluation dashboard with scorecard",
     "Execution log showing agent thought process","Chat history persistence via Supabase"], C1),
    ("Knowledge Base", ["Upload documents to specific KBs","View document list with status badges",
     "Reindex / delete documents","Version history tracking","File size & upload date display"], C2),
    ("Admin Dashboard", ["User management (create/edit/delete)","Role assignment (Admin/Manager/Employee)",
     "System-wide settings","Accessible only to HR_ADMIN role"], C3),
    ("Login Page", ["Supabase Auth integration","Email + password authentication",
     "Session persistence","Auto-redirect on auth state"], OR),
]
for i, (t, b, c) in enumerate(pages):
    bcard(s, Inches(0.3)+i*Inches(3.2), Inches(2.3), Inches(3.0), Inches(4.5), t, b, tc=c)

# ═══ SLIDE 16: Code Structure ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Project Code Structure", "Clean separation of concerns with modular architecture")
structure = """app/
 agents/
   graph/
     workflow.py    <- LangGraph state machine
     node.py        <- 6 specialist agent functions
     router.py      <- Intent classification
     state.py       <- AgentState TypedDict
   rag/
     retriever.py   <- ChromaDB retriever + embeddings
     vectorstore.py <- Vector store builder
     build_vectorstore.py <- KB adapter
     loader.py      <- PDF document loader
 auth/
   auth_service.py    <- Supabase auth wrapper
   authorization.py   <- RBAC middleware
   session_manager.py <- Session state handler
 database/
   supabase_service.py <- Singleton DB client
   chat_repository.py  <- Chat history CRUD
   profile_repository.py
 models/
   models.py          <- Pydantic: CandidateEval, Leave
   user.py            <- Role enum, Profile model
 pages/
   chat.py, login.py, admin.py
   knowledge_base.py, knowledge_base_types.py
 services/
   knowledge_base.py  <- Full KB pipeline service
 utils/
   config.py, dependencies.py"""
bx = s.shapes.add_textbox(Inches(0.8), Inches(2.2), Inches(11.5), Inches(5))
tf = bx.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.text = structure; p.font.size = Pt(12); p.font.color.rgb = C1; p.font.name = "Courier New"

# ═══ SLIDE 17: Challenges ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Challenges Faced & Solutions", "Real-world problems encountered during development")
items = [
    ("LLM returning inconsistent output formats", "Pydantic with_structured_output() enforces strict schema"),
    ("ChromaDB duplicate chunks on re-upload", "Deterministic IDs (doc_id + chunk_index) + upsert"),
    ("RAG returning irrelevant cross-KB results", "Knowledge base ID filtering on similarity search"),
    ("Leave date extraction from natural language", "Dedicated LeaveExtraction Pydantic model with LLM"),
    ("Supabase RLS blocking backend operations", "Dual client pattern: anon_key + service_role_key"),
    ("Document versioning without breaking data", "Fail-open design - versioning errors are non-fatal"),
    ("Session management across Streamlit reruns", "Custom SessionManager with st.session_state"),
]
rect(s, Inches(0.8), Inches(2.2), Inches(5.3), Inches(0.5), C1)
tb(s, Inches(0.9), Inches(2.22), Inches(5), Inches(0.45), "Challenge", 14, True, BG)
rect(s, Inches(6.1), Inches(2.2), Inches(6.2), Inches(0.5), C3)
tb(s, Inches(6.2), Inches(2.22), Inches(6), Inches(0.45), "Solution", 14, True, BG)
for i, (ch, sol) in enumerate(items):
    y = Inches(2.8) + i * Inches(0.62)
    bgc = CARD if i % 2 == 0 else CARD2
    rect(s, Inches(0.8), y, Inches(5.3), Inches(0.55), bgc)
    tb(s, Inches(0.9), y + Inches(0.05), Inches(5.1), Inches(0.45), ch, 12, False, G)
    rect(s, Inches(6.1), y, Inches(6.2), Inches(0.55), bgc)
    tb(s, Inches(6.2), y + Inches(0.05), Inches(6), Inches(0.45), sol, 12, False, C3)

# ═══ SLIDE 18: Key Learnings ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Key Learnings & Skill Improvement", "What I gained through this project")
bcard(s, Inches(0.5), Inches(2.2), Inches(4), Inches(4.8), "AI / ML / LLM Skills", [
    "Agentic AI architecture design","LangGraph state machines & workflows",
    "RAG pipeline: embed -> store -> retrieve","Prompt engineering for structured output",
    "Pydantic schemas for LLM response control","Vector databases (ChromaDB) concepts",
    "Embedding models (Gemini, HuggingFace)","Multi-agent orchestration patterns",
    "Confidence scoring & knowledge gap detection"], tc=C1)
bcard(s, Inches(4.8), Inches(2.2), Inches(3.8), Inches(4.8), "Backend & Architecture", [
    "Clean architecture with separation of concerns","Dependency injection pattern",
    "Singleton pattern (SupabaseService)","Repository pattern for data access",
    "Service layer design","Role-based access control (RBAC)",
    "Document versioning strategies","Fail-open vs fail-closed design",
    "Error handling best practices"], tc=C2)
bcard(s, Inches(8.9), Inches(2.2), Inches(3.8), Inches(4.8), "Frontend & Full Stack", [
    "Streamlit multi-page app architecture","Session state management",
    "Custom CSS for chat UI styling","File upload & PDF processing",
    "Supabase Auth integration","Real-time UI feedback",
    "Supabase Storage (buckets)","PostgreSQL via Supabase client",
    "Environment configuration (.env)"], tc=C3)

# ═══ SLIDE 19: AI Tools Detail ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "AI Tools & Frameworks - Detailed Breakdown", "Deep dive into AI/RAG/Agentic tools used")
tools = [
    ("LangChain", "Core framework for LLM app development.\nUsed for: document loaders, text splitters,\nembeddings, structured output, chains.", C1),
    ("LangGraph", "State machine framework for multi-agent\nworkflows. Used for: StateGraph, conditional\nedges, node routing, orchestration.", C2),
    ("Google Gemini 2.5 Flash", "Primary LLM powering all agent intelligence.\nUsed via: ChatGoogleGenerativeAI.\nFast inference, structured output.", C3),
    ("Gemini Embedding-2", "Document embedding model for RAG pipeline.\nUsed via: GoogleGenerativeAIEmbeddings.\nCreates vector representations of chunks.", OR),
    ("ChromaDB", "Persistent vector database for RAG retrieval.\nFeatures: MMR search, metadata filtering,\nsimilarity_search_with_score.", YL),
    ("Groq (Optional)", "Alternative LLM provider configured.\nlangchain-groq integrated for fallback.\nFast inference on open-source models.", RD),
]
for i, (t, d, c) in enumerate(tools):
    x = Inches(0.5) + (i%3)*Inches(4.2)
    y = Inches(2.3) + (i//3)*Inches(2.6)
    r = rect(s, x, y, Inches(3.9), Inches(2.3), CARD)
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(3.9), Inches(0.05))
    sh.fill.solid(); sh.fill.fore_color.rgb = c; sh.line.fill.background()
    tf = r.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2); tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]; p.text = t; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = c
    dp = tf.add_paragraph(); dp.text = d; dp.font.size = Pt(11); dp.font.color.rgb = G; dp.space_before = Pt(8)

# ═══ SLIDE 20: MCP Status ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "MCP (Model Context Protocol) Status", "Not used in this project - here's what we used instead")
bcard(s, Inches(0.8), Inches(2.3), Inches(5.5), Inches(2.5), "MCP Was NOT Used", [
    "No MCP server configuration found","No external tool integration via MCP",
    "Project uses direct LangChain/LangGraph","All tools are built-in agent functions"], tc=RD)
bcard(s, Inches(6.8), Inches(2.3), Inches(5.5), Inches(2.5), "What We Used Instead", [
    "LangGraph nodes as specialized tools/agents","Pydantic structured output as tool schema",
    "Direct Supabase client for DB operations","ChromaDB as the retrieval tool for RAG"], tc=C3)
bcard(s, Inches(0.8), Inches(5.2), Inches(11.5), Inches(1.8), "Future: MCP Could Enhance This Project", [
    "MCP server for external HR system integrations (SAP, Workday, BambooHR)",
    "MCP tools for calendar booking (interview scheduling), email sending",
    "MCP resources for real-time salary benchmarking data, job market analytics",
    "Would enable the agentic system to interact with external services autonomously"], tc=C2)

# ═══ SLIDE 21: Future ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Future Enhancements", "Roadmap for continued development")
future = [
    ("MCP Integration","Connect to external HR\ntools (SAP, Workday)",C1),
    ("Analytics Dashboard","Visual analytics for\nrecruitment metrics",C2),
    ("Voice Interface","Speech-to-text for\nhands-free HR queries",C3),
    ("Email Integration","Send actual emails via\nSMTP/Gmail API",OR),
    ("Notifications","Push alerts for leave\napprovals & onboarding",YL),
    ("A/B Testing","Compare LLM models\nfor evaluation quality",RD),
    ("Mobile App","React Native or Flutter\nfor mobile access",C1),
    ("CI/CD Pipeline","Automated testing and\ndeployment pipeline",C2),
]
for i, (t, d, c) in enumerate(future):
    icard(s, Inches(0.5)+(i%4)*Inches(3.15), Inches(2.3)+(i//4)*Inches(2.5), Inches(2.9), Inches(2.1), ["🔌","📊","🗣","📧","🔔","🧪","📱","🔄"][i], t, d, c)

# ═══ SLIDE 22: Metrics ═══
s = prs.slides.add_slide(prs.slide_layouts[6])
hdr(s, "Project Summary - By the Numbers", "")
metrics = [("6","Specialist\nAI Agents",C1),("7","Intent\nCategories",C2),("8+","Supabase\nDB Tables",C3),
           ("5","Streamlit\nPages",OR),("3","User Roles\n(RBAC)",YL),("2","LLM Providers\nConfigured",RD),
           ("20+","Python\nModules",C1),("1000+","Lines of\nAgent Code",C2)]
for i, (n, l, c) in enumerate(metrics):
    r = rect(s, Inches(0.8)+(i%4)*Inches(3.1), Inches(2.3)+(i//4)*Inches(2.5), Inches(2.8), Inches(2.1), CARD)
    tf = r.text_frame; tf.word_wrap = True; tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]; p.text = n; p.font.size = Pt(44); p.font.bold = True; p.font.color.rgb = c; p.alignment = PP_ALIGN.CENTER
    lp = tf.add_paragraph(); lp.text = l; lp.font.size = Pt(14); lp.font.color.rgb = G; lp.alignment = PP_ALIGN.CENTER; lp.space_before = Pt(6)

# ═══ SLIDE 23: Thank You ═══
s = prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
rect(s, Inches(0), Inches(0), Inches(0.08), SH, C2)
bar(s, Inches(4.5), Inches(2.5), Inches(4.3), C1)
tb(s, Inches(1.5), Inches(2.7), Inches(10), Inches(1.2), "Thank You!", 52, True, W, PP_ALIGN.CENTER)
tb(s, Inches(1.5), Inches(4.0), Inches(10), Inches(0.8), "Questions & Discussion", 28, False, C2, PP_ALIGN.CENTER)
bar(s, Inches(5), Inches(4.9), Inches(3.3), C2)
tb(s, Inches(1.5), Inches(5.2), Inches(10), Inches(0.5), "Labi V Abraham  |  HR Agentic AI  |  September 2026", 16, False, G, PP_ALIGN.CENTER)
tb(s, Inches(1.5), Inches(5.8), Inches(10), Inches(0.5), "Built with LangGraph, Gemini AI, ChromaDB, Streamlit & Supabase", 13, False, G, PP_ALIGN.CENTER)

# ═══ SAVE ═══
out = "/Users/labi/Documents/hr-agentic-ai copy/HR_Agentic_AI_Presentation.pptx"
prs.save(out)
print(f"\n✅ Presentation saved to: {out}")
print(f"📊 Total slides: {len(prs.slides)}")
