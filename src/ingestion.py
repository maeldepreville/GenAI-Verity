"""
This script takes .txt files of regulations, breaks them into 1,000-character
chunks, embeds them using Google's text-embedding-004 model, and saves them
into a FAISS vector store.
"""

import logging
import time
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGULATIONS_DIR = Path("data/regulations")
VECTOR_STORE_DIR = Path("data/vector_store/faiss_index")


def build_vector_store() -> None:
    # Ensure environment variables / settings are loaded
    get_settings()

    if not REGULATIONS_DIR.exists():
        logger.error("Directory %s does not exist.", REGULATIONS_DIR)
        return

    texts: list[str] = []
    metadatas: list[dict[str, str]] = []

    files = list(REGULATIONS_DIR.glob("*.txt"))
    if not files:
        logger.warning("No .txt files found in %s.", REGULATIONS_DIR)
        return

    for file in files:
        logger.info("Processing %s...", file.name)
        content = file.read_text(encoding="utf-8")
        texts.append(content)
        metadatas.append({"source": file.name})

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "],
    )

    all_chunks: list[str] = []
    all_metadatas: list[dict[str, str]] = []

    for text, metadata in zip(texts, metadatas, strict=True):
        splits = splitter.split_text(text)
        all_chunks.extend(splits)
        all_metadatas.extend([metadata] * len(splits))

    logger.info("Total chunks to embed: %d", len(all_chunks))

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
    )

    batch_size = 10
    vectorstore: FAISS | None = None

    total_batches = (len(all_chunks) + batch_size - 1) // batch_size

    for index in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[index : index + batch_size]
        batch_metadatas = all_metadatas[index : index + batch_size]

        current_batch = (index // batch_size) + 1
        logger.info(
            "Embedding batch %d/%d...",
            current_batch,
            total_batches,
        )

        try:
            if vectorstore is None:
                vectorstore = FAISS.from_texts(
                    batch_chunks,
                    embeddings,
                    metadatas=batch_metadatas,
                )
            else:
                vectorstore.add_texts(
                    batch_chunks,
                    metadatas=batch_metadatas,
                )

            time.sleep(2)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed on batch %d: %s",
                current_batch,
                exc,
            )
            time.sleep(10)

    if vectorstore is None:
        logger.error("No vector store created (empty input?).")
        return

    VECTOR_STORE_DIR.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTOR_STORE_DIR))
    logger.info("Vector store saved to %s", VECTOR_STORE_DIR)


if __name__ == "__main__":
    build_vector_store()
