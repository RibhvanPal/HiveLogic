import os
import re
import requests
from typing import List, Dict

from .state import HiveLogicState

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_URL = "https://newsapi.org/v2/everything"
INDIAN_SUFFIXES = (".NS", ".BO", ".NSE", ".BSE")

def is_indian_stock(ticker: str) -> bool:
    return ticker.upper().endswith(INDIAN_SUFFIXES)

def fetch_news_newsapi(query: str, page_size: int = 5) -> List[Dict]:
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "language": "en",
        "apiKey": NEWS_API_KEY,
    }
    try:
        resp = requests.get(NEWS_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return [
            {
                "title": article.get("title", ""),
                "content": article.get("description", "")
                or article.get("content", "")
                or "",
                "url": article.get("url", ""),
                "published": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", "NewsAPI"),
            }
            for article in data.get("articles", [])
            if article.get("title")
        ]

    except Exception as e:
        print(f"[News Agent] NewsAPI error: {e}")
        return []

def fetch_news_fallback(ticker: str) -> List[Dict]:
    try:
        url = (
            f"https://feeds.finance.yahoo.com/rss/2.0/headline"
            f"?s={ticker}&region=US&lang=en-US"
        )

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        titles = re.findall(
            r"<title><!\[CDATA\[(.*?)\]\]></title>",
            resp.text,
        )
        links = re.findall(
            r"<link>(https://finance\.yahoo.*?)</link>",
            resp.text,
        )

        articles = []

        for i, title in enumerate(titles[1:6]):
            articles.append(
                {
                    "title": title.strip(),
                    "content": title.strip(),
                    "url": links[i] if i < len(links) else "",
                    "published": "",
                    "source": "Yahoo Finance",
                }
            )
        return articles
    except Exception as e:
        print(f"[News Agent] Yahoo RSS error: {e}")
        return []

def filter_articles(
    articles: List[Dict],
    ticker: str,
    company_name: str,
) -> List[Dict]:

    ticker = ticker.lower()
    company_words = [
        word.lower()
        for word in company_name.split()
        if len(word) > 2
    ]

    filtered = []

    for article in articles:
        text = (
            article.get("title", "")
            + " "
            + article.get("content", "")
        ).lower()
        ticker_match = ticker in text
        company_match = any(word in text for word in company_words)
        if ticker_match or company_match:
            filtered.append(article)
    return filtered


def fetch_news_indian(
    ticker: str,
    company_name: str,
) -> List[Dict]:

    yahoo_articles = fetch_news_fallback(ticker)

    if yahoo_articles:
        print(
            f"[News Agent] Yahoo RSS returned "
            f"{len(yahoo_articles)} articles"
        )
        return yahoo_articles

    if NEWS_API_KEY:
        base_ticker = ticker.split(".")[0]

        articles = fetch_news_newsapi(
            f'"{base_ticker}" India NSE BSE',
            page_size=8,
        )
        articles = filter_articles(
            articles,
            base_ticker,
            company_name,
        )
        if articles:
            return articles
    return []

def news_agent_node(state: HiveLogicState) -> HiveLogicState:
    ticker = state["company_ticker"]
    metrics = state.get("financial_metrics", {})
    company_name = metrics.get("company_name", ticker)
    base_ticker = ticker.split(".")[0]

    print(
        f"[News Agent] Fetching news for "
        f"{ticker} ({company_name})"
    )
    errors = state.get("errors", [])
    articles = []

    try:
        if is_indian_stock(ticker):
            articles = fetch_news_indian(
                ticker,
                company_name,
            )
        elif NEWS_API_KEY:
            articles = fetch_news_newsapi(
                f'"{company_name}" OR "{ticker}"',
                page_size=8,
            )
            articles = filter_articles(
                articles,
                base_ticker,
                company_name,
            )
            if not articles:
                articles = fetch_news_fallback(ticker)
        else:
            articles = fetch_news_fallback(ticker)

    except Exception as e:
        errors = errors + [f"[News Agent] {str(e)}"]
        articles = fetch_news_fallback(ticker)

    print(
        f"[News Agent] Final article count: "
        f"{len(articles)}"
    )

    return {
        **state,
        "news_articles": articles,
        "errors": errors,
    }