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

# ==================================================
# Session State for Chat
# ==================================================
import uuid
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())

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
        st.session_state.current_session_id = str(uuid.uuid4())
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
prompt = st.chat_input("Ask the HR Agent...", accept_file=accept_file, file_type=["pdf"] if accept_file else None)

if prompt and getattr(prompt, 'files', None):
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
        st.session_state[session_key].append({"role": "assistant", "content": "✅ Resume detected and loaded into context. Type `/role` to select a role for evaluation."})
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

if "_pending_query_after_upload" in st.session_state:
    query = st.session_state.pop("_pending_query_after_upload")
else:
    query = prompt.text if prompt else None

# Handle simulated query removed

if query:
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

    if st.session_state.get("request_role"):
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
        "email": "EMAIL"
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
    print(f"Selected Knowledge Base: {result.get('current_role') or 'General HR'}")
    print(f"Final Answer:\n{answer}\n")
    print(f"Execution time: {response_time:.2f}s")
    print("-" * 33)

    with st.chat_message("assistant"):
        st.markdown(answer)

        if result["intent"] in ["resume", "recruitment"] and authz.can_review_resumes():
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Match Percentage", f'{result["match_percentage"]}%')
            with col2:
                st.metric("Recommendation", result["recommendation"])

            if result["recommendation"].lower() == "selected":
                st.success("✅ Candidate Shortlisted")
            else:
                st.error("❌ Candidate Rejected")

            with st.expander("📋 Candidate Analysis"):
                st.write(result["analysis"])

        if authz.can_view_logs():
            with st.expander("🔍 Agent Execution Log"):
                for step in result["execution_log"]:
                    st.success(step)

    st.session_state[session_key].append({"role": "assistant", "content": answer})

