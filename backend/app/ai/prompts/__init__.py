import json
from backend.app.ai.prompts.system import SYSTEM_INSTRUCTIONS

def build_investigation_prompt(exception_data: dict) -> str:
    return f"""
<UNTRUSTED FINANCIAL DATA>
{json.dumps(exception_data, indent=2)}
</UNTRUSTED FINANCIAL DATA>

Analyze the provided evidence and determine the most likely scenario.
Return ONLY a JSON object matching the required schema.
"""

__all__ = ["SYSTEM_INSTRUCTIONS", "build_investigation_prompt"]
