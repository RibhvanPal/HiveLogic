import os
from pathlib import Path
from typing import List, Dict, Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index")

_vectorstore_cache = None
_embeddings_cache = None


def get_embeddings():
    global _embeddings_cache

    if _embeddings_cache is None:
        _embeddings_cache = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

    return _embeddings_cache


def get_vectorstore() -> Optional[FAISS]:
    global _vectorstore_cache

    index_dir = Path(FAISS_INDEX_PATH)
    index_file = index_dir / "index.faiss"

    if not index_file.exists():
        _vectorstore_cache = None
        return None

    if _vectorstore_cache is None:
        try:
            _vectorstore_cache = FAISS.load_local(
                FAISS_INDEX_PATH,
                get_embeddings(),
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            print(f"[RAG] Failed to load FAISS index: {e}")
            return None

    return _vectorstore_cache
def load_report_vectorstore(report_id): #Load FAISS belonging to a specific report

    try:

        path = (
            Path("data")
            / "vectorstores"
            / report_id
        )

        index_file = path / "index.faiss"

        if not index_file.exists():
            return None

        return FAISS.load_local(
            str(path),
            get_embeddings(),
            allow_dangerous_deserialization=True,
        )

    except Exception as e:
        print(
            f"[RAG] Failed loading report vectorstore: {e}"
        )
        return None
    
def retrieve_report_chunks(
    report_id: str,
    query: str,
    k: int = 5,
): #Retrieve chunks from a report-specific FAISS

    vs = load_report_vectorstore(
        report_id
    )
    if vs is None:
        return []
    try:
        results = (
            vs.similarity_search_with_score(
                query,
                k=k,
            )
        )
        chunks = []
        for doc, score in results:
            chunks.append(
                {
                    "text":
                        doc.page_content,

                    "source":
                        doc.metadata.get(
                            "source",
                            "unknown",
                        ),

                    "chunk_id":
                        doc.metadata.get(
                            "chunk_id",
                            "",
                        ),

                    "score":
                        float(score),
                }
            )

        return chunks

    except Exception as e:
        print(
            f"[RAG] Report retrieval failed: {e}"
        )
        return []

def retrieve_chunks(query: str, k: int = 5) -> List[Dict]:
    vs = get_vectorstore()
    if vs is None:
        return []
    try:
        results = vs.similarity_search_with_score(query, k=k)
        chunks = []
        for doc, score in results:
            chunks.append(
                {
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", ""),
                    "score": float(score),
                }
            )
        return chunks
    except Exception as e:
        print(f"[RAG] Retrieval failed: {e}")
        return []

def invalidate_cache():
    global _vectorstore_cache
    _vectorstore_cache = None