# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, START, END

from app.agents.graph.state import AgentState
from app.agents.graph.router import detect_intent
from app.agents.graph.node import (
    candidate_evaluator,
    interview_email_generator,
    hr_policy_specialist,
    general_assistant,
    final_response,
    supervisor_decision,
    onboarding_specialist,
    leave_specialist,
)
# ==========================================
# Supervisor Agent
# ==========================================

def supervisor(state: AgentState):
    """
    Detects the user's intent and routes the request
    to the appropriate specialist.
    """

    state["intent"] = detect_intent(state["query"])

    state["execution_log"].append(
        f"🧠 Supervisor detected intent: {state['intent']}"
    )

    return state


# ==========================================
# Intent Router
# ==========================================

def route_intent(state: AgentState):

    intent = state["intent"]

    if intent in ["resume", "recruitment"]:
        return "candidate_evaluator"

    elif intent == "email":
        return "interview_email"

    elif intent == "policy":
        return "policy"

    elif intent == "onboarding":
        return "onboarding"

    elif intent == "leave":
        return "leave"

    else:
        return "general"


# ==========================================
# Supervisor Decision Router
# ==========================================

def decision_router(state: AgentState):
    """
    Routes based on the decision made
    by the Supervisor Decision Agent.
    """

    return state["next_node"]


# ==========================================
# Build Workflow
# ==========================================

import streamlit as st

@st.cache_resource
def get_graph():
    builder = StateGraph(AgentState)

    # Nodes
    builder.add_node("supervisor", supervisor)
    builder.add_node("candidate_evaluator", candidate_evaluator)
    builder.add_node("supervisor_decision", supervisor_decision)
    builder.add_node("interview_email", interview_email_generator)
    builder.add_node("policy", hr_policy_specialist)
    builder.add_node("general", general_assistant)
    builder.add_node("onboarding", onboarding_specialist)
    builder.add_node("leave", leave_specialist)
    builder.add_node("final", final_response)

    # Start
    builder.add_edge(START, "supervisor")

    # Supervisor → Specialist
    builder.add_conditional_edges(
        "supervisor",
        route_intent,
    )

    # Candidate Evaluation → Supervisor Decision
    builder.add_edge(
        "candidate_evaluator",
        "supervisor_decision",
    )

    # Supervisor Decision → Next Node
    builder.add_conditional_edges(
        "supervisor_decision",
        decision_router,
    )

    # Remaining Flow
    builder.add_edge("interview_email", "final")
    builder.add_edge("policy", "final")
    builder.add_edge("general", "final")
    builder.add_edge("onboarding", "final")
    builder.add_edge("leave", "final")
    builder.add_edge("final", END)

    return builder.compile()