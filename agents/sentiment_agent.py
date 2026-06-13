from typing import Dict, List
from .state import HiveLogicState

POSITIVE_WORDS = {
    "growth",
    "profit",
    "profits",
    "record",
    "strong",
    "surge",
    "beat",
    "beats",
    "expansion",
    "upgrade",
    "bullish",
    "gain",
    "gains",
    "improved",
    "improvement",
    "recovery",
    "positive",
}

NEGATIVE_WORDS = {
    "loss",
    "losses",
    "decline",
    "declines",
    "weak",
    "miss",
    "missed",
    "downgrade",
    "layoff",
    "layoffs",
    "drop",
    "falls",
    "fall",
    "risk",
    "risks",
    "investigation",
    "lawsuit",
    "negative",
    "cut",
}

def analyze_sentiment(
    ticker: str,
    articles: List[Dict],
):
    if not articles:
        return 0.0, "Neutral"

    text = " ".join(
        (
            article.get("title", "")
            + " "
            + article.get("content", "")
        ).lower()
        for article in articles
    )

    positive = sum(text.count(word) for word in POSITIVE_WORDS)
    negative = sum(text.count(word) for word in NEGATIVE_WORDS)
    total = positive + negative

    if total == 0:
        return 0.0, "Neutral"
    score = (positive - negative) / total
    score = max(-1.0, min(1.0, score))

    if score > 0.20:
        label = "Bullish"
    elif score < -0.20:
        label = "Bearish"
    else:
        label = "Neutral"
    return round(score, 2), label

def sentiment_agent_node(state: HiveLogicState) -> HiveLogicState:
    ticker = state["company_ticker"]
    print(f"[Sentiment Agent] Analyzing sentiment for {ticker}")
    score, label = analyze_sentiment(
        ticker,
        state.get("news_articles", []),
    )
    return {
        **state,
        "sentiment_score": score,
        "sentiment_label": label,
    }