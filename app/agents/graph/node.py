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
    provided Job Description.
    """

    structured_llm = get_llm().with_structured_output(CandidateEvaluation)

    prompt = f"""
You are a Senior HR Recruitment Specialist.

Your task is to evaluate the uploaded resume against the Job Description.

Resume:

{state["resume_text"]}


Job Description:

{state["query"]}


Instructions:

1. Analyze the candidate's technical skills.
2. Compare them with the Job Description.
3. Evaluate projects, education and experience.
4. Calculate an approximate match percentage.
5. Decide whether the candidate should be shortlisted.
"""

    try:
        result = structured_llm.invoke(prompt)

        state["match_percentage"] = result.match_percentage
        state["recommendation"] = result.recommendation
        state["analysis"] = result.analysis

    except Exception as e:

        state["match_percentage"] = 0
        state["recommendation"] = "Unable to Evaluate"
        state["analysis"] = str(e)
        state["execution_log"].append(
    "👨‍💼 Candidate Evaluator completed resume evaluation."
)

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
        # Retrieve relevant handbook sections
        retriever = get_retriever()
        documents = retriever.invoke(state["query"])

        context = "\n\n".join(
            doc.page_content for doc in documents
        )

        prompt = f"""
You are an HR Policy Specialist.

Answer ONLY using the provided Employee Handbook context.

If the answer is not present in the handbook, say:

"I couldn't find this information in the Employee Handbook."

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

    elif state["intent"] == "resume":

        state["final_answer"] = state["analysis"]

    elif state["intent"] == "recruitment":

        if state["match_percentage"] >= 80:

            state["final_answer"] = f"""
# Candidate Selected

## Evaluation

{state["analysis"]}

---

## Interview Invitation

{state["email"]}
"""

        else:

            state["final_answer"] = f"""
# Candidate Not Selected

{state["analysis"]}
"""

    else:

        state["final_answer"] = "Task Completed."
        state["execution_log"].append(
    "✅ Workflow completed."
)

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