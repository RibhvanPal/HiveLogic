import re
from .state import HiveLogicState
from rag.retriever import retrieve_chunks

RAG_DISTANCE_THRESHOLD = 1.3
MIN_WORD_OVERLAP = 0.25

def classify_claim_source(claim: str) -> str:
    claim_lower = claim.lower()
    if any(
        word in claim_lower
        for word in [
            "sentiment",
            "bullish",
            "bearish",
            "analyst",
        ]
    ):
        return "sentiment"

    if any(
        word in claim_lower
        for word in [
            "taiwan",
            "china",
            "tsmc",
            "foxconn",
            "supply chain",
            "contagion",
            "geopolitical",
            "regulation",
        ]
    ):
        return "contagion"
    return "filing"

def verification_agent_node(state: HiveLogicState) -> HiveLogicState:
    print("[Verification Agent] Verifying claims")
    source_text = state.get("risk_summary", "")

    if not source_text:
        return {
            **state,
            "verified": False,
            "verified_claims": [],
            "verification_notes": "No content available for verification.",
        }

    print("\nVERIFICATION SOURCE")
    print(source_text[:3000])
    print("==============================\n")

    claims = []

    # bullet points
    claims.extend(
        re.findall(
            r"^\s*[*•+-]\s+(.+)$",
            source_text,
            re.MULTILINE,
        )
    )

    # numbered points
    claims.extend(
        re.findall(
            r"^\s*\d+\.\s+(.+)$",
            source_text,
            re.MULTILINE,
        )
    )

    # fallback: split into lines
    if not claims:
        return {
            **state,
            "verified": False,
            "verified_claims": [],
            "verification_notes":
                "No bullet-point claims found.",
        }

    # remove duplicates
    claims = list(dict.fromkeys(claims))

    # remove short garbage fragments
    claims = [
        c.strip()
        for c in claims
        if len(c.strip()) > 40
        and "None explicitly mentioned" not in c
    ]

    print(
        f"[Verification] Extracted "
        f"{len(claims)} claims"
    )

    print("\nCLAIMS")
    for c in claims:
        print(c)
    print("============================\n")

    if not claims:
        return {
            **state,
            "verified": False,
            "verified_claims": [],
            "verification_notes": "No structured claims found.",
        }

    verified_claims = []
    notes = []

    for claim in claims[:10]:
        source_type = classify_claim_source(claim)
        try:
            print(
                f"[Verification] Claim: "
                f"{claim[:120]}"
            )
            if source_type != "filing":

                verified_claims.append(
                    {
                        "claim": claim,
                        "evidence": "",
                        "source": source_type,
                        "source_type": source_type,
                        "chunk_id": "",
                        "score": 0,
                        "overlap": 1.0,
                    }
                )

                notes.append(
                    f"{source_type.upper()}_SUPPORTED: "
                    f"{claim[:60]}"
                )

                continue
            chunks = retrieve_chunks(claim, k=3)

            print(
                f"[Verification] Retrieved "
                f"{len(chunks)} chunks"
            )

            if chunks:
                print(
                    f"[Verification] Best source: "
                    f"{chunks[0]['source']}"
                )

                print(
                    f"[Verification] Distance: "
                    f"{chunks[0]['score']}"
                )

            if not chunks:
                notes.append(
                    f"NO_EVIDENCE: {claim[:60]}"
                )
                continue

            best = chunks[0]

            claim_words = set(
                re.findall(
                    r"\w+",
                    claim.lower(),
                )
            )

            evidence_words = set(
                re.findall(
                    r"\w+",
                    best["text"].lower(),
                )
            )

            overlap = (
                len(claim_words & evidence_words)
                / max(len(claim_words), 1)
            )

            print(
                f"[Verification] Overlap: "
                f"{overlap:.2f}"
            )

            if best["score"] > RAG_DISTANCE_THRESHOLD:

                notes.append(
                    f"WEAK_MATCH "
                    f"({best['score']:.3f}): "
                    f"{claim[:60]}"
                )

                continue

            if overlap < MIN_WORD_OVERLAP:

                notes.append(
                    f"LOW_OVERLAP "
                    f"({overlap:.2f}): "
                    f"{claim[:60]}"
                )

                continue

            verified_claims.append(
                {
                    "claim": claim,
                    "evidence": best["text"][:500],
                    "source": best["source"],
                    "source_type": source_type,
                    "chunk_id": best["chunk_id"],
                    "score": best["score"],
                    "overlap": round(overlap, 2),
                }
            )

            notes.append(
                f"SUPPORTED "
                f"({best['score']:.3f}, "
                f"overlap={overlap:.2f}): "
                f"{claim[:60]}"
            )

        except Exception as e:

            notes.append(
                f"ERROR: "
                f"{claim[:60]} -> {str(e)}"
            )

    verified = (
        len(claims) > 0
        and len(verified_claims) / len(claims) >= 0.75
    )

    print(
        f"[Verification] "
        f"{len(verified_claims)}/{len(claims)} "
        f"claims supported"
    )

    return {
        **state,
        "verified": verified,
        "verified_claims": verified_claims,
        "verification_notes": "\n".join(notes),
    }