import os
import re
import io
from typing import Optional

def extract_text_from_pdf(pdf_bytes: bytes) -> str: # extract clean text from PDF bytes
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text.strip())
        full_text = "\n\n".join(text_parts)
        # Clean up whitespace
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        full_text = re.sub(r' {2,}', ' ', full_text)
        print(f"[PDF Agent] Extracted {len(full_text)} chars from PDF")
        return full_text
    except Exception as e:
        return f"[PDF Agent Error] {str(e)}"


def ingest_pdf_to_rag(pdf_bytes: bytes, source_name: str) -> bool: #extract PDF text and ingest into FAISS vector store
    text = extract_text_from_pdf(pdf_bytes)

    if not text or text.startswith("[PDF Agent Error]"):
        print(f"[PDF Agent] Extraction failed: {text}")
        return False

    if len(text.strip()) < 50:
        print("[PDF Agent] Extracted text too short - PDF may be scanned/image-based")
        return False

    try:
        import sys
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)

        from rag.ingest import ingest_documents
        from rag.retriever import invalidate_cache

        ingest_documents([{"text": text, "source": source_name}])
        invalidate_cache()
        print(f"[PDF Agent] Successfully ingested '{source_name}' into FAISS")
        return True

    except Exception as e:
        print(f"[PDF Agent] RAG ingestion failed: {e}")
        return False


def get_pdf_summary_text(pdf_bytes: bytes) -> str: #get first 3000 chars of PDF for quick LLM context
    text = extract_text_from_pdf(pdf_bytes)
    if not text or text.startswith("[PDF Agent Error]"):
        return ""
    return text[:3000]