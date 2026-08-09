import os
import tempfile
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader

# Dependency Injection
from app.utils.dependencies import (
    get_authorization_service, 
    get_session_manager, 
    get_chat_repo
)

# Agents imports
from app.agents.graph.workflow import get_graph
from app.agents.rag.build_vectorstore import build_vectorstore
from app.agents.rag.retriever import (
    get_retriever,
    get_vectorstore,
)
authz = get_authorization_service()
authz.require_auth()

session_manager = get_session_manager()
chat_repo = get_chat_repo()
profile = session_manager.get_current_profile()

st.title("🤖 HR Agentic AI - Chat")
st.caption(f"Welcome, {profile.name}! (Role: {profile.role.value})")

CHAT_CSS = """
<style>
[data-testid="stChatMessage"] {
    margin-bottom: 0.35rem !important;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    display: flex !important;
    width: 100% !important;
}

[data-testid="stChatMessageContent"] {
    padding: 0.65rem 1rem !important;
    border-radius: 1.1rem !important;
    max-width: 62% !important;
    width: fit-content !important;
    line-height: 1.5;
    flex-shrink: 0;
}

/* ---- USER: right-aligned blue bubble ---- */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse !important;
    justify-content: flex-start !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: #2b6cb0 !important;
    color: #ffffff !important;
    margin-left: auto !important;
    margin-right: 0 !important;
    border-bottom-right-radius: 0.25rem;
}
[data-testid="stChatMessageAvatarUser"] {
    display: none !important;
}

/* ---- ASSISTANT: left-aligned dark bubble ---- */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    flex-direction: row !important;
    justify-content: flex-start !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    background: #262730 !important;
    color: #f0f0f0 !important;
    margin-right: auto !important;
    margin-left: 0 !important;
    border-bottom-left-radius: 0.25rem;
}
[data-testid="stChatMessageAvatarAssistant"] {
    display: none !important;
}

[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span {
    color: inherit !important;
}

.assistant-result-card {
    background: #262730 !important;
    border-radius: 1rem;
    padding: 1rem 1.25rem;
    margin: 0.25rem 0 0.75rem 0;
    max-width: 62%;
}
.assistant-result-card [data-testid="stMetricLabel"],
.assistant-result-card [data-testid="stMetricValue"] {
    color: #f0f0f0 !important;
}
</style>
"""
st.markdown(CHAT_CSS, unsafe_allow_html=True)

# ==================================================
# Session State for Chat
# ==================================================
import uuid
query_params = st.query_params
if "session_id" in query_params:
    st.session_state.current_session_id = query_params["session_id"]
elif "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.query_params["session_id"] = st.session_state.current_session_id

session_key = f"messages_{profile.id}_{st.session_state.current_session_id}"

if session_key not in st.session_state:
    # Load history from Supabase
    db_history = chat_repo.get_history(profile.id, st.session_state.current_session_id)
    st.session_state[session_key] = []
    for msg in db_history:
        st.session_state[session_key].append({"role": "user", "content": msg.get("question")})
        st.session_state[session_key].append({"role": "assistant", "content": msg.get("response")})

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "request_role" not in st.session_state:
    st.session_state.request_role = None

# Removed show_role_dropdown state

# ==================================================
# Sidebar: Chat History
# ==================================================
with st.sidebar:
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.current_session_id = new_id
        st.query_params["session_id"] = new_id
        st.rerun()
        
    st.divider()
    st.markdown("### Recent Conversations")
    
    sessions = chat_repo.get_sessions(profile.id)
    
    if sessions:
        for sess in sessions:
            sid = sess.get("session_id")
            if not sid:
                continue
            question = sess.get("question") or "Empty Chat"
            title = question[:25] + ("..." if len(question) > 25 else "")
            
            # Highlight active conversation
            btn_type = "primary" if sid == st.session_state.current_session_id else "secondary"
            if st.button(f"💬 {title}", key=f"sess_{sid}", use_container_width=True, type=btn_type):
                st.session_state.current_session_id = sid
                st.query_params["session_id"] = sid
                st.rerun()
    else:
        st.info("No previous conversations.")

    st.divider()
    if st.button("🗑 Clear Current Chat", use_container_width=True):
        st.session_state[session_key] = []
        st.rerun()

# ==================================================
# Display Chat History
# ==================================================
for message in st.session_state[session_key]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("bulk_results"):
            st.markdown("### Candidate Details")
            rec_emoji = {"Selected": "✅", "Hold": "🟡", "Rejected": "❌", "Error": "⚠️"}
            for r in message["bulk_results"]:
                emoji = rec_emoji.get(r["recommendation"], "")
                with st.expander(f"{r['candidate_name']} — {r['match_percentage']}% {emoji} {r['recommendation']}"):
                    st.write(r["analysis"])
                    if r.get("scorecard"):
                        st.markdown("**Scorecard**")
                        for item in r["scorecard"]:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"{item['criterion']}")
                                st.caption(item['justification'])
                            with col2:
                                st.progress(item['score'] / 100, text=f"{item['score']}%")
                    if r.get("suggested_questions"):
                        st.markdown("**Suggested Interview Questions:**")
                        for q in r["suggested_questions"]:
                            st.markdown(f"- {q}")

# ==================================================
# ==================================================
# Chat Input & Request Role UI
# ==================================================
from app.utils.dependencies import get_backend_container
client = get_backend_container()["supabase_service"].get_admin_client()

res = client.table("knowledge_bases").select("id,name,type").eq("is_active", True).execute()
kbs = sorted(list(set(r["name"] for r in res.data))) if res.data else []

import json

current_req_role = st.session_state.get('request_role')
js_req_role = f"'{current_req_role}'" if current_req_role else "null"

js_code = f"""
<script>
(function() {{
    const parent = window.parent.document;
    
    const dropdown = parent.createElement('div');
    dropdown.style.position = 'absolute';
    dropdown.style.bottom = '100%'; 
    dropdown.style.left = '0';
    dropdown.style.width = '100%';
    dropdown.style.backgroundColor = 'var(--secondary-background-color, #ffffff)';
    dropdown.style.color = 'var(--text-color, #31333F)';
    dropdown.style.border = '1px solid var(--faded-text-60, #d3d3d3)';
    dropdown.style.borderRadius = '0.5rem';
    dropdown.style.marginBottom = '0.5rem';
    dropdown.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
    dropdown.style.display = 'none';
    dropdown.style.zIndex = '999999';
    dropdown.style.maxHeight = '250px';
    dropdown.style.overflowY = 'auto';
    
    let currentState = 'none';
    let selectedRole = sessionStorage.getItem('selectedRole') || null;
    
    const streamlitRole = {js_req_role};
    if (streamlitRole !== null) {{
        selectedRole = streamlitRole;
        sessionStorage.setItem('selectedRole', selectedRole);
    }} else {{
        selectedRole = null;
        sessionStorage.removeItem('selectedRole');
    }}
    
    const baseCommands = [
        {{cmd: '/role', desc: 'Evaluate resume against a specific role'}},
        {{cmd: '/help', desc: 'Show available commands'}},
        {{cmd: '/clear', desc: 'Clear request role context'}},
        {{cmd: '/new', desc: 'Start a new chat'}},
        {{cmd: '/history', desc: 'View chat history'}},
        {{cmd: '/logout', desc: 'Log out'}}
    ];
    const roleList = {json.dumps(kbs)};
    console.log('Loaded knowledge bases:', roleList);
    
    function getIcon(role) {{
        if (role === 'General HR') return '📚';
        if (role.includes('Software')) return '💻';
        if (role.includes('React')) return '⚛️';
        if (role.includes('Python')) return '🐍';
        if (role.includes('QA')) return '🧪';
        if (role.includes('DevOps')) return '⚙️';
        if (role.includes('Data')) return '📊';
        if (role.includes('Designer') || role.includes('UX')) return '🎨';
        return '📝';
    }}
    
    let currentItems = [];
    let highlightedIndex = 0;
    
    function renderDropdown() {{
        if (currentItems.length === 0 || currentState === 'none') {{
            dropdown.style.display = 'none';
            return;
        }}
        dropdown.style.display = 'block';
        let html = '<ul style="list-style-type: none; margin: 0; padding: 0.5rem 0;">';
        
        currentItems.forEach((item, idx) => {{
            const isSelected = idx === highlightedIndex;
            const bg = isSelected ? 'var(--primary-color, #ff4b4b)' : 'transparent';
            const color = isSelected ? 'white' : 'inherit';
            
            if (currentState === 'command') {{
                html += `<li style="padding: 0.5rem 1rem; cursor: pointer; display: flex; flex-direction: column; background-color: ${{bg}}; color: ${{color}};" data-index="${{idx}}">
                    <span style="font-weight: bold;">${{item.cmd}}</span>
                    <span style="font-size: 0.85rem; opacity: 0.8;">${{item.desc}}</span>
                </li>`;
            }} else if (currentState === 'role') {{
                html += `<li style="padding: 0.5rem 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; background-color: ${{bg}}; color: ${{color}};" data-index="${{idx}}">
                    <span style="font-size: 1.2rem;">${{getIcon(item)}}</span>
                    <span style="font-weight: 500;">${{item}}</span>
                </li>`;
            }}
        }});
        html += '</ul>';
        dropdown.innerHTML = html;
    }}

    function showHelpModal() {{
        let modal = parent.document.getElementById('custom-help-modal');
        if (!modal) {{
            modal = parent.document.createElement('div');
            modal.id = 'custom-help-modal';
            modal.style.position = 'fixed';
            modal.style.top = '50%';
            modal.style.left = '50%';
            modal.style.transform = 'translate(-50%, -50%)';
            modal.style.backgroundColor = 'var(--secondary-background-color, #ffffff)';
            modal.style.color = 'var(--text-color, #31333F)';
            modal.style.padding = '2rem';
            modal.style.borderRadius = '0.5rem';
            modal.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.1)';
            modal.style.zIndex = '9999999';
            modal.style.maxWidth = '500px';
            modal.style.width = '100%';
            modal.style.border = '1px solid var(--faded-text-60, #d3d3d3)';
            
            const html = `
                <h2 style="margin-top:0;">Available Commands</h2>
                <div style="margin-bottom: 1.5rem;">
                    <div style="font-weight:bold; font-size: 1.1rem; margin-bottom:0.25rem;">/role &lt;Knowledge Base&gt;</div>
                    <div style="opacity: 0.8;">Evaluate resume against a specific role</div>
                </div>
                <div style="margin-bottom: 1.5rem;">
                    <h4 style="margin:0 0 0.5rem 0;">Examples</h4>
                    <div style="background: var(--background-color, #f0f2f6); padding: 0.5rem; border-radius: 4px; font-family: monospace; margin-bottom:0.25rem;">/role React Developer Evaluate this resume</div>
                    <div style="background: var(--background-color, #f0f2f6); padding: 0.5rem; border-radius: 4px; font-family: monospace;">/role Software Engineer Compare candidate with JD</div>
                </div>
                <div style="opacity: 0.8; font-size: 0.9rem;">
                    General HR questions do NOT require /role.
                </div>
                <button id="close-help-modal" style="margin-top:1.5rem; padding:0.5rem 1rem; border:none; background:var(--primary-color,#ff4b4b); color:white; border-radius:4px; cursor:pointer;">Close</button>
            `;
            modal.innerHTML = html;
            
            const overlay = parent.document.createElement('div');
            overlay.id = 'custom-help-overlay';
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
            overlay.style.zIndex = '9999998';
            
            parent.document.body.appendChild(overlay);
            parent.document.body.appendChild(modal);
            
            const closeBtn = modal.querySelector('#close-help-modal');
            closeBtn.addEventListener('click', () => {{
                modal.remove();
                overlay.remove();
            }});
            overlay.addEventListener('click', () => {{
                modal.remove();
                overlay.remove();
            }});
        }}
    }}

    let activeTextarea = null;

    function executeSelection(index) {{
        if (!activeTextarea) return;
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;

        if (currentState === 'command') {{
            const cmd = currentItems[index].cmd;
            if (cmd === '/role') {{
                nativeInputValueSetter.call(activeTextarea, '/role ');
                activeTextarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                activeTextarea.selectionStart = activeTextarea.selectionEnd = activeTextarea.value.length;
            }} else if (cmd === '/help') {{
                nativeInputValueSetter.call(activeTextarea, '');
                activeTextarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                dropdown.style.display = 'none';
                showHelpModal();
            }} else {{
                nativeInputValueSetter.call(activeTextarea, cmd);
                activeTextarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                dropdown.style.display = 'none';
                currentState = 'none';
                activeTextarea.selectionStart = activeTextarea.selectionEnd = activeTextarea.value.length;
            }}
        }} else if (currentState === 'role') {{
            const role = currentItems[index];
            selectedRole = role;
            sessionStorage.setItem('selectedRole', role);
            nativeInputValueSetter.call(activeTextarea, '/role ' + role + ' ');
            activeTextarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            dropdown.style.display = 'none';
            currentState = 'none';
            activeTextarea.selectionStart = activeTextarea.selectionEnd = activeTextarea.value.length;
        }}
        activeTextarea.focus();
    }}

    function updateFilter() {{
        if (!activeTextarea) return;
        const val = activeTextarea.value;
        
        if (selectedRole && !val.toLowerCase().startsWith(`/role ${{selectedRole.toLowerCase()}}`)) {{
            selectedRole = null;
            sessionStorage.removeItem('selectedRole');
        }}
        
        if (selectedRole) {{
            currentState = 'none';
            currentItems = [];
            dropdown.style.display = 'none';
            return;
        }}
        
        let searchStr = '';
        const sortedRoles = [...roleList].sort((a, b) => b.length - a.length);
        const matchedRole = sortedRoles.find(r => val.toLowerCase().startsWith(`/role ${{r.toLowerCase()}} `));
        
        if (matchedRole) {{
            selectedRole = matchedRole;
            sessionStorage.setItem('selectedRole', selectedRole);
            currentState = 'none';
            currentItems = [];
            dropdown.style.display = 'none';
            return;
        }}
        
        if (val.startsWith('/role')) {{
            currentState = 'role';
            searchStr = val.substring(5).trim().toLowerCase();
            currentItems = roleList.filter(r => r.toLowerCase().includes(searchStr));
            console.log(`Autocomplete active: true`);
        }} else if (val.startsWith('/')) {{
            currentState = 'command';
            searchStr = val.toLowerCase();
            currentItems = baseCommands.filter(c => c.cmd.startsWith(searchStr));
            console.log(`Autocomplete active: true`);
        }} else {{
            currentState = 'none';
            currentItems = [];
        }}

        if (highlightedIndex >= currentItems.length) highlightedIndex = 0;
        renderDropdown();
    }}

    const onInput = (e) => {{
        updateFilter();
    }};

    const onKeyDown = (e) => {{
        if (dropdown.style.display === 'block' && currentItems.length > 0) {{
            if (e.key === 'ArrowDown') {{
                e.preventDefault();
                e.stopPropagation();
                highlightedIndex = (highlightedIndex + 1) % currentItems.length;
                renderDropdown();
            }} else if (e.key === 'ArrowUp') {{
                e.preventDefault();
                e.stopPropagation();
                highlightedIndex = (highlightedIndex - 1 + currentItems.length) % currentItems.length;
                renderDropdown();
            }} else if (e.key === 'Enter' || e.key === 'Tab') {{
                e.preventDefault();
                e.stopImmediatePropagation();
                e.stopPropagation();
                executeSelection(highlightedIndex);
            }} else if (e.key === 'Escape') {{
                e.preventDefault();
                e.stopPropagation();
                dropdown.style.display = 'none';
                currentState = 'none';
            }}
        }}
    }};

    dropdown.addEventListener('mousedown', (e) => {{
        e.preventDefault();
    }});

    dropdown.addEventListener('click', (e) => {{
        const li = e.target.closest('li');
        if (li) {{
            const idx = parseInt(li.getAttribute('data-index'));
            executeSelection(idx);
        }}
    }});

    function hookTextarea() {{
        const textarea = parent.querySelector('[data-testid="stChatInputTextArea"]') || parent.querySelector('.stChatInput textarea');
        if (!textarea) return;
        
        const container = textarea.closest('[data-testid="stChatInput"]');
        if (!container) return;
        
        if (activeTextarea === textarea && container.contains(dropdown)) {{
            return;
        }}
        
        if (activeTextarea && activeTextarea !== textarea) {{
            activeTextarea.removeEventListener('input', onInput);
            activeTextarea.removeEventListener('keydown', onKeyDown, true);
        }}
        
        activeTextarea = textarea;
        activeTextarea.addEventListener('input', onInput);
        activeTextarea.addEventListener('keydown', onKeyDown, true);
        
        container.style.position = 'relative';
        if (!container.contains(dropdown)) {{
            container.appendChild(dropdown);
        }}
    }}

    const observer = new MutationObserver(() => {{
        hookTextarea();
    }});
    observer.observe(parent.body, {{ childList: true, subtree: true }});
    
    hookTextarea();

}})();
</script>
"""
import streamlit.components.v1 as components
components.html(js_code, height=0)
accept_file = authz.can_review_resumes()
prompt = st.chat_input("Ask the HR Agent...", accept_file="multiple" if accept_file else False, file_type=["pdf"] if accept_file else None)

# ==================================================
# Bulk-ranking helpers
# ==================================================

def extract_role_from_query(text: str, available_kbs: list) -> str | None:
    """Return the first KB name found inside *text*, longest match wins."""
    if not text:
        return None
    lower = text.lower()
    for kb in sorted(available_kbs, key=len, reverse=True):
        if kb.lower() in lower:
            return kb
    return None


def run_bulk_ranking(files, role_name: str, available_kbs: list) -> list:
    """
    Evaluate each PDF in *files* against *role_name* and return a list of dicts:
        {candidate_name, match_percentage, recommendation, analysis, suggested_questions}

    Reuses the same structured-output call and vectorstore retrieval as
    candidate_evaluator in node.py — no duplicate evaluation logic.
    """
    import tempfile
    from langchain_community.document_loaders import PyPDFLoader
    from app.utils.config import get_llm
    from app.models.models import CandidateEvaluation
    from app.agents.rag.retriever import get_vectorstore
    from app.utils.dependencies import get_backend_container

    # Resolve kb_id exactly as candidate_evaluator does
    client = get_backend_container()["supabase_service"].get_admin_client()
    res_kb = client.table("knowledge_bases").select("id").eq("name", role_name).execute()
    kb_id = res_kb.data[0]["id"] if res_kb.data else "unknown"

    structured_llm = get_llm().with_structured_output(CandidateEvaluation)
    vs = get_vectorstore()

    results = []
    for uploaded_file in files:
        filename_fallback = uploaded_file.name
        try:
            # Extract text via PyPDFLoader (same pattern as single-resume branch)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                pdf_path = tmp.name

            pages = PyPDFLoader(pdf_path).load()
            resume_text = "\n".join(p.page_content for p in pages)

            # Retrieve role context (same filter pattern as candidate_evaluator)
            print("============================")
            print("REQUEST (BULK)")
            print("============================")
            print("\nCandidate File:")
            print(filename_fallback)
            print("\nIntent:")
            print("resume (bulk)")
            print("\nKnowledge Base:")
            print(role_name)
            print("\nKnowledge Base ID:")
            print(kb_id)
            print("\n{")
            print("    \"knowledge_base_id\":")
            print(f"    \"{kb_id}\"")
            print("}")

            docs_and_scores = vs.similarity_search_with_score(
                f"Evaluate candidate for {role_name}",
                k=10,
                filter={"knowledge_base_id": {"$in": [kb_id]}},
            )
            documents = [d for d, _ in docs_and_scores]

            print("\nChunks Retrieved:")
            print(len(documents))

            if not documents:
                print("\nNo chunks retrieved.")

            docs_names = list(set(doc.metadata.get('filename', 'Unknown') for doc in documents))
            print("\nFiles:")
            for name in docs_names:
                print(name)
            print()

            for i, (doc, score) in enumerate(docs_and_scores, 1):
                print(f"Chunk {i}")
                print("\nSource:")
                print(doc.metadata.get("filename", "Unknown"))
                print("\nScore:")
                print(f"{score:.2f}")
                print()

            kb_context = ""
            if documents:
                kb_context = "\n\nRole Knowledge Base Context:\n" + "\n\n".join(
                    f"--- {doc.metadata.get('filename', 'Doc')} ---\n{doc.page_content}"
                    for doc in documents
                )

            # Same evaluation prompt as candidate_evaluator
            eval_prompt = f"""You are a Senior HR Recruitment Specialist.

Evaluate the resume below against the role: {role_name}

RESUME:
{resume_text}
{kb_context}

REQUEST:
Evaluate this candidate for the {role_name} role.

OUTPUT RULES (strictly enforced):
1. candidate_name: extract the candidate's full name from the resume text. Default to 'Unknown Candidate' if not found.
2. match_percentage: integer 0-100.
3. recommendation: MUST be exactly one of "Selected", "Rejected", or "Hold". No other wording.
4. analysis: 2-4 sentences ONLY. Summarise key fit factors and major gaps. \
   Do NOT include interview questions, coaching tips, or candidate-facing text here.
5. suggested_questions: at most 5 short interview questions targeted at this candidate's \
   specific gaps. Leave empty if none are warranted.
6. final_answer: ONE sentence (max 25 words) suitable as a chat reply.
7. scorecard: Break down the evaluation into 3-6 specific criteria relevant to THIS role \
   (derive criteria from the role knowledge base content provided above, not a generic fixed list). \
   Each criterion needs a 0-100 score and a one-sentence justification grounded in the resume \
   and role requirements.
"""
            result = structured_llm.invoke(eval_prompt)
            candidate_name = result.candidate_name or filename_fallback

            print("-" * 33)
            print(f"Candidate: {filename_fallback}")
            print(f"Detected Name: {candidate_name}")
            print(f"Detected Match: {result.match_percentage}%")
            print(f"Recommendation: {result.recommendation}")
            print("-" * 33)
            
            # Save to Supabase (so bulk candidates exist for onboarding lookup)
            try:
                from app.utils.dependencies import get_session_manager
                auth_user_id = None
                try:
                    session_manager = get_session_manager()
                    profile = session_manager.get_current_profile()
                    if profile:
                        auth_user_id = profile.auth_user_id
                except Exception:
                    pass

                db_payload = {
                    "candidate_name": candidate_name,
                    "applied_role": role_name,
                    "ats_score": result.match_percentage,
                    "overall_score": result.match_percentage,
                    "recommendation": result.recommendation,
                    "strengths": [],
                    "weaknesses": [],
                    "missing_skills": [],
                    "interview_questions": result.suggested_questions or [],
                    "evaluation_json": result.model_dump(),
                }
                if auth_user_id:
                    db_payload["created_by"] = auth_user_id

                from app.utils.dependencies import get_backend_container
                container = get_backend_container()
                supabase_service = container["supabase_service"]
                supabase_service.insert_evaluation(db_payload)
            except Exception as e:
                import logging
                logging.error(f"Failed to insert bulk evaluation: {e}")

            results.append({
                "candidate_name": candidate_name,
                "match_percentage": result.match_percentage,
                "recommendation": result.recommendation,
                "analysis": result.analysis,
                "suggested_questions": result.suggested_questions or [],
                "scorecard": [item.model_dump() for item in (result.scorecard or [])],
            })
        except Exception as exc:
            results.append({
                "candidate_name": filename_fallback,
                "match_percentage": 0,
                "recommendation": "Error",
                "analysis": str(exc),
                "suggested_questions": [],
            })
    return results


def format_bulk_ranking_report(results: list, role_name: str):
    """
    Return a (report_md, sorted_results) tuple:
    - report_md: markdown table only (header + table rows). No HTML.
    - sorted_results: list of result dicts sorted by match_percentage descending,
      used by the caller to render native st.expander() blocks.
    """
    sorted_results = sorted(results, key=lambda r: r["match_percentage"], reverse=True)

    rec_emoji = {"Selected": "✅", "Hold": "🟡", "Rejected": "❌", "Error": "⚠️"}

    lines = [
        f"## 📊 Bulk Ranking Results — {role_name}",
        f"*{len(results)} candidate(s) evaluated, ranked by match percentage.*",
        "",
        "| # | Candidate | Match % | Recommendation |",
        "|---|-----------|---------|----------------|",
    ]
    for i, r in enumerate(sorted_results, 1):
        emoji = rec_emoji.get(r["recommendation"], "")
        lines.append(
            f"| {i} | {r['candidate_name']} "
            f"| {r['match_percentage']}% "
            f"| {emoji} {r['recommendation']} |"
        )

    selected_names = [r["candidate_name"] for r in sorted_results if r["recommendation"] == "Selected"]
    if selected_names:
        lines.append(f"\n💡 {', '.join(selected_names)} {'was' if len(selected_names)==1 else 'were'} selected — want me to start onboarding for any of them? Just ask, e.g. \"start onboarding for {selected_names[0]}\".")

    return "\n".join(lines), sorted_results

if prompt and getattr(prompt, 'files', None):
    if len(prompt.files) == 1:
        uploaded_resume = prompt.files[0]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_resume.read())
            pdf_path = temp_pdf.name

        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        st.session_state.resume_text = "\n".join(page.page_content for page in pages)
        
        # Classify document
        from app.utils.config import get_llm
        llm = get_llm()
        class_prompt = f"Analyze the following text from an uploaded document. Classify it EXACTLY as one of the following: 'Resume', 'Job Description', 'HR Policy', 'Employee Handbook', or 'Unknown PDF'. Return ONLY the classification name.\n\nText: {st.session_state.resume_text[:2000]}"
        try:
            doc_type = llm.invoke(class_prompt).content.strip()
        except:
            doc_type = "Unknown PDF"
            
        if "Resume" in doc_type:
            # Auto-detect the best-fit role from the available knowledge bases
            detected_role = None
            try:
                role_prompt = f"""You are matching a resume to the best-fit job role.

Available roles: {', '.join(kbs)}

Resume text:
{st.session_state.resume_text[:3000]}

Return ONLY the exact role name from the list above that best matches this resume. If no role is a clear match, return "General HR". Return nothing else — just the role name."""
                detected = llm.invoke(role_prompt).content.strip()
                # Validate against the actual kb list to avoid hallucinated role names
                if detected in kbs:
                    detected_role = detected
            except Exception:
                detected_role = None

            if detected_role and detected_role != "General HR":
                st.session_state.request_role = detected_role
                _upload_msg = f"✅ Resume detected and loaded. Based on its content, I've matched it to **{detected_role}** — ask me to evaluate it, or type `/role` to pick a different role."
                st.session_state[session_key].append({
                    "role": "assistant",
                    "content": _upload_msg,
                })
            else:
                _upload_msg = "✅ Resume detected and loaded into context. I couldn't confidently match it to a specific role — type `/role` to select one for evaluation."
                st.session_state[session_key].append({
                    "role": "assistant",
                    "content": _upload_msg,
                })
            chat_repo.save_message(
                user_id=profile.id,
                session_id=st.session_state.current_session_id,
                question="[Resume Upload]",
                response=_upload_msg,
                agent_used="RESUME",
                llm_used="gemini-2.5-flash"
            )
        elif "Job Description" in doc_type:
            st.session_state[session_key].append({"role": "assistant", "content": "Job Description detected. Please specify which knowledge base it belongs to by using the `/knowledge` command."})
        elif "Employee Handbook" in doc_type or "HR Policy" in doc_type:
            st.session_state[session_key].append({"role": "assistant", "content": f"{doc_type} detected. Suggest adding to General HR knowledge base via the `/knowledge` command."})
        else:
            st.session_state[session_key].append({"role": "assistant", "content": "Unknown PDF detected. What would you like to do with it? (Consider adding it via `/knowledge`)"})

        if prompt.text and prompt.text.strip():
            st.session_state["_pending_query_after_upload"] = prompt.text.strip()
        else:
            st.rerun()
    else:
        # ── Bulk ranking path (2+ files) ──────────────────────────────────
        bulk_role = extract_role_from_query(prompt.text or "", kbs)
        if not bulk_role:
            st.session_state[session_key].append({
                "role": "assistant",
                "content": (
                    f"I see **{len(prompt.files)} resumes** attached. "
                    "Which role should I rank them against? "
                    "Reply like: *'rank these for React Developer'*."
                ),
            })
            st.session_state["_pending_bulk_files"] = prompt.files
            st.rerun()
        else:
            with st.spinner(f"Ranking {len(prompt.files)} candidates for **{bulk_role}**..."):
                results = run_bulk_ranking(prompt.files, bulk_role, kbs)
            report_md, sorted_results = format_bulk_ranking_report(results, bulk_role)
            chat_repo.save_message(
                user_id=profile.id,
                session_id=st.session_state.current_session_id,
                question=prompt.text or f"Bulk resume ranking — {bulk_role}",
                response=report_md,
                agent_used="RESUME",
                llm_used="gemini-2.5-flash"
            )
            st.session_state[session_key].append({"role": "assistant", "content": report_md, "bulk_results": sorted_results})
            st.rerun()

if "_pending_query_after_upload" in st.session_state:
    query = st.session_state.pop("_pending_query_after_upload")
else:
    query = prompt.text if prompt else None

# Handle simulated query removed

if query:
    # ── Pending bulk-files follow-up ─────────────────────────────────────
    if st.session_state.get("_pending_bulk_files"):
        bulk_role = extract_role_from_query(query, kbs)
        if bulk_role:
            pending_files = st.session_state.pop("_pending_bulk_files")
            with st.spinner(f"Ranking {len(pending_files)} candidates for **{bulk_role}**..."):
                results = run_bulk_ranking(pending_files, bulk_role, kbs)
            report_md, sorted_results = format_bulk_ranking_report(results, bulk_role)
            chat_repo.save_message(
                user_id=profile.id,
                session_id=st.session_state.current_session_id,
                question=query or f"Bulk resume ranking — {bulk_role}",
                response=report_md,
                agent_used="RESUME",
                llm_used="gemini-2.5-flash"
            )
            st.session_state[session_key].append({"role": "assistant", "content": report_md, "bulk_results": sorted_results})
            st.rerun()
        # No role found → fall through to normal query handling unchanged

    if query.startswith("/role ") or query.strip() == "/role":
        if query.startswith("/role "):
            query_stripped = query[6:].strip()
            matched_role = None
            
            for kb in sorted(kbs, key=len, reverse=True):
                if query_stripped.lower().startswith(kb.lower()):
                    matched_role = kb
                    query = query_stripped[len(kb):].strip()
                    break
                    
            if matched_role:
                st.session_state.request_role = matched_role
        
        if query.strip() == "/role":
            query = ""
            
    if not query.strip():
        if not st.session_state.get("request_role"):
            st.session_state[session_key].append({"role": "assistant", "content": "Please type `/role` and select a role from the dropdown menu, then add your prompt."})
        else:
            st.session_state[session_key].append({"role": "assistant", "content": f"Active role is **{st.session_state.request_role}**. Please provide a prompt."})
        st.rerun()

    if query.startswith("/"):
        cmd = query.split()[0].lower()
        if cmd == "/help":
            st.session_state[session_key].append({"role": "assistant", "content": "Please use the floating help menu by typing `/help` in the input box."})
            st.rerun()
        elif cmd == "/clear":
            st.session_state.request_role = None
            st.session_state[session_key].append({"role": "assistant", "content": "Cleared request role context."})
            st.rerun()
        elif cmd == "/knowledge":
            st.session_state["show_kb_manager"] = True
            st.session_state[session_key].append({"role": "assistant", "content": "Opened Knowledge Base Manager in sidebar/dialog."})
            st.rerun()
        elif cmd == "/collections":
            from app.utils.dependencies import get_knowledge_base_service
            docs = get_knowledge_base_service().list_documents()
            kbs_list = set(d.get('kb_name', 'General HR') for d in docs)
            st.session_state[session_key].append({"role": "assistant", "content": f"Available Knowledge Bases:\n- " + "\n- ".join(kbs_list)})
            st.rerun()
        else:
            st.session_state[session_key].append({"role": "assistant", "content": f"Unknown command: {cmd}"})
            st.rerun()

    display_query = f"**[{st.session_state.request_role}]**\n{query}" if st.session_state.get("request_role") else query
    st.session_state[session_key].append({"role": "user", "content": display_query})
    with st.chat_message("user"):
        st.markdown(display_query)

    resume_required = any(word in query.lower() for word in ["resume", "candidate", "screen", "evaluate", "recruitment", "shortlist"])
    role_context_required = resume_required or any(word in query.lower() for word in ["interview question", "role", "position", "job description", "requirements"])

    if resume_required:
        if not authz.can_review_resumes():
            answer = "⚠️ You do not have permission to perform resume reviews."
            with st.chat_message("assistant"):
                st.error(answer)
            st.session_state[session_key].append({"role": "assistant", "content": answer})
            st.stop()
        elif not st.session_state.resume_text:
            answer = "⚠️ Please upload a resume before requesting candidate evaluation."
            with st.chat_message("assistant"):
                st.warning(answer)
            st.session_state[session_key].append({"role": "assistant", "content": answer})
            st.stop()

    if role_context_required and st.session_state.get("request_role"):
        active_kbs = [st.session_state.request_role]
    else:
        active_kbs = ["General HR"]
        
    print("-" * 33)
    print(f"Selected Role: {st.session_state.get('request_role')}")
    print(f"Clean Query: {query}")
    print(f"Current Role: {st.session_state.get('request_role')}")
    print(f"Active KB: {active_kbs[0]}")
    print(f"Workflow Query: {query}")
    print("-" * 33)
        
    state = {
        "query": query,
        "resume_text": st.session_state.resume_text,
        "current_role": st.session_state.get("request_role"),
        "active_kbs": active_kbs,
        "intent": "",
        "next_node": "",
        "match_percentage": 0,
        "recommendation": "",
        "analysis": "",
        "email": "",
        "policy": "",
        "final_answer": "",
        "execution_log": [],
    }

    with st.spinner("🤖 Thinking..."):
        import time
        start_t = time.time()
        result = get_graph().invoke(state)
        response_time = time.time() - start_t

    answer = result["final_answer"]
    
    intent_map = {
        "policy": "HR_POLICY",
        "general": "GENERAL",
        "resume": "RESUME",
        "recruitment": "RESUME",
        "email": "EMAIL",
        "onboarding": "GENERAL",  # Maps to GENERAL; agent_type enum does not include ONBOARDING
    }
    db_agent_used = intent_map.get(result.get("intent", "general"), "GENERAL")
    
    # Save to Supabase Chat History
    chat_repo.save_message(
        user_id=profile.id,
        session_id=st.session_state.current_session_id,
        question=query,
        response=answer,
        agent_used=db_agent_used,
        llm_used="gemini-2.5-flash"
    )
    
    # Debug Logging
    print("-" * 33)
    print("EXECUTION LOGS")
    print("-" * 33)
    print(f"Detected Intent: {result.get('intent', 'Unknown')}")
    print(f"Selected Knowledge Base: {result.get('active_kbs', ['General HR'])[0] if result.get('intent') in ('resume','recruitment') else 'N/A (no retrieval)'}")
    print(f"Final Answer:\n{answer}\n")
    print(f"Execution time: {response_time:.2f}s")
    print("-" * 33)

    with st.chat_message("assistant"):
        st.markdown(answer)

        if result["intent"] in ["resume", "recruitment"] and authz.can_review_resumes():
            st.markdown('<div class="assistant-result-card">', unsafe_allow_html=True)
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Match Percentage", f'{result["match_percentage"]}%')
            with col2:
                st.metric("Recommendation", result["recommendation"])

            if result["recommendation"].lower() == "selected":
                st.success("✅ Candidate Shortlisted")
                offer_text = f"💡 Want me to start onboarding for **{result.get('evaluation_data', {}).get('candidate_name', 'this candidate')}**? Just ask — e.g. \"start onboarding for {result.get('evaluation_data', {}).get('candidate_name', '')}\"."
                st.markdown(offer_text)
                answer += f"\n\n{offer_text}"
            else:
                st.error("❌ Candidate Rejected")

            with st.expander("📋 Candidate Analysis"):
                st.write(result["analysis"])

            if result.get("evaluation_data", {}).get("scorecard"):
                st.markdown("**Scorecard**")
                for item in result["evaluation_data"]["scorecard"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"{item['criterion']}")
                        st.caption(item['justification'])
                    with col2:
                        st.progress(item['score'] / 100, text=f"{item['score']}%")

            st.markdown('</div>', unsafe_allow_html=True)

        if authz.can_view_logs():
            with st.expander("🔍 Agent Execution Log"):
                for step in result["execution_log"]:
                    st.success(step)

    st.session_state[session_key].append({"role": "assistant", "content": answer})

