import os
import re
import requests
from .state import HiveLogicState
from bs4 import BeautifulSoup
EDGAR_HEADERS = {"User-Agent": "HiveLogic research@hivelogic.ai"}


def download_filing_text(cik: str, accession: str) -> str:
    # download actual SEC filing text.
    try:
        cik = str(int(cik))
        accession_clean = accession.replace("-", "")
        filing_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik}/{accession_clean}/{accession}-index.html"
        )
        print(f"[Filing Agent] Filing URL: {filing_url}")

        resp = requests.get(
            filing_url,
            headers=EDGAR_HEADERS,
            timeout=20,
        )
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")
        filing_doc = None
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all(["td", "th"])
                if len(cols) < 4:
                    continue
                doc_type = cols[3].get_text(strip=True)
                if doc_type.upper() == "10-K":
                    link = cols[2].find("a")

                    if link:
                        filing_doc = link.get("href")
                        print(
                            f"[Filing Agent] Found 10-K document: "
                            f"{filing_doc}"
                        )
                        break

            if filing_doc:
                break

        if not filing_doc:
            return ""
        if filing_doc.startswith("/ix?doc="):
            filing_doc = filing_doc.replace("/ix?doc=", "")
        if not filing_doc.startswith("http"):
            filing_doc = (
                "https://www.sec.gov"
                + filing_doc
            )
        print(f"[Filing Agent] Downloading filing: {filing_doc}")

        filing_resp = requests.get(
            filing_doc,
            headers=EDGAR_HEADERS,
            timeout=30,
        )
        print(
            f"[Filing Agent] Filing response status: "
            f"{filing_resp.status_code}"
        )

        if filing_resp.status_code != 200:
            return ""

        filing_soup = BeautifulSoup(
            filing_resp.text,
            "html.parser",
        )
        for tag in filing_soup([
            "script",
            "style",
            "ix:header",
            "ix:hidden",
        ]):
            tag.decompose()

        content = (
            filing_soup.find(id="formDiv")
            or filing_soup.find(class_="formContent")
        )

        if content:
            text = content.get_text(
                separator="\n",
                strip=True,
            )
        else:
            body = filing_soup.find("body")
            if body:
                text = body.get_text(
                    separator="\n",
                    strip=True,
                )
            else:
                text = filing_soup.get_text(
                    separator="\n",
                    strip=True,
                )

        # Remove SEC/XBRL garbage
        text = re.sub(
            r"http://fasb\.org/[^\s]+",
            "",
            text,
        )
        text = re.sub(
            r"us-gaap:[A-Za-z0-9_]+",
            "",
            text,
        )
        text = re.sub(
            r"[A-Za-z0-9]+:[A-Za-z0-9_]+Member",
            "",
            text,
        )
        text = re.sub(
            r"\bP\d+[DYM]\b",
            "",
            text,
        )
        text = re.sub(
            r"\biso4217:[A-Z]+\b",
            "",
            text,
        )
        text = re.sub(
            r"\bxbrli:[A-Za-z]+\b",
            "",
            text,
        )
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )
        text = re.sub(
            r"[ \t]{2,}",
            " ",
            text,
        )

        print(
            f"[Filing Agent] Preview:\n"
            f"{text[:3000]}"
        )
        print(f"[Filing Agent] Filing text length: {len(text)}")

        return text

    except Exception as e:
        print(
            f"[Filing Agent] Filing download failed: {e}"
        )
        return ""
    
def fetch_edgar_filing(ticker: str) -> str: # fetch latest 10-K summary from SEC EDGAR (2023 onwards only)
    try:
        search_url = (
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
            f"&forms=10-K&dateRange=custom&startdt=2023-01-01"
        )
        resp = requests.get(search_url, headers=EDGAR_HEADERS, timeout=10)

        print(resp.status_code)
        print(resp.text[:1000])
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])

        if not hits:
            return f"No recent 10-K filing found for {ticker} on SEC EDGAR."

        filing = None

        for hit in hits:
            source = hit["_source"]
            file_date = source.get("file_date", "")
            if file_date >= "2023-01-01":
                filing = source
                break

        if filing is None:
            return f"No recent 10-K filing found for {ticker} on SEC EDGAR."
        file_date = filing.get("file_date", "")

        # Reject anything before 2023
        if file_date and file_date < "2023-01-01":
            return f"No recent 10-K filing found for {ticker} on SEC EDGAR."

        company = (
            filing.get("display_names", [ticker])[0]
        )
        form_type = (
            filing.get("root_forms", ["10-K"])[0]
        )
        period = filing.get("period_ending", "")
        cik = filing.get("ciks", [""])[0]
        adsh = filing.get("adsh", "")
        # Reject if period is unknown
        if not period:
            period = "Not available"

        filing_text = download_filing_text(
            cik=cik,
            accession=adsh,
        )

        if filing_text:
            print(
                f"[Filing Agent] Downloaded filing size: "
                f"{len(filing_text)} chars"
            )
            print(
                f"[Filing Agent] Estimated chunks: "
                f"{len(filing_text) // 500}"
            )
            return filing_text[:1000000]

        return (
            f"Filing: {form_type} for {company} ({ticker})\n"
            f"Period: {period} | Filed: {file_date}\n"
            f"This filing covers the company's financial performance, "
            f"risk factors, and management discussion for the reported period. "
            f"Full text available via SEC EDGAR.\n"
            f"Source: https://www.sec.gov/cgi-bin/browse-edgar?"
            f"action=getcompany&company={ticker}&type=10-K"
        )

    except Exception as e:
        return f"[Filing Agent] Could not fetch EDGAR data: {str(e)}"


def is_valid_filing(text: str) -> bool: # check if filing text is reliable enough
    bad_signals = [
        "No recent 10-K filing",
        "unknown period",
        "[Filing Agent]",
        "No verified filing",
        "Please upload a PDF",
        "Access Denied",
        "Request Rate Threshold Exceeded",
        "SEC.gov |"
    ]
    return not any(s in text for s in bad_signals)


def extract_metrics_from_text(text: str) -> dict:
    metrics = {}
    clean = text.replace(",", "")

    patterns = [
        ("revenue_from_filing", [
            r'[Rr]evenue\s+from\s+[Oo]perations[^\d]*?([\d]+)',
            r'[Tt]otal\s+[Rr]evenue[^\d]*?([\d]+)',
        ]),
        ("net_profit_from_filing", [
            r'[Nn]et\s+[Pp]rofit\s+[Aa]fter\s+[Tt]ax[^\d]*?([\d]+)',
            r'[Nn]et\s+[Pp]rofit[^\d]*?([\d]+)',
        ]),
    ]

    for key, pats in patterns:
        for pat in pats:
            m = re.search(pat, clean)
            if m:
                metrics[key] = m.group(1)
                break

    float_patterns = {
        "profit_margin":
            r'[Nn]et\s+[Pp]rofit\s+[Mm]argin\s*[\|:]?\s*([\d.]+)\s*%',
        "current_ratio":
            r'[Cc]urrent\s+[Rr]atio\s*[\|:]?\s*([\d.]+)',
        "debt_to_equity":
            r'[Dd]ebt.to.[Ee]quity\s*(?:[Rr]atio)?\s*[\|:]?\s*([\d.]+)',
        "roe":
            r'[Rr]eturn\s+on\s+[Ee]quity[^\d]*?([\d.]+)\s*%',
        "roa":
            r'[Rr]eturn\s+on\s+[Aa]ssets[^\d]*?([\d.]+)\s*%',
        "gross_profit_margin":
            r'[Gg]ross\s+[Pp]rofit\s+[Mm]argin\s*[\|:]?\s*([\d.]+)\s*%',
    }

    for key, pat in float_patterns.items():
        m = re.search(pat, text)
        if m:
            try:
                val = float(m.group(1))
                # ROE/ROA/margins stored as decimals
                if key in ["profit_margin", "gross_profit_margin", "roe", "roa"]:
                    metrics[key] = val / 100 if val > 1 else val
                else:
                    metrics[key] = val
            except ValueError:
                pass

    if metrics:
        print(f"[Filing Agent] Extracted: {list(metrics.keys())}")
    return metrics


def filing_agent_node(state: HiveLogicState) -> HiveLogicState: #LangGraph node: fetch filing text
    ticker = state["company_ticker"]
    errors = state.get("errors", [])
    print(f"[Filing Agent] Processing {ticker}")

    # Priority 1: PDF chunks in FAISS (ticker-scoped)
    try:
        from rag.retriever import retrieve_chunks
        base_ticker = ticker.split(".")[0].upper()
        chunks = retrieve_chunks(
            f"{ticker} financial performance risk factors", k=8
        )
        # only chunks whose source name contains this ticker
        pdf_chunks = [
            c for c in chunks
            if c.get(
                "source",
                ""
            ).lower().startswith(
                f"pdf_{base_ticker.lower()}_"
            )
        ]
        if pdf_chunks:
            print(f"[Filing Agent] Using {len(pdf_chunks)} PDF chunks for {ticker}")
            combined_text = "\n\n".join(c["text"] for c in pdf_chunks)
            final_metrics = state.get("financial_metrics", {})
            if not final_metrics or not any(
                v for v in final_metrics.values() if v
            ):
                extracted = extract_metrics_from_text(combined_text)
                if extracted:
                    extracted["company_name"] = ticker
                    final_metrics = extracted
            return {
                **state,
                "filings_text": combined_text,
                "financial_metrics": final_metrics,
                "errors": errors,
            }
    except Exception as e:
        print(f"[Filing Agent] PDF check failed: {e}")

    # Priority 2: SEC EDGAR (only for known/US tickers)
    base = ticker.split(".")[0].upper()
    text = ""

    if not ticker.upper().endswith((".NS", ".BO")):
        text = fetch_edgar_filing(ticker)

        print("\nEDGAR RESPONSE")
        print(text[:2000])
        print("====================================\n")

        if not is_valid_filing(text):
            print(f"[Filing Agent] Invalid EDGAR filing for {ticker}")
            text = ""  # discard bad EDGAR data
        else:
            # only ingest valid and recent EDGAR filings into FAISS
            try:
                from rag.ingest import ingest_documents
                print("[Filing Agent] Ingesting EDGAR into FAISS")
                ingest_documents([{"text": text, "source": f"edgar_{base}"}])
                print("[Filing Agent] EDGAR ingestion complete")
            except Exception as e:
                print(f"[Filing Agent] FAISS ingest skipped: {e}")

    if not text:
        text = (
            f"No verified filing available for {ticker}. "
            f"Upload a PDF annual report for detailed analysis."
        )
        errors = errors + [f"No EDGAR filing found for {ticker}"]

    if text.startswith("[Filing Agent]"):
        errors = errors + [text]
        text = f"Filing data unavailable for {ticker}."

    # extract metrics from text if yfinance returned nothing
    final_metrics = state.get("financial_metrics", {})
    if not final_metrics or not any(v for v in final_metrics.values() if v):
        extracted = extract_metrics_from_text(text)
        if extracted:
            extracted["company_name"] = ticker
            final_metrics = extracted

    return {
        **state,
        "filings_text": text,
        "financial_metrics": final_metrics,
        "errors": errors,
    }