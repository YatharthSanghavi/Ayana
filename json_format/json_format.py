import json
import re

def extract_json(text: str) -> dict:
    """
    Robustly extract the first valid JSON object from a model response.
    Falls back to a safe default if nothing parses.
    """
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())

    # Find the outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                parsed.setdefault("markdown", "")
                parsed.setdefault("locations", [])
                parsed.setdefault("budget", {})
                return parsed
        except json.JSONDecodeError:
            pass

    # Final fallback
    return {"markdown": text.strip(), "locations": [], "budget": {}}
