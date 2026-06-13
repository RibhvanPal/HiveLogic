import re
from typing import List, Dict
from .state import HiveLogicState

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def is_valid_filing_text(text: str) -> bool: # check if filing text is reliable enough for citations
    bad_signals = [
        "unknown period",
        "no recent 10-k",
        "no verified filing",
        "please upload a pdf",
        "filing data unavailable",
        "2010-",   # old filing dates
        "2011-",
        "2012-",
        "filed: 200",  # anything before 2010
    ]
    lower = text.lower()
    return not any(s in lower for s in bad_signals)

def build_citations_from_filing(filings_text: str) -> List[Dict]: # build citations from filing text, only if text is reliable.
    if not filings_text or not is_valid_filing_text(filings_text):
        return []

    sentences = re.split(r"(?<=[.!?])\s+", filings_text)
    citations = []

    for i, sentence in enumerate(sentences[:6]):
        sentence = clean_text(sentence)
        if len(sentence) < 40:
            continue
        # Skip generic filler sentences
        if any(w in sentence.lower() for w in [
            "full text available", "source: https", "management discussion"
        ]):
            continue
        citations.append({
            "claim": sentence[:120],
            "source": "Company Filing",
            "excerpt": sentence[:300],
            "chunk_id": f"filing_{i}",
            "url": "",
        })

    return citations

def build_citations_from_news(news_articles: List[Dict]) -> List[Dict]: # build citations from news articles
    citations = []
    for i, article in enumerate(news_articles[:5]):
        title = article.get("title", "")
        if not title or "Could not fetch" in title:
            continue
        citations.append({
            "claim": title[:120],
            "source": article.get("source", "News"),
            "excerpt": clean_text(article.get("content", title)[:300]),
            "chunk_id": f"news_{i}",
            "url": article.get("url", ""),
        })
    return citations


def build_citations_from_rag(ticker: str, filings_text: str) -> List[Dict]: # try FAISS RAG
    citations = []
    base_ticker = ticker.split(".")[0].upper()

    try:
        from rag.retriever import retrieve_chunks
        chunks = retrieve_chunks(
            f"{ticker} financial performance risks revenue profit", k=6
        )
        # Strict ticker scoping
        matching = [
            c for c in chunks
            if base_ticker.lower() in c.get("source", "").lower()
        ]
        for c in matching[:4]:
            text = clean_text(c["text"][:300])
            if len(text) < 30:
                continue
            citations.append({
                "claim": text[:120],
                "source": c.get("source", "Filing"),
                "excerpt": text,
                "chunk_id": c.get("chunk_id", ""),
                "url": "",
            })
    except Exception:
        pass

    return citations


def citation_agent_node(state: HiveLogicState) -> HiveLogicState:
    print("[Citation Agent] Building citations")

    ticker = state["company_ticker"]
    filings_text = state.get("filings_text", "")
    news_articles = state.get("news_articles", [])
    citations = []

    # Priority 1: verified claims
    for item in state.get("verified_claims", []):

        # skip weak matches
        if item.get("score", 999) > 1.5:
            continue

        source_type = item.get("source_type", "filing")

        if source_type == "sentiment":
            source_label = "Sentiment Analysis"
            excerpt = "Derived from sentiment analysis."

        elif source_type == "contagion":
            source_label = "Graph Contagion Model"
            excerpt = "Derived from GraphRAG contagion analysis."

        else:
            source_label = item.get(
                "source",
                "SEC Filing",
            )
            excerpt = clean_text(
                item.get("evidence", "")
            )

        if source_label == "unknown":
            continue
        if not excerpt:
            continue
        citations.append(
            {
                "claim": item.get(
                    "claim",
                    "",
                )[:120],
                "source": source_label,
                "excerpt": excerpt,
                "chunk_id": item.get(
                    "chunk_id",
                    "",
                ),
                "url": "",
            }
        )

    # Priority 2: RAG chunks (ticker-scoped)
    if not citations:
        citations = build_citations_from_rag(ticker, filings_text)

    # Priority 3: Filing text (only if reliable/recent)
    if not citations:
        citations = build_citations_from_filing(filings_text)

    # Priority 4: News articles
    if not citations:
        citations = build_citations_from_news(news_articles)

    # Explicit no-data message
    if not citations:
        citations = [{
            "claim": f"No verified sources available for {ticker}",
            "source": "System",
            "excerpt": (
                "No PDF filing was uploaded and no recent online data was found. "
                "Upload a company filing PDF for verified citations."
            ),
            "chunk_id": "no_data",
            "url": "",
        }]
    seen = set()
    unique = []

    for citation in citations:
        key = citation["claim"][:60].lower()
        if key in seen:
            continue

        seen.add(key)
        unique.append(citation)

    citations = unique
    print(f"[Citation Agent] Generated {len(citations)} citations.")
    return {**state, "citations": citations}