import json

from app.agents.graph.state import AgentState
from app.utils.config import get_llm
from app.models.models import CandidateEvaluation
from app.agents.rag.retriever import get_retriever
from app.prompts.loader import render_prompt

# ==========================================
# Candidate Evaluation Specialist
# ==========================================

def candidate_evaluator(state: AgentState):
    """
    HR Recruitment Specialist

    Evaluates the uploaded resume against the
    provided Job Description and Role Context.
    """

    structured_llm = get_llm().with_structured_output(CandidateEvaluation)

    try:
        kb_name = state.get("current_role") if state.get("current_role") else "General HR"
        from app.utils.dependencies import get_backend_container
        client = get_backend_container()["supabase_service"].get_admin_client()
        res_kb = client.table("knowledge_bases").select("id").eq("name", kb_name).execute()
        kb_id = res_kb.data[0]["id"] if res_kb.data else "unknown"

        print("============================")
        print("REQUEST")
        print("============================")
        print("\nIntent:")
        print("resume")
        print("\nKnowledge Base:")
        print(kb_name)
        print("\nKnowledge Base ID:")
        print(kb_id)
        print("\n{")
        print("    \"knowledge_base_id\":")
        print(f"    \"{kb_id}\"")
        print("}")

        from app.agents.rag.retriever import get_vectorstore
        vs = get_vectorstore()
        
        docs_and_scores = vs.similarity_search_with_score(state["query"], k=10, filter={"knowledge_base_id": {"$in": [kb_id]}})
        documents = [d for d, s in docs_and_scores]

        # --- RAG citation / confidence (additive) ---
        if docs_and_scores:
            avg_score = sum(s for _, s in docs_and_scores) / len(docs_and_scores)
            source_files = sorted(set(doc.metadata.get('filename', 'Unknown') for doc, _ in docs_and_scores))
        else:
            avg_score = 0
            source_files = []

        if avg_score >= 0.75:
            confidence_badge = "🟢 High Confidence"
        elif avg_score >= 0.5:
            confidence_badge = "🟡 Medium Confidence"
        else:
            confidence_badge = "🔴 Low Confidence"

        knowledge_gap_flag = (not docs_and_scores) or (avg_score < 0.4)

        state["source_files"] = source_files
        state["confidence_badge"] = confidence_badge
        state["knowledge_gap"] = knowledge_gap_flag
        # --- end RAG citation / confidence ---
        
        print("\nChunks Retrieved:")
        print(len(documents))
        
        if not documents:
            print("\nNo chunks retrieved.")
            state["match_percentage"] = 0
            state["recommendation"] = "Unable to Evaluate"
            state["analysis"] = "No role knowledge base chunks were retrieved; cannot evaluate."
            state["suggested_questions"] = []
            state["final_answer"] = "Evaluation could not be completed: no matching knowledge base content found."
            state["evaluation_data"] = {}
            return state

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
            
        prompt = render_prompt(
            "resume_evaluation.j2",
            current_role=state.get('current_role', 'General Candidate'),
            resume_text=state["resume_text"],
            kb_context=kb_context,
            query=state["query"],
        )

        result = structured_llm.invoke(prompt)

        state["match_percentage"] = result.match_percentage
        state["recommendation"] = result.recommendation
        state["analysis"] = result.analysis
        state["suggested_questions"] = result.suggested_questions or []
        state["final_answer"] = result.final_answer
        state["evaluation_data"] = result.model_dump()

        state["execution_log"].append(f"👨\u200d💼 Evaluated candidate for {state.get('current_role')}.")

    except Exception as e:
        state["match_percentage"] = 0
        state["recommendation"] = "Unable to Evaluate"
        state["analysis"] = str(e)
        state["suggested_questions"] = []
        state["final_answer"] = "Resume evaluation failed due to an internal error."
        state["evaluation_data"] = {}
        state["execution_log"].append(f"❌ Candidate Evaluator failed: {e}")

    return state
# ==========================================
# HR Communication Specialist
# ==========================================

def interview_email_generator(state: AgentState):
    """
    HR Communication Specialist

    Generates a professional interview invitation
    for shortlisted candidates.
    """

    prompt = render_prompt(
        "interview_email.j2",
        analysis=state["analysis"],
        match_percentage=state["match_percentage"],
        recommendation=state["recommendation"],
    )

    try:
        response = get_llm().invoke(prompt)
        state["email"] = response.content
        state["execution_log"].append(
    "📧 HR Communication Specialist generated interview invitation."
)

    except Exception as e:
        state["email"] = f"Unable to generate interview email.\n\nError: {str(e)}"
        state["execution_log"].append(f"❌ Interview Email Generator failed: {e}")

    return state

# ==========================================
# HR Policy Specialist
# ==========================================

def hr_policy_specialist(state: AgentState):
    """
    HR Policy Specialist

    Answers HR policy questions using the company's
    employee handbook (RAG).
    """

    try:
        print("\n" + "=" * 50)
        print("[HR Policy Specialist] Starting...")
        print("=" * 50)

        kb_name = "General HR"
        from app.utils.dependencies import get_backend_container
        client = get_backend_container()["supabase_service"].get_admin_client()
        res_kb = client.table("knowledge_bases").select("id").eq("name", kb_name).execute()
        kb_id = res_kb.data[0]["id"] if res_kb.data else "unknown"

        print(f"[Retriever Loaded] KB='{kb_name}', KB_ID='{kb_id}'")

        print("\nIntent: policy")
        print(f"Knowledge Base: {kb_name}")
        print(f"Knowledge Base ID: {kb_id}")

        from app.agents.rag.retriever import get_vectorstore
        vs = get_vectorstore()
        
        # Using similarity search directly to get scores
        docs_and_scores = vs.similarity_search_with_score(state["query"], k=10, filter={"knowledge_base_id": {"$in": [kb_id]}})
        documents = [d for d, s in docs_and_scores]

        # --- RAG citation / confidence (additive) ---
        if docs_and_scores:
            avg_score = sum(s for _, s in docs_and_scores) / len(docs_and_scores)
            source_files = sorted(set(doc.metadata.get('filename', 'Unknown') for doc, _ in docs_and_scores))
        else:
            avg_score = 0
            source_files = []

        if avg_score >= 0.75:
            confidence_badge = "🟢 High Confidence"
        elif avg_score >= 0.5:
            confidence_badge = "🟡 Medium Confidence"
        else:
            confidence_badge = "🔴 Low Confidence"

        knowledge_gap_flag = (not docs_and_scores) or (avg_score < 0.4)

        state["source_files"] = source_files
        state["confidence_badge"] = confidence_badge
        state["knowledge_gap"] = knowledge_gap_flag
        # --- end RAG citation / confidence ---
        
        print(f"\n[Documents Indexed: {vs._collection.count()}]")
        print(f"[Retrieved Chunks: {len(documents)}]")
        
        if not documents:
            print("[WARNING] No chunks retrieved for this query.")
            state["policy"] = "No information found in the knowledge base for this query."
            state["execution_log"].append("⚠️ HR Policy Specialist: no relevant chunks found.")
            return state

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

        context = "\n\n".join(
            f"--- Source: {doc.metadata.get('filename', 'Employee Handbook')} ---\n{doc.page_content}"
            for doc in documents
        )

        prompt = render_prompt(
            "hr_policy.j2",
            context=context,
            query=state["query"],
        )
        print("\n[LLM Selection] Invoking get_llm() for policy response...")

        response = get_llm().invoke(prompt)
        
        print(f"[Response Generated] Length={len(response.content)} chars")
        print(f"[LLM Output Preview] {response.content[:200]}...")

        state["policy"] = response.content
        state["execution_log"].append("📚 HR Policy Specialist answered handbook question.")

    except Exception as e:
        print(f"\n[ERROR] HR Policy Specialist failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

        state["policy"] = (
            "Unable to retrieve HR policy information.\n\n"
            f"Error: {str(e)}"
        )
        state["execution_log"].append(f"❌ HR Policy Specialist failed: {e}")

    return state
# ==========================================
# General HR Assistant
# ==========================================

def general_assistant(state: AgentState):
    try:
        print("\n[General Assistant] Invoking LLM...")
        response = get_llm().invoke(state["query"])
        state["final_answer"] = response.content
        print(f"[General Assistant] Response generated ({len(response.content)} chars)")
    except Exception as e:
        print(f"[ERROR] General Assistant failed: {type(e).__name__}: {e}")
        state["final_answer"] = f"I'm sorry, I encountered an error processing your request.\n\nError: {str(e)}"
        state["execution_log"].append(f"❌ General Assistant failed: {e}")

    return state


# ==========================================
# Onboarding Checklist Tracker
# ==========================================

DEFAULT_ONBOARDING_TASKS = [
    "IT equipment setup",
    "HR paperwork",
    "Welcome meeting",
    "Role-specific training",
    "Team introduction",
]

def onboarding_specialist(state: AgentState):
    """
    Onboarding Checklist Tracker

    Handles three sub-cases driven by query content:
      - START  : "start onboarding" — seeds 5 default checklist rows for a candidate.
      - UPDATE : "mark ... done/complete" — marks a matched task as DONE.
      - STATUS : "onboarding status" / "onboarding checklist" — displays current checklist.
    """

    query_lower = state["query"].lower()

    try:
        from app.utils.dependencies import get_backend_container
        client = get_backend_container()["supabase_service"].get_admin_client()

        # ----------------------------------------------------------
        # Helper: find the most-recent evaluation row for a candidate
        # by case-insensitive name match in the "evaluations" table.
        # (This codebase writes to "evaluations", not "resume_evaluations".)
        # ----------------------------------------------------------
        def find_candidate(name_hint: str):
            """Returns the most-recent evaluation row matching the name hint, or None."""
            res = (
                client.table("evaluations")
                .select("id, candidate_name, recommendation")
                .ilike("candidate_name", f"%{name_hint}%")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None

        # ----------------------------------------------------------
        # Helper: extract a simple name guess from the query.
        # Looks for the first multi-word run after trigger keywords.
        # ----------------------------------------------------------
        def extract_name(query: str) -> str:
            import re
            # Strip common trigger phrases to isolate the name portion
            cleaned = re.sub(
                r"(start onboarding for|start onboarding|onboarding for|mark|done|complete|onboarding status|onboarding checklist)",
                "",
                query,
                flags=re.IGNORECASE,
            ).strip()
            # Remove leading filler words
            cleaned = re.sub(r"^(for|of|candidate|the)\s+", "", cleaned, flags=re.IGNORECASE).strip()
            # Return first 60 chars to avoid overly long names
            return cleaned[:60] if cleaned else ""

        # ----------------------------------------------------------
        # SUB-CASE A — START ONBOARDING
        # ----------------------------------------------------------
        if "start onboarding" in query_lower:
            candidate_name = extract_name(state["query"])

            if not candidate_name:
                state["onboarding_result"] = (
                    "⚠️ I couldn't extract a candidate name from your request. "
                    "Please use a phrase like: *'Start onboarding for Jane Doe'*."
                )
                state["execution_log"].append("⚠️ Onboarding: no candidate name found in query.")
                return state

            candidate_row = find_candidate(candidate_name)

            if not candidate_row:
                state["onboarding_result"] = (
                    f"❌ No evaluation record found for **'{candidate_name}'**. "
                    "Please ensure the candidate has been evaluated first, and use the exact name as stored."
                )
                state["execution_log"].append(f"❌ Onboarding: candidate '{candidate_name}' not found in evaluations.")
                return state
                
            if candidate_row.get("recommendation") != "Selected":
                state["onboarding_result"] = (
                    f"⚠️ {candidate_row['candidate_name']}'s recommendation is currently "
                    f"'{candidate_row.get('recommendation')}', not 'Selected'. Onboarding can "
                    "only be started for selected candidates."
                )
                state["execution_log"].append(f"⚠️ Onboarding: candidate '{candidate_row['candidate_name']}' is not Selected.")
                return state

            cand_id = candidate_row["id"]
            cand_display = candidate_row["candidate_name"]
            state["candidate_id"] = cand_id

            # Insert 5 default checklist rows
            rows = [
                {"candidate_id": cand_id, "task_name": task, "status": "PENDING"}
                for task in DEFAULT_ONBOARDING_TASKS
            ]
            client.table("onboarding_checklists").insert(rows).execute()

            checklist_md = f"## ✅ Onboarding Started: {cand_display}\n\n"
            checklist_md += "| Task | Status |\n|------|--------|\n"
            for task in DEFAULT_ONBOARDING_TASKS:
                checklist_md += f"| {task} | ⏳ PENDING |\n"

            state["onboarding_result"] = checklist_md
            state["execution_log"].append(f"✅ Onboarding started for {cand_display} (id={cand_id}).")

        # ----------------------------------------------------------
        # SUB-CASE B — MARK TASK DONE / COMPLETE
        # ----------------------------------------------------------
        elif "mark" in query_lower and any(w in query_lower for w in ["done", "complete"]):
            import re
            task_keywords = None
            candidate_name_raw = None
            try:
                extraction_prompt = render_prompt(
                    "onboarding_task_extraction.j2",
                    query=state["query"],
                )
                llm_result = get_llm().invoke(extraction_prompt).content.strip()
                lines = llm_result.split("\n")
                for line in lines:
                    if line.startswith("TASK:"):
                        val = line.replace("TASK:", "").strip()
                        if val and val.upper() != "UNKNOWN":
                            task_keywords = val
                    elif line.startswith("CANDIDATE:"):
                        val = line.replace("CANDIDATE:", "").strip()
                        if val and val.upper() != "UNKNOWN":
                            candidate_name_raw = val
            except Exception:
                task_keywords = None
                candidate_name_raw = None

            # Fallback to the existing regex if LLM extraction didn't produce both values
            if not task_keywords or not candidate_name_raw:
                match = re.search(r"mark (.+?) (?:done|complete)(?:\s+for\s+(.+))?", state["query"], re.IGNORECASE)
                if match:
                    task_keywords = task_keywords or match.group(1).strip()
                    candidate_name_raw = candidate_name_raw or (match.group(2).strip() if match.group(2) else None)

            if not candidate_name_raw:
                state["onboarding_result"] = (
                    "⚠️ I couldn't determine which candidate you mean. "
                    "Try: *'Mark IT equipment setup done for Jane Doe'*."
                )
                state["execution_log"].append("⚠️ Onboarding update: no candidate name found.")
                return state

            candidate_row = find_candidate(candidate_name_raw)

            if not candidate_row:
                state["onboarding_result"] = (
                    f"❌ No evaluation record found for **'{candidate_name_raw}'**. "
                    "Please check the candidate name and try again."
                )
                state["execution_log"].append(f"❌ Onboarding update: candidate '{candidate_name_raw}' not found.")
                return state

            cand_id = candidate_row["id"]
            cand_display = candidate_row["candidate_name"]
            state["candidate_id"] = cand_id

            # Fetch existing checklist rows for this candidate
            rows_res = (
                client.table("onboarding_checklists")
                .select("id, task_name, status")
                .eq("candidate_id", cand_id)
                .execute()
            )
            if not rows_res.data:
                state["onboarding_result"] = (
                    f"⚠️ No onboarding checklist found for **{cand_display}**. "
                    f"Start onboarding first with: *'Start onboarding for {cand_display}'*."
                )
                state["execution_log"].append(f"⚠️ Onboarding update: no checklist rows for {cand_display}.")
                return state

            # Fuzzy-match: find the task whose name best matches query keywords
            matched_row = None
            best_score = 0
            for row in rows_res.data:
                task_words = set(row["task_name"].lower().split())
                query_words = set(task_keywords.lower().split()) if task_keywords else set()
                overlap = len(task_words & query_words)
                if overlap > best_score:
                    best_score = overlap
                    matched_row = row

            if not matched_row or best_score == 0:
                task_list = ", ".join(r["task_name"] for r in rows_res.data)
                state["onboarding_result"] = (
                    f"⚠️ Couldn't match a task in your query. Available tasks for **{cand_display}**: {task_list}."
                )
                state["execution_log"].append("⚠️ Onboarding update: no task matched query keywords.")
                return state

            # Update matched task to DONE
            client.table("onboarding_checklists").update(
                {"status": "DONE", "completed_at": "now()"}
            ).eq("id", matched_row["id"]).execute()

            state["onboarding_result"] = (
                f"✅ Marked **'{matched_row['task_name']}'** as **DONE** for **{cand_display}**."
            )
            state["execution_log"].append(
                f"✅ Onboarding: '{matched_row['task_name']}' marked DONE for {cand_display}."
            )

        # ----------------------------------------------------------
        # SUB-CASE C — STATUS / CHECKLIST
        # ----------------------------------------------------------
        else:
            candidate_name = extract_name(state["query"])

            if not candidate_name:
                state["onboarding_result"] = (
                    "⚠️ Please include the candidate name in your request. "
                    "Try: *'Onboarding status for Jane Doe'*."
                )
                state["execution_log"].append("⚠️ Onboarding status: no candidate name found.")
                return state

            candidate_row = find_candidate(candidate_name)

            if not candidate_row:
                state["onboarding_result"] = (
                    f"❌ No evaluation record found for **'{candidate_name}'**."
                )
                state["execution_log"].append(f"❌ Onboarding status: candidate '{candidate_name}' not found.")
                return state

            cand_id = candidate_row["id"]
            cand_display = candidate_row["candidate_name"]
            state["candidate_id"] = cand_id

            rows_res = (
                client.table("onboarding_checklists")
                .select("task_name, status, completed_at")
                .eq("candidate_id", cand_id)
                .order("created_at", desc=False)
                .execute()
            )

            if not rows_res.data:
                state["onboarding_result"] = (
                    f"⚠️ No onboarding checklist found for **{cand_display}**. "
                    f"Start one with: *'Start onboarding for {cand_display}'*."
                )
                state["execution_log"].append(f"⚠️ Onboarding status: no checklist rows for {cand_display}.")
                return state

            status_md = f"## 📋 Onboarding Checklist: {cand_display}\n\n"
            status_md += "| Task | Status |\n|------|--------|\n"
            for row in rows_res.data:
                icon = "✅" if row["status"] == "DONE" else "⏳"
                status_md += f"| {row['task_name']} | {icon} {row['status']} |\n"

            state["onboarding_result"] = status_md
            state["execution_log"].append(f"📋 Onboarding status displayed for {cand_display}.")

    except Exception as e:
        state["onboarding_result"] = (
            f"⚠️ Onboarding action could not be completed.\n\nError: {str(e)}"
        )
        state["execution_log"].append(f"❌ Onboarding Specialist failed: {e}")

    return state


# ==========================================
# Leave Request Specialist
# ==========================================

def leave_specialist(state: AgentState):
    """
    Leave Request Specialist

    Handles four sub-cases driven by query content:
      - APPLY   : "apply for leave" / "request time off" / "request leave" — creates a leave request.
      - STATUS  : "leave status" / "my leave" — shows the current user's own leave requests.
      - PENDING : "pending leave requests" — shows all pending requests (managers/admins only).
      - APPROVE/REJECT : "approve leave" / "reject leave" — approves or rejects a specific request.
    """

    query_lower = state["query"].lower()

    try:
        from app.utils.dependencies import get_backend_container, get_session_manager, get_authorization_service
        client = get_backend_container()["supabase_service"].get_admin_client()
        session_manager = get_session_manager()
        authz = get_authorization_service()
        profile = session_manager.get_current_profile()

        if not profile:
            state["leave_result"] = "⚠️ You must be logged in to use leave features."
            state["execution_log"].append("⚠️ Leave: no authenticated profile.")
            return state

        # ----------------------------------------------------------
        # SUB-CASE A — APPLY FOR LEAVE
        # ----------------------------------------------------------
        if any(phrase in query_lower for phrase in ["apply for leave", "request time off", "request leave"]):
            if not authz.can_apply_leave():
                state["leave_result"] = "❌ You do not have permission to apply for leave."
                state["execution_log"].append("❌ Leave apply: permission denied.")
                return state

            # Use LLM to extract leave details
            from app.models.models import LeaveExtraction
            structured_llm = get_llm().with_structured_output(LeaveExtraction)

            extraction_prompt = render_prompt(
                "leave_extraction.j2",
                query=state["query"],
            )
            extraction = structured_llm.invoke(extraction_prompt)

            if not extraction.start_date or not extraction.end_date:
                state["leave_result"] = (
                    "⚠️ I couldn't determine the leave dates from your request. "
                    "Please specify start and end dates clearly, e.g.: "
                    "*'Apply for sick leave from 2025-03-10 to 2025-03-12 for medical appointment'*."
                )
                state["execution_log"].append("⚠️ Leave apply: missing dates in extraction.")
                return state

            # Insert into leave_requests
            leave_payload = {
                "employee_id": str(profile.id),
                "leave_type": extraction.leave_type,
                "start_date": extraction.start_date,
                "end_date": extraction.end_date,
                "reason": extraction.reason or "Not specified",
                "status": "PENDING",
            }
            client.table("leave_requests").insert(leave_payload).execute()

            state["leave_result"] = (
                f"## ✅ Leave Request Submitted\n\n"
                f"- **Type:** {extraction.leave_type}\n"
                f"- **From:** {extraction.start_date}\n"
                f"- **To:** {extraction.end_date}\n"
                f"- **Reason:** {extraction.reason or 'Not specified'}\n"
                f"- **Status:** ⏳ PENDING\n\n"
                f"Your manager will review this request."
            )
            state["execution_log"].append(f"✅ Leave request submitted: {extraction.leave_type} ({extraction.start_date} to {extraction.end_date}).")

        # ----------------------------------------------------------
        # SUB-CASE D — APPROVE / REJECT LEAVE (checked before STATUS
        #              to prevent "approve leave" matching STATUS)
        # ----------------------------------------------------------
        elif any(phrase in query_lower for phrase in ["approve leave", "reject leave"]):
            if not authz.can_approve_leave():
                state["leave_result"] = "❌ You do not have permission to approve or reject leave requests. Only HR Managers and Admins can do this."
                state["execution_log"].append("❌ Leave approve/reject: permission denied.")
                return state

            action = "APPROVED" if "approve" in query_lower else "REJECTED"
            action_verb = "approved" if action == "APPROVED" else "rejected"

            # Extract employee name using the same pattern as onboarding_specialist
            import re
            cleaned = re.sub(
                r"(approve leave|reject leave|approve|reject|for|request|of|the)",
                "",
                state["query"],
                flags=re.IGNORECASE,
            ).strip()
            employee_name = cleaned[:60] if cleaned else ""

            if not employee_name:
                state["leave_result"] = (
                    "⚠️ I couldn't determine which employee's leave to process. "
                    "Please try: *'Approve leave for John Doe'*."
                )
                state["execution_log"].append("⚠️ Leave approve/reject: no employee name found.")
                return state

            # Fuzzy-match employee name in profiles (same ilike pattern as onboarding's find_candidate)
            emp_res = (
                client.table("profiles")
                .select("id, name")
                .ilike("name", f"%{employee_name}%")
                .limit(1)
                .execute()
            )

            if not emp_res.data:
                state["leave_result"] = f"❌ No employee found matching **'{employee_name}'**. Please check the name and try again."
                state["execution_log"].append(f"❌ Leave approve/reject: employee '{employee_name}' not found.")
                return state

            emp = emp_res.data[0]

            # Find most recent PENDING leave request for this employee
            lr_res = (
                client.table("leave_requests")
                .select("id, leave_type, start_date, end_date")
                .eq("employee_id", emp["id"])
                .eq("status", "PENDING")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not lr_res.data:
                state["leave_result"] = f"⚠️ No pending leave requests found for **{emp['name']}**."
                state["execution_log"].append(f"⚠️ Leave approve/reject: no pending requests for {emp['name']}.")
                return state

            lr = lr_res.data[0]
            client.table("leave_requests").update({
                "status": action,
                "reviewed_by": str(profile.id),
                "reviewed_at": "now()",
            }).eq("id", lr["id"]).execute()

            emoji = "✅" if action == "APPROVED" else "❌"
            state["leave_result"] = (
                f"## {emoji} Leave Request {action}\n\n"
                f"- **Employee:** {emp['name']}\n"
                f"- **Type:** {lr['leave_type']}\n"
                f"- **Period:** {lr['start_date']} to {lr['end_date']}\n"
                f"- **Decision:** {action}\n"
                f"- **Reviewed by:** {profile.name}"
            )
            state["execution_log"].append(f"{emoji} Leave {action_verb} for {emp['name']}.")

        # ----------------------------------------------------------
        # SUB-CASE C — LIST PENDING LEAVE REQUESTS (managers/admins)
        # ----------------------------------------------------------
        elif "pending leave" in query_lower or ("pending" in query_lower and "leave" in query_lower):
            if not authz.can_approve_leave():
                state["leave_result"] = "❌ You do not have permission to view pending leave requests. Only HR Managers and Admins can do this."
                state["execution_log"].append("❌ Leave pending list: permission denied.")
                return state

            pending_res = (
                client.table("leave_requests")
                .select("id, employee_id, leave_type, start_date, end_date, reason, created_at")
                .eq("status", "PENDING")
                .order("created_at", desc=False)
                .execute()
            )

            if not pending_res.data:
                state["leave_result"] = "✅ No pending leave requests at this time."
                state["execution_log"].append("📋 Leave pending list: none found.")
                return state

            # Join with profiles to get employee names
            emp_ids = list(set(r["employee_id"] for r in pending_res.data))
            profiles_res = (
                client.table("profiles")
                .select("id, name")
                .in_("id", emp_ids)
                .execute()
            )
            name_map = {p["id"]: p["name"] for p in profiles_res.data} if profiles_res.data else {}

            md = "## 📋 Pending Leave Requests\n\n"
            md += "| # | Employee | Type | From | To | Reason |\n"
            md += "|---|----------|------|------|----|--------|\n"
            for i, lr in enumerate(pending_res.data, 1):
                emp_name = name_map.get(lr["employee_id"], "Unknown")
                reason = lr.get("reason", "N/A") or "N/A"
                md += f"| {i} | {emp_name} | {lr['leave_type']} | {lr['start_date']} | {lr['end_date']} | {reason} |\n"

            state["leave_result"] = md
            state["execution_log"].append(f"📋 Displayed {len(pending_res.data)} pending leave request(s).")

        # ----------------------------------------------------------
        # SUB-CASE B — MY LEAVE STATUS (own requests only)
        # ----------------------------------------------------------
        else:
            my_res = (
                client.table("leave_requests")
                .select("leave_type, start_date, end_date, status, reason, created_at")
                .eq("employee_id", str(profile.id))
                .order("created_at", desc=True)
                .execute()
            )

            if not my_res.data:
                state["leave_result"] = "ℹ️ You have no leave requests on record."
                state["execution_log"].append("📋 Leave status: no requests found for current user.")
                return state

            md = "## 📋 My Leave Requests\n\n"
            md += "| # | Type | From | To | Status | Reason |\n"
            md += "|---|------|------|----|--------|--------|\n"
            status_icons = {"PENDING": "⏳", "APPROVED": "✅", "REJECTED": "❌"}
            for i, lr in enumerate(my_res.data, 1):
                icon = status_icons.get(lr["status"], "")
                reason = lr.get("reason", "N/A") or "N/A"
                md += f"| {i} | {lr['leave_type']} | {lr['start_date']} | {lr['end_date']} | {icon} {lr['status']} | {reason} |\n"

            state["leave_result"] = md
            state["execution_log"].append(f"📋 Displayed {len(my_res.data)} leave request(s) for current user.")

    except Exception as e:
        state["leave_result"] = (
            f"⚠️ Leave action could not be completed.\n\nError: {str(e)}"
        )
        state["execution_log"].append(f"❌ Leave Specialist failed: {e}")

    return state


# ==========================================
# Final Response
# ==========================================

def final_response(state: AgentState):

    if state["intent"] == "policy":
        state["final_answer"] = state["policy"]

        # --- RAG citation / confidence section (additive) ---
        if state.get("knowledge_gap"):
            state["final_answer"] += "\n\n⚠️ **Knowledge Gap** — the knowledge base may not have enough relevant content to answer this confidently."
        elif state.get("confidence_badge"):
            state["final_answer"] += f"\n\n{state['confidence_badge']}"

        if state.get("source_files"):
            state["final_answer"] += "\n\n📄 **Sources:** " + ", ".join(state["source_files"])
        # --- end RAG citation / confidence section ---

    elif state["intent"] == "email":
        state["final_answer"] = state["email"]

    elif state["intent"] == "resume" or state["intent"] == "recruitment":
        eval_data = state.get("evaluation_data", {})
        
        if eval_data:
            role = state.get('current_role', 'Candidate')
            pct = eval_data.get('match_percentage', 0)
            rec = eval_data.get('recommendation', 'N/A')
            analysis = eval_data.get('analysis', '')
            questions = eval_data.get('suggested_questions') or []

            report = f"## Resume Evaluation: {role}\n\n"
            report += f"**Match:** {pct}% | **Decision:** {rec}\n\n"
            report += f"{analysis}\n"

            if questions:
                report += "\n**Suggested Interview Questions:**\n"
                report += "\n".join(f"- {q}" for q in questions[:5]) + "\n"

            if state["intent"] == "recruitment" and state.get("email"):
                report += f"\n---\n\n## Interview Invitation Email\n\n{state['email']}"

            state["final_answer"] = report

            # --- RAG citation / confidence section (additive) ---
            if state.get("knowledge_gap"):
                state["final_answer"] += "\n\n⚠️ **Knowledge Gap** — the knowledge base may not have enough relevant content to answer this confidently."
            elif state.get("confidence_badge"):
                state["final_answer"] += f"\n\n{state['confidence_badge']}"

            if state.get("source_files"):
                state["final_answer"] += "\n\n📄 **Sources:** " + ", ".join(state["source_files"])
            # --- end RAG citation / confidence section ---

            # Save to Supabase
            try:
                from app.utils.dependencies import get_backend_container, get_session_manager
                container = get_backend_container()
                supabase_service = container["supabase_service"]

                # BUG FIX: resolve candidate_name from LLM output instead of hardcoding
                candidate_name = eval_data.get("candidate_name") or "Unknown Candidate"

                # BUG FIX: use profile.auth_user_id (FK to auth.users(id)), not profile.id
                # (profile.id is the public.profiles PK — a different UUID)
                auth_user_id = None
                try:
                    session_manager = get_session_manager()
                    profile = session_manager.get_current_profile()
                    if profile:
                        auth_user_id = profile.auth_user_id
                except Exception:
                    pass  # created_by remains None; insert still proceeds without it

                db_payload = {
                    "candidate_name": candidate_name,
                    # BUG FIX: omit fake placeholder email; leave null unless the model
                    # extracts a real one (CandidateEvaluation has no candidate_email field)
                    "applied_role": role,
                    "ats_score": pct,
                    "overall_score": pct,
                    "recommendation": rec,
                    "strengths": [],
                    "weaknesses": [],
                    "missing_skills": [],
                    "interview_questions": questions,
                    "evaluation_json": eval_data,
                }

                # Only include created_by if we have a valid auth UID
                if auth_user_id:
                    db_payload["created_by"] = auth_user_id

                supabase_service.insert_evaluation(db_payload)
            except Exception as e:
                import logging
                logging.error(f"Failed to insert evaluation: {e}")
                
        else:
            state["final_answer"] = f"# Evaluation Failed\n\n{state.get('analysis', 'Unknown error occurred.')}"

    elif state["intent"] == "general":
        # Pass through the answer generated by general_assistant
        pass

    elif state["intent"] == "onboarding":
        state["final_answer"] = state.get("onboarding_result", "Onboarding action completed.")

    elif state["intent"] == "leave":
        state["final_answer"] = state.get("leave_result", "Leave request processed.")

    else:
        state["final_answer"] = "Task Completed."
        state["execution_log"].append("✅ Workflow completed.")

    return state


def supervisor_decision(state: AgentState):
    """
    Supervisor reviews the candidate evaluation and
    decides the next step.
    """

    if state["match_percentage"] >= 80:
        state["next_node"] = "interview_email"

        state["execution_log"].append(
            "🧠 Supervisor approved candidate for interview."
        )

    else:
        state["next_node"] = "final"

        state["execution_log"].append(
            "🧠 Supervisor rejected candidate."
        )

    return state