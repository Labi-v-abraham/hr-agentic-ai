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

    prompt = f"""
You are a Senior HR Recruitment Specialist and Technical Interviewer.

Your task is to evaluate the uploaded resume for the role of: {state.get('current_role', 'General Candidate')}

Resume:
{state["resume_text"]}

Job Description / Request:
{state["query"]}

Instructions:
1. Perform a deep analysis of the candidate's technical skills, soft skills, and experience.
2. Calculate an estimated ATS Score and an overall match percentage.
3. Identify key strengths, weaknesses, and any missing skills.
4. Highlight relevant certifications or projects.
5. Provide specific Technical and HR interview questions.
6. Make a clear hiring recommendation (e.g., Selected, Rejected, Keep on file).
7. Return a detailed JSON evaluation.
"""

    try:
        # Also query the role-specific knowledge base to get evaluation rubrics if available
        retriever = get_retriever(active_kbs=state.get("active_kbs", ["General HR"]))
        # Just to add context, although structured output is main goal.
        # Actually, let's just do the evaluation since the prompt is already huge.
        
        result = structured_llm.invoke(prompt)

        state["match_percentage"] = result.match_percentage
        state["recommendation"] = result.recommendation
        state["analysis"] = result.analysis
        
        # Save evaluation data to state so final_response can format it and save to DB
        state["evaluation_data"] = result.dict()

        state["execution_log"].append(f"👨‍💼 Evaluated candidate for {state.get('current_role')}.")

    except Exception as e:
        state["match_percentage"] = 0
        state["recommendation"] = "Unable to Evaluate"
        state["analysis"] = str(e)
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

    except Exception as e:
        state["email"] = f"Unable to generate interview email.\n\nError: {str(e)}"
        state["execution_log"].append(
    "📧 HR Communication Specialist generated interview invitation."
)

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
        # Retrieve relevant handbook sections using active KBs
        active_kbs = state.get("active_kbs", ["General HR"])
        retriever = get_retriever(active_kbs=active_kbs)
        documents = retriever.invoke(state["query"])

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

        response = get_llm().invoke(prompt)

        state["policy"] = response.content

    except Exception as e:

        state["policy"] = (
            "Unable to retrieve HR policy information.\n\n"
            f"Error: {str(e)}"
        )
        state["execution_log"].append(
    "📚 HR Policy Specialist answered handbook question."
)

    return state
# ==========================================
# General HR Assistant
# ==========================================

def general_assistant(state: AgentState):

    response = get_llm().invoke(state["query"])

    state["final_answer"] = response.content

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
            # Format the output beautifully
            report = f"# Resume Evaluation: {state.get('current_role', 'Candidate')}\n\n"
            report += f"**ATS Score:** {eval_data.get('ats_score', 0)}/100 | **Overall Match:** {eval_data.get('match_percentage', 0)}%\n\n"
            report += f"## Recommendation: {eval_data.get('recommendation', 'N/A')}\n\n"
            report += f"### Summary\n{eval_data.get('candidate_summary', '')}\n\n"
            
            report += "### 💡 Skills & Match\n"
            report += f"**Skills Match Analysis:** {eval_data.get('skills_match', '')}\n\n"
            report += f"- **Technical Skills:** {', '.join(eval_data.get('technical_skills', []))}\n"
            report += f"- **Soft Skills:** {', '.join(eval_data.get('soft_skills', []))}\n"
            report += f"- **Missing Skills:** {', '.join(eval_data.get('missing_skills', []))}\n\n"
            
            report += "### 📊 Detailed Analysis\n"
            report += f"- **Education:** {eval_data.get('education_analysis', '')}\n"
            report += f"- **Experience:** {eval_data.get('experience_analysis', '')}\n"
            report += f"- **Projects:** {eval_data.get('project_analysis', '')}\n\n"
            
            report += "### ✅ Strengths & ⚠️ Weaknesses\n"
            report += f"**Strengths:** {', '.join(eval_data.get('strengths', []))}\n"
            report += f"**Weaknesses / Risks:** {', '.join(eval_data.get('weaknesses', []) + eval_data.get('risk_factors', []))}\n\n"
            
            report += "### 💬 Interview Questions\n"
            report += "**Technical:**\n" + "\n".join([f"- {q}" for q in eval_data.get('technical_interview_questions', [])]) + "\n\n"
            report += "**HR:**\n" + "\n".join([f"- {q}" for q in eval_data.get('hr_interview_questions', [])]) + "\n\n"
            
            if state["intent"] == "recruitment" and state.get("email"):
                report += f"---\n\n## Interview Invitation Email\n\n{state['email']}"
                
            state["final_answer"] = report
            
            # Save to Supabase
            try:
                from app.utils.dependencies import get_backend_container
                container = get_backend_container()
                supabase_service = container["supabase_service"]
                
                db_payload = {
                    "candidate_name": "Unknown (Parsed from Resume)", # Or parse it via LLM
                    "email": "unknown@example.com",
                    "applied_role": state.get("current_role", "Unknown"),
                    "ats_score": eval_data.get("ats_score", 0),
                    "overall_score": eval_data.get("match_percentage", 0),
                    "recommendation": eval_data.get("recommendation", ""),
                    "strengths": eval_data.get("strengths", []),
                    "weaknesses": eval_data.get("weaknesses", []),
                    "missing_skills": eval_data.get("missing_skills", []),
                    "interview_questions": eval_data.get("technical_interview_questions", []) + eval_data.get("hr_interview_questions", []),
                    "evaluation_json": eval_data
                }
                supabase_service.insert_evaluation(db_payload)
            except Exception as e:
                import logging
                logging.error(f"Failed to save evaluation to DB: {e}")
                
        else:
            state["final_answer"] = f"# Evaluation Failed\n\n{state.get('analysis', 'Unknown error occurred.')}"

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