import json

from app.agents.graph.state import AgentState
from app.utils.config import get_llm
from app.models.models import CandidateEvaluation
from app.agents.rag.retriever import get_retriever

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
            
        prompt = f"""You are a Senior HR Recruitment Specialist.

Evaluate the resume below against the role: {state.get('current_role', 'General Candidate')}

RESUME:
{state["resume_text"]}
{kb_context}

REQUEST:
{state["query"]}

OUTPUT RULES (strictly enforced):
1. match_percentage: integer 0-100.
2. recommendation: MUST be exactly one of "Selected", "Rejected", or "Hold". No other wording.
3. analysis: 2-4 sentences ONLY. Summarise key fit factors and major gaps. \
   Do NOT include interview questions, coaching tips, or candidate-facing text here.
4. suggested_questions: at most 5 short interview questions targeted at this candidate's \
   specific gaps. Leave empty if none are warranted.
5. final_answer: ONE sentence (max 25 words) suitable as a chat reply, \
   e.g. "The candidate is a moderate match for the {state.get('current_role', 'role')} role with {'{match_percentage}'}% alignment."
6. scorecard: Break down the evaluation into 3-6 specific criteria relevant to THIS role \
   (derive criteria from the role knowledge base content provided above, not a generic fixed list). \
   Each criterion needs a 0-100 score and a one-sentence justification grounded in the resume \
   and role requirements.
7. candidate_name: Extract the candidate's full name from the resume header or contact section. \
   If no name is clearly present, use "Unknown Candidate".
"""

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

    prompt = f"""
You are an HR Communication Specialist.

Generate a professional interview invitation email based on the candidate evaluation.

Candidate Evaluation:

{state["analysis"]}

Candidate Match Percentage:
{state["match_percentage"]}%

Recommendation:
{state["recommendation"]}

Instructions:

- Congratulate the candidate.
- Mention they have been shortlisted.
- Invite them for an interview.
- Keep the email professional and friendly.
- Include placeholders for:
    - Company Name
    - Interview Date
    - Interview Time
    - Interview Mode (Online/Offline)
    - HR Contact
- End with a professional closing.
"""

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
        kb_name = "General HR"
        from app.utils.dependencies import get_backend_container
        client = get_backend_container()["supabase_service"].get_admin_client()
        res_kb = client.table("knowledge_bases").select("id").eq("name", kb_name).execute()
        kb_id = res_kb.data[0]["id"] if res_kb.data else "unknown"

        print("============================")
        print("REQUEST")
        print("============================")
        print("\nIntent:")
        print("policy")
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
        
        # Using similarity search directly to get scores
        docs_and_scores = vs.similarity_search_with_score(state["query"], k=10, filter={"knowledge_base_id": {"$in": [kb_id]}})
        documents = [d for d, s in docs_and_scores]
        
        print("\nChunks Retrieved:")
        print(len(documents))
        
        if not documents:
            print("\nNo chunks retrieved.")
            state["policy"] = "No information found"
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

        prompt = f"""
You are an HR Policy Specialist.

Answer ONLY using the provided Employee Handbook context.

If the exact answer is not present but related information exists, summarize it instead.
Do NOT say "I couldn't find this information" unless no relevant information is provided in the context at all.

Employee Handbook Context:

{context}

Question:

{state["query"]}

Provide a clear and professional answer.
"""
        print("\nPrompt sent to LLM:")
        print(prompt)

        response = get_llm().invoke(prompt)
        
        print("\nLLM output:")
        print(response.content)

        state["policy"] = response.content
        state["execution_log"].append("📚 HR Policy Specialist answered handbook question.")

    except Exception as e:

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

    response = get_llm().invoke(state["query"])

    state["final_answer"] = response.content

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
            match = re.search(r"mark (.+?) (?:done|complete)(?:\s+for\s+(.+))?", state["query"], re.IGNORECASE)
            if match:
                task_keywords = match.group(1).strip()
                candidate_name_raw = match.group(2).strip() if match.group(2) else None
            else:
                task_keywords = None
                candidate_name_raw = None

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
# Final Response
# ==========================================

def final_response(state: AgentState):

    if state["intent"] == "policy":
        state["final_answer"] = state["policy"]

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