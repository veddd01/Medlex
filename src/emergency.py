"""Emergency phrase detection — hardcoded rules that the LLM can never override.

Flags phrases like chest pain, overdose, suicidal thoughts, difficulty breathing.
Returns an emergency message + hotline numbers instead of normal generation.
"""
import re
from typing import Optional

EMERGENCY_PATTERNS = [
    r"\bchest\s+pain\b",
    r"\boverdose\b",
    r"\bsuicid(e|al)\b",
    r"\bkill\s+(my|him|her|them)self\b",
    r"\bwant\s+to\s+die\b",
    r"\bdifficulty\s+breathing\b",
    r"\b(can'?t|cannot)\s+breathe\b",
    r"\bheart\s+attack\b",
    r"\bstroke\s+symptoms?\b",
    r"\bsevere\s+bleeding\b",
    r"\bunconscious\b",
    r"\bseizure\b",
    r"\banaphyla(xis|ctic)\b",
    r"\bpoisoning\b",
    r"\bself[- ]?harm\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]

EMERGENCY_MESSAGE = (
    "⚠️ **This sounds like it could be a medical emergency.**\n\n"
    "Please contact emergency services immediately:\n"
    "• **Emergency (US):** 911\n"
    "• **Poison Control (US):** 1-800-222-1222\n"
    "• **Suicide & Crisis Lifeline:** 988\n"
    "• **Crisis Text Line:** Text HOME to 741741\n\n"
    "This chatbot is not a substitute for emergency medical care. "
    "If you or someone else is in immediate danger, call emergency services now."
)

def check_emergency(text: str) -> Optional[str]:
    """Return EMERGENCY_MESSAGE if text matches any pattern, else None."""
    for pattern in _COMPILED:
        if pattern.search(text):
            return EMERGENCY_MESSAGE
    return None
