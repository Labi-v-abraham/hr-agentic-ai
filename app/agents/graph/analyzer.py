from datetime import date
from app.utils.config import get_llm
from app.models.models import RequestAnalysis
from app.prompts.loader import render_prompt
import logging

logger = logging.getLogger(__name__)

def analyze_request(query: str, available_roles: list) -> dict | None:
    try:
        structured_llm = get_llm().with_structured_output(RequestAnalysis)
        prompt = render_prompt(
            "request_analysis.j2",
            query=query,
            today_date=date.today().isoformat(),
            available_roles=", ".join(available_roles),
        )
        result = structured_llm.invoke(prompt)
        return result.model_dump()
    except Exception as e:
        logger.warning(f"[RequestAnalysis] LLM analysis failed, falling back to keyword matching: {e}")
        return None
