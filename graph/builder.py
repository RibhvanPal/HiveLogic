import re
from typing import List, Tuple, Dict

Relationship = Tuple[str, str, str, float]  # (source, target, relation, weight)

# Sector peer map. Companies in same sector/industry are competitors
SECTOR_PEERS = {
    "Technology": {
        "Software - Infrastructure": ["MSFT", "ORCL", "IBM", "CSCO"],
        "Semiconductors": ["NVDA", "AMD", "INTC", "QCOM", "TSM"],
        "Consumer Electronics": ["AAPL", "SONY", "SAMS"],
        "Internet Content": ["GOOGL", "META", "SNAP", "TWTR"],
        "Software - Application": ["ADBE", "CRM", "NOW", "WDAY"],
    },
    "Communication Services": {
        "Internet Content": ["GOOGL", "META", "NFLX", "SNAP"],
    },
    "Consumer Discretionary": {
        "Internet Retail": ["AMZN", "BABA", "JD"],
        "Auto Manufacturers": ["TSLA", "F", "GM", "TM"],
    },
    "Energy": {
        "Oil & Gas": ["RELIANCE", "XOM", "CVX", "BP", "ONGC"],
    },
    "Information Technology": {
        "IT Services": ["TCS", "INFY", "WIPRO", "HCL", "TECHM"],
    },
}

#Known supply chain relationships
KNOWN_SUPPLY_CHAINS: List[Relationship] = [
    # Apple supply chain
    ("AAPL", "TSMC", "chip_supplier", 0.95),
    ("AAPL", "Foxconn", "manufacturer", 0.90),
    ("AAPL", "Samsung", "display_supplier", 0.70),
    ("AAPL", "GOOGL", "competitor", 0.65),
    ("AAPL", "QCOM", "chip_supplier", 0.60),
    ("AAPL", "Corning", "glass_supplier", 0.55),

    # Microsoft
    ("MSFT", "NVDA", "hardware_supplier", 0.80),
    ("MSFT", "OpenAI", "strategic_partner", 0.85),
    ("MSFT", "AMZN", "cloud_competitor", 0.70),
    ("MSFT", "GOOGL", "competitor", 0.65),
    ("MSFT", "LinkedIn", "subsidiary", 0.50),

    # NVIDIA
    ("NVDA", "TSMC", "chip_manufacturer", 0.98),
    ("NVDA", "Samsung", "chip_manufacturer", 0.60),
    ("NVDA", "MSFT", "major_customer", 0.75),
    ("NVDA", "AMZN", "major_customer", 0.70),
    ("NVDA", "GOOGL", "major_customer", 0.70),
    ("NVDA", "META", "major_customer", 0.65),

    # TSMC
    ("TSMC", "Taiwan_Geopolitics", "geopolitical_risk", 0.90),
    ("TSMC", "NVDA", "major_customer", 0.70),
    ("TSMC", "AAPL", "major_customer", 0.80),

    # Google
    ("GOOGL", "Ad_Market", "revenue_dependency", 0.90),
    ("GOOGL", "AAPL", "distribution_partner", 0.75),
    ("GOOGL", "META", "ad_competitor", 0.70),
    ("GOOGL", "MSFT", "competitor", 0.65),

    # Meta
    ("META", "Ad_Market", "revenue_dependency", 0.92),
    ("META", "GOOGL", "ad_competitor", 0.70),
    ("META", "NVDA", "hardware_supplier", 0.65),
    ("META", "China_Regulations", "regulatory_risk", 0.60),

    # Amazon
    ("AMZN", "AWS_Cloud", "revenue_pillar", 0.80),
    ("AMZN", "MSFT", "cloud_competitor", 0.70),
    ("AMZN", "GOOGL", "cloud_competitor", 0.65),
    ("AMZN", "Logistics_Costs", "cost_risk", 0.60),
    ("AMZN", "FedEx", "logistics_partner", 0.55),

    # Indian IT
    ("TCS", "IT_Spending_US", "revenue_dependency", 0.85),
    ("TCS", "INFY", "competitor", 0.50),
    ("TCS", "USD_INR", "currency_risk", 0.65),
    ("INFY", "IT_Spending_US", "revenue_dependency", 0.85),
    ("INFY", "TCS", "competitor", 0.50),
    ("INFY", "USD_INR", "currency_risk", 0.65),
    ("WIPRO", "IT_Spending_US", "revenue_dependency", 0.80),
    ("WIPRO", "TCS", "competitor", 0.45),

    # Reliance
    ("RELIANCE", "Oil_Prices", "commodity_risk", 0.75),
    ("RELIANCE", "INR_USD", "currency_risk", 0.55),
    ("RELIANCE", "ONGC", "competitor", 0.40),
    ("RELIANCE", "Jio_Telecom", "subsidiary", 0.60),

    # Macro risk nodes (shared across companies)
    ("China_Regulations", "Supply_Chain_Risk", "amplifier", 0.80),
    ("Taiwan_Geopolitics", "Supply_Chain_Risk", "amplifier", 0.85),
    ("Oil_Prices", "Global_Inflation", "amplifier", 0.70),
    ("Ad_Market", "Economic_Slowdown", "sensitivity", 0.75),
    ("IT_Spending_US", "US_Recession_Risk", "sensitivity", 0.70),
]

# NER patterns for extracting relationships from news
SUPPLY_CHAIN_PATTERNS = [
    (r"(?:supplier|supplies|supply)\s+(?:to\s+)?([A-Z]{2,6})", "supplier", 0.6),
    (r"(?:partner(?:ship)?|partnership\s+with)\s+([A-Z]{2,6})", "partner", 0.5),
    (r"(?:compet(?:es?|itor)\s+(?:with\s+)?)?([A-Z]{2,6})", "competitor", 0.4),
    (r"(?:acqui(?:res?|sition\s+of))\s+([A-Z]{2,6})", "acquisition", 0.7),
    (r"(?:customer|client)\s+([A-Z]{2,6})", "customer", 0.55),
]


def extract_relationships_from_text(
    ticker: str,
    text: str,
    known_tickers: set = None,
) -> List[Relationship]:
    #Simple NER: extract company relationships from news/filing text. Returns list of (source, target, relation, weight).
    relationships = []
    ticker_upper = ticker.upper()
    text_upper = text.upper()

    if known_tickers is None:
        # common tickers to look for
        known_tickers = {
            "AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA",
            "AMD", "INTC", "QCOM", "TSMC", "TCS", "INFY", "WIPRO",
            "RELIANCE", "HDFCBANK", "ICICIBANK", "ADANIENT",
        }

    for pattern, rel_type, weight in SUPPLY_CHAIN_PATTERNS:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            match = match.strip()
            if (
                match != ticker_upper
                and match in known_tickers
                and len(match) >= 2
            ):
                relationships.append(
                    (ticker_upper, match, rel_type, weight)
                )

    return relationships


def get_relationships_from_yfinance(ticker: str) -> List[Relationship]:
    #Build relationships from yfinance company info
    relationships = []
    base_ticker = ticker.split(".")[0].upper()

    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        sector = info.get("sector", "")
        industry = info.get("industry", "")

        # Add sector/industry peers as competitors
        if sector in SECTOR_PEERS:
            industry_peers = SECTOR_PEERS[sector].get(industry, [])
            for peer in industry_peers:
                if peer != base_ticker:
                    relationships.append(
                        (base_ticker, peer, "competitor", 0.45)
                    )

        # Add macro risk relationships based on sector
        sector_risks = {
            "Technology": [
                ("Taiwan_Geopolitics", "supply_chain_risk", 0.55),
                ("China_Regulations", "regulatory_risk", 0.50),
            ],
            "Energy": [
                ("Oil_Prices", "commodity_risk", 0.75),
                ("Global_Inflation", "macro_risk", 0.60),
            ],
            "Information Technology": [
                ("IT_Spending_US", "revenue_dependency", 0.70),
                ("USD_INR", "currency_risk", 0.60),
            ],
            "Communication Services": [
                ("Ad_Market", "revenue_dependency", 0.65),
                ("Regulatory_Scrutiny", "regulatory_risk", 0.55),
            ],
            "Consumer Discretionary": [
                ("Consumer_Spending", "revenue_dependency", 0.70),
                ("Logistics_Costs", "cost_risk", 0.50),
            ],
            "Financial Services": [
                ("Interest_Rates", "macro_risk", 0.75),
                ("Credit_Risk", "regulatory_risk", 0.65),
            ],
            "Healthcare": [
                ("FDA_Regulations", "regulatory_risk", 0.70),
                ("Drug_Pricing", "revenue_dependency", 0.60),
            ],
            "Industrials": [
                ("Global_Inflation", "cost_risk", 0.60),
                ("Supply_Chain_Risk", "supply_chain_risk", 0.65),
            ],
            "Consumer Staples": [
                ("Consumer_Spending", "revenue_dependency", 0.60),
                ("Commodity_Prices", "commodity_risk", 0.65),
            ],
        }

        if sector in sector_risks:
            for risk_node, rel_type, weight in sector_risks[sector]:
                relationships.append(
                    (base_ticker, risk_node, rel_type, weight)
                )

        print(
            f"[Graph Builder] yfinance: {len(relationships)} "
            f"relationships for {ticker} ({sector}/{industry})"
        )

    except Exception as e:
        print(f"[Graph Builder] yfinance relationships failed: {e}")

    return relationships


def build_dynamic_graph(ticker: str, news_text: str = "") -> List[Relationship]:
    #Build a complete relationship list for a ticker by combining: 1. Known hardcoded supply chains 2. yfinance sector/industry peers 3. NER extraction from news text
    all_relationships = []
    base_ticker = ticker.split(".")[0].upper()

    # 1. Known supply chains
    known = [
        r for r in KNOWN_SUPPLY_CHAINS
        if r[0] == base_ticker or r[1] == base_ticker
    ]
    all_relationships.extend(known)

    # 2. yfinance-derived relationships
    yf_rels = get_relationships_from_yfinance(ticker)
    all_relationships.extend(yf_rels)

    # 3. NER from news text
    if news_text:
        ner_rels = extract_relationships_from_text(base_ticker, news_text)
        all_relationships.extend(ner_rels)

    # Deduplicate
    seen = set()
    unique = []
    for r in all_relationships:
        key = (r[0], r[1])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    print(
        f"[Graph Builder] Total relationships for {base_ticker}: "
        f"{len(unique)} ({len(known)} known, {len(yf_rels)} yfinance, "
        f"{len(all_relationships)-len(known)-len(yf_rels)} NER)"
    )

    return unique