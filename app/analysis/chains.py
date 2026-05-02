import json
from langchain_core.output_parsers import JsonOutputParser
from app.analysis.llm_client import llm, llm_creative
from app.analysis.prompts import (
    PATTERN_EXTRACTION_PROMPT,
    ROOT_CAUSE_PROMPT,
    FIX_SUGGESTION_PROMPT,
)

pattern_chain = PATTERN_EXTRACTION_PROMPT | llm | JsonOutputParser()
rca_chain = ROOT_CAUSE_PROMPT | llm | JsonOutputParser()
fix_chain = FIX_SUGGESTION_PROMPT | llm_creative | JsonOutputParser()


async def extract_patterns(log_text: str) -> list:
    try:
        result = await pattern_chain.ainvoke({"log_text": log_text})
        return result.get("patterns", [])
    except Exception:
        return []


async def extract_root_causes(patterns: list) -> list:
    if not patterns:
        return []
    try:
        result = await rca_chain.ainvoke({"patterns_json": json.dumps(patterns, indent=2)})
        return result.get("root_causes", [])
    except Exception:
        return []


async def extract_fixes(root_causes: list) -> list:
    if not root_causes:
        return []
    try:
        result = await fix_chain.ainvoke({"root_causes_json": json.dumps(root_causes, indent=2)})
        return result.get("fixes", [])
    except Exception:
        return []
