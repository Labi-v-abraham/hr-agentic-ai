# HR Agentic AI - Project Overview

This document explains the workflow, architecture, code structure, and tools used in the **HR Agentic AI** project.

## 🛠 Tools & Technologies Used
- **[Streamlit](https://streamlit.io/)**: Used for the frontend to provide an interactive web application for the HR Assistant. Handles PDF uploads and chat interface.
- **[LangChain](https://langchain.com/) & [LangGraph](https://python.langchain.com/v0.1/docs/langgraph/)**: The core framework orchestrating the autonomous agents workflow. LangGraph is used to manage states and route tasks between different specialized agents.
- **[Google Gemini (Gemini 2.5 Flash)](https://deepmind.google/technologies/gemini/)**: The primary Large Language Model (LLM) powering the agents' intelligence (`ChatGoogleGenerativeAI`).
- **[ChromaDB](https://www.trychroma.com/)**: A vector database used to store and retrieve document embeddings (specifically for the Employee Handbook) to support Retrieval-Augmented Generation (RAG).
- **[HuggingFace Embeddings](https://huggingface.co/)**: Uses the `sentence-transformers/all-MiniLM-L6-v2` model to embed document chunks before storing them in ChromaDB.
- **PyPDFLoader**: Used to parse and extract text from uploaded PDF files (both the Employee Handbook and Candidate Resumes).
- **Pydantic**: Used for strict type definitions and structured output parsing (e.g., `CandidateEvaluation` model).

## 🔄 Project Workflow
The application operates as an AI-powered HR Assistant with capabilities ranging from candidate evaluation to answering HR policy queries. Here is the step-by-step workflow:

1. **Knowledge Base Initialization (RAG)**:
   - The user can upload an Employee Handbook (PDF) via the sidebar.
   - The document is parsed, chunked, and vectorized using HuggingFace embeddings.
   - The vectors are saved in a persistent ChromaDB vector store (`vectorstore/` directory) for subsequent querying.

2. **User Interaction & Resume Upload**:
   - The user can chat with the HR Agent via the main chat input.
   - If a recruitment-related query is made, the user is prompted to upload a candidate's resume (PDF).

3. **LangGraph State Management**:
   - The user's query and the resume text are packaged into a unified `AgentState` dictionary.
   - This state is passed into the LangGraph workflow.

4. **Agentic Routing (The Supervisor)**:
   - The `supervisor` node is the entry point. It evaluates the user's query to detect the **intent** (e.g., `resume`, `recruitment`, `email`, `policy`, `general`).
   - Based on the detected intent, the `route_intent` function routes the state to the appropriate specialist agent node.

5. **Specialist Agents Execution**:
   - **Candidate Evaluator (`candidate_evaluator`)**: Analyzes the candidate's resume against the user's query. Computes a match percentage and detailed analysis. Followed by `supervisor_decision` to decide if an interview email should be drafted.
   - **HR Policy Specialist (`hr_policy_specialist`)**: Queries the ChromaDB vector store to answer policy-related questions using RAG.
   - **Interview Email Generator (`interview_email`)**: Drafts an interview invitation for shortlisted candidates.
   - **General Assistant (`general`)**: Handles casual conversation or out-of-scope queries.

6. **Final Response Compilation**:
   - All paths converge at the `final_response` node, which formats the final answer.
   - The Streamlit UI displays the response, and if applicable, a Recruitment Dashboard showing the match percentage, recommendation (Selected/Rejected), and an execution log detailing the agent's thought process.

## 📂 Code Structure Explanation

- **`app.py`**: The main Streamlit application script. It handles the UI layout, file uploads, session state management, user input, and displaying the LangGraph agent's results (including the execution log and candidate dashboard).
- **`config.py`**: Handles configuration and environment variables. It loads the `GOOGLE_API_KEY` and initializes the Google Gemini LLM (`ChatGoogleGenerativeAI`).
- **`models.py`**: Contains Pydantic models (like `CandidateEvaluation`) that dictate the structured schema the LLM must return when evaluating candidates.
- **`graph/workflow.py`**: Defines the core LangGraph state machine. It contains the logic for nodes (supervisor, specialist agents) and conditional edges (routing based on intent and supervisor decisions).
- **`graph/router.py`**: Contains the logic to detect user intents.
- **`graph/node.py`**: Contains the individual agent node functions that call the LLMs.
- **`graph/state.py`**: Defines the `AgentState` schema used to pass data between nodes.
- **`rag/build_vectorstore.py`**: Contains the logic to process the uploaded Employee Handbook, generate HuggingFace embeddings, and persist them into ChromaDB.
- **`rag/loader.py`**: Utility to load documents for the vectorstore.
