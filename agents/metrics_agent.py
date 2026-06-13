from typing import Dict

from .state import HiveLogicState


def format_market_cap(value):
    if not value:
        return "N/A"
    try:
        value = float(value)
        if value >= 1e12:
            return f"${value / 1e12:.2f}T"
        elif value >= 1e9:
            return f"${value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"${value / 1e6:.2f}M"
        return f"${value:,.0f}"

    except Exception:
        return "N/A"

def fetch_metrics(ticker: str) -> Dict:
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker)

        try:
            info = stock.info or {}
        except Exception:
            info = {}

        try:
            fast_info = stock.fast_info
        except Exception:
            fast_info = {}

        metrics = {
            "company_name": info.get("longName")
            or info.get("shortName")
            or ticker,

            "employees": info.get("fullTimeEmployees"),

            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),

            "cash": info.get("totalCash"),

            "market_cap": (
                info.get("marketCap")
                or fast_info.get("market_cap")
            ),

            "current_price": (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or fast_info.get("lastPrice")
                or fast_info.get("last_price")
            ),

            "pe_ratio": (
                info.get("trailingPE")
                or info.get("forwardPE")
            ),

            "forward_pe": info.get("forwardPE"),

            "eps": info.get("trailingEps"),

            "revenue": info.get("totalRevenue"),

            "revenue_growth": info.get("revenueGrowth"),

            "profit_margin": info.get("profitMargins"),

            "debt_to_equity": info.get("debtToEquity"),

            "current_ratio": info.get("currentRatio"),

            "52w_high": (
                info.get("fiftyTwoWeekHigh")
                or fast_info.get("yearHigh")
                or fast_info.get("year_high")
            ),

            "52w_low": (
                info.get("fiftyTwoWeekLow")
                or fast_info.get("yearLow")
                or fast_info.get("year_low")
            ),

            "beta": info.get("beta"),

            "dividend_yield": info.get("dividendYield"),

            "analyst_rating": (
                info.get("recommendationKey")
                or "N/A"
            ),

            "target_price": info.get("targetMeanPrice"),
            "operating_margin": info.get("operatingMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "description": (
                info.get("longBusinessSummary", "")[:500]
            ),
        }

        metrics["market_cap_fmt"] = format_market_cap(
            metrics["market_cap"]
        )
        metrics["revenue_fmt"] = format_market_cap(
            metrics["revenue"]
        )
        metrics["cash_fmt"] = format_market_cap(
            metrics["cash"]
        )

        return metrics

    except Exception as e:
        return {
            "company_name": ticker,
            "error": str(e),
        }


def metrics_agent_node(state: HiveLogicState) -> HiveLogicState:
    ticker = state["company_ticker"]

    print(f"[Metrics Agent] Fetching metrics for {ticker}")

    metrics = fetch_metrics(ticker)

    errors = state.get("errors", [])

    if metrics.get("error"):
        errors.append(
            f"[Metrics Agent] {metrics['error']}"
        )

    return {
        **state,
        "financial_metrics": metrics,
        "errors": errors,
    }