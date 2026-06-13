import os
from pathlib import Path
from typing import List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index")

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 800,
    overlap: int = 100,
) -> List[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_text(text)
    return [
        {
            "text": chunk,
            "source": source,
            "chunk_id": f"{source}_{i}",
        }
        for i, chunk in enumerate(chunks)
    ]

def ingest_documents(documents: List[dict]) -> FAISS:
    embeddings = get_embeddings()
    all_chunks = []
    for doc in documents:
        text = doc.get("text", "").strip()
        if not text:
            continue
        all_chunks.extend(
            chunk_text(
                text=text,
                source=doc["source"],
            )
        )

    if not all_chunks:
        raise ValueError("No valid text found for ingestion.")

    texts = [c["text"] for c in all_chunks]
    metadatas = [
        {
            "source": c["source"],
            "chunk_id": c["chunk_id"],
        }
        for c in all_chunks
    ]

    Path(FAISS_INDEX_PATH).mkdir(parents=True, exist_ok=True)
    index_file = Path(FAISS_INDEX_PATH) / "index.faiss"

    new_sources = {
        doc["source"]
        for doc in documents
        if doc.get("source")
    }

    if index_file.exists():
        try:
            existing = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True,
            )
            old_docs = existing.docstore._dict
            kept_texts = []
            kept_metas = []

            for doc_id, doc in old_docs.items():
                doc_source = doc.metadata.get("source", "")
                if not any(
                    doc_source.startswith(src) or src.startswith(doc_source)
                    for src in new_sources
                ):
                    kept_texts.append(doc.page_content)
                    kept_metas.append(doc.metadata)
            final_texts = kept_texts + texts
            final_metas = kept_metas + metadatas

            vectorstore = FAISS.from_texts(
                final_texts,
                embeddings,
                metadatas=final_metas,
            )

            vectorstore.save_local(FAISS_INDEX_PATH)
            invalidate_cache()

            print(
                f"[RAG] Index updated: {len(final_texts)} chunks"
            )
            return vectorstore
        except Exception as e:
            print(f"[RAG] Smart merge failed: {e}")

    vectorstore = FAISS.from_texts(
        texts,
        embeddings,
        metadatas=metadatas,
    )

    vectorstore.save_local(FAISS_INDEX_PATH)
    invalidate_cache()

    print(
        f"[RAG] Fresh index created: {len(texts)} chunks"
    )

    return vectorstore

def load_vectorstore() -> Optional[FAISS]:
    index_file = Path(FAISS_INDEX_PATH) / "index.faiss"
    if not index_file.exists():
        return None

    return FAISS.load_local(
        FAISS_INDEX_PATH,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def invalidate_cache():
    try:
        from rag.retriever import invalidate_cache as _invalidate
        _invalidate()

    except Exception:
        pass