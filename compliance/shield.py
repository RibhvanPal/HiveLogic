import re

# Patterns signalling direct trading advice requests
TRADING_ADVICE_PATTERNS = [
    r"\bshould i (buy|sell|hold|invest|short)\b",
    r"\b(buy|sell|short)\s+(this|the|some|more)?\s*(stock|share|equity|position)\b",
    r"\bwill (it|this|the stock|the price) (go up|go down|rise|fall|crash|moon)\b",
    r"\bprice target\b",
    r"\bgood (time|moment) to (buy|sell|invest)\b",
    r"\bwhat('s| is) my (return|profit|gain|loss)\b",
    r"\bshould i (exit|enter|take profit|cut loss)\b",
    r"\b(recommend|advice|advise) (me )?(to )?(buy|sell|hold|invest)\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in TRADING_ADVICE_PATTERNS]

COMPLIANCE_BLOCK_MESSAGE = (
    "**Compliance Notice**: HiveLogic cannot provide direct trading advice, "
    "buy/sell recommendations, or price targets. This would require SEBI/FINRA registration.\n\n"
    "However, I can provide you with a **comprehensive research report** on this company including "
    "financial metrics, risk analysis, news sentiment, and verified data from official filings. "
    "This information can support your own independent investment decisions.\n\n"
    "*This is not financial advice. Please consult a registered financial advisor.*"
)

def check_compliance(query: str) -> tuple[bool, str]:
    for pattern in COMPILED_PATTERNS:
        if pattern.search(query):
            return False, COMPLIANCE_BLOCK_MESSAGE
    return True, ""