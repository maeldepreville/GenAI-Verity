import time
import logging
from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from config.settings import get_settings

# Configure logging to see progress
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGULATIONS_DIR = Path("data/regulations")
VECTOR_STORE_DIR = Path("data/vector_store/faiss_index")


def build_vector_store() -> None:
    _ = get_settings()  # Ensure env vars are loaded

    if not REGULATIONS_DIR.exists():
        logger.error(f"Directory {REGULATIONS_DIR} does not exist.")
        return

    # 1. Load Texts
    texts = []
    metadatas = []
    
    files = list(REGULATIONS_DIR.glob("*.txt"))
    if not files:
        logger.warning("No .txt files found in data/regulations.")
        return

    for file in files:
        logger.info(f"Processing {file.name}...")
        content = file.read_text(encoding="utf-8")
        texts.append(content)
        metadatas.append({"source": file.name})

    # 2. Split Texts
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )

    all_chunks = []
    all_metadatas = []

    for text, meta in zip(texts, metadatas):
        splits = splitter.split_text(text)
        all_chunks.extend(splits)
        all_metadatas.extend([meta] * len(splits))

    logger.info(f"Total chunks to embed: {len(all_chunks)}")

    # 3. Initialize Embeddings (Use text-embedding-004)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # 4. Batch Processing with Rate Limiting
    batch_size = 10  # Conservative batch size for free tier
    vectorstore = None
    
    total_batches = (len(all_chunks) + batch_size - 1) // batch_size

    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i : i + batch_size]
        batch_meta = all_metadatas[i : i + batch_size]
        
        current_batch = (i // batch_size) + 1
        logger.info(f"Embedding batch {current_batch}/{total_batches}...")

        try:
            if vectorstore is None:
                # First batch creates the index
                vectorstore = FAISS.from_texts(batch_chunks, embeddings, metadatas=batch_meta)
            else:
                # Subsequent batches add to it
                vectorstore.add_texts(batch_chunks, metadatas=batch_meta)
            
            # CRITICAL: Sleep to respect rate limits (RPM)
            # Free tier often allows ~15-60 requests per minute.
            # 2 seconds sleep + processing time should be safe.
            time.sleep(2) 

        except Exception as e:
            logger.error(f"Failed on batch {current_batch}: {e}")
            # Optional: Add retry logic here if needed, but sleep usually fixes it
            time.sleep(10) 
            # Try adding again or skip (depending on strictness)

    # 5. Save
    if vectorstore:
        VECTOR_STORE_DIR.parent.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(VECTOR_STORE_DIR)
        logger.info(f"✅ Vector store saved to {VECTOR_STORE_DIR}")
    else:
        logger.error("No vector store created (empty input?).")

if __name__ == "__main__":
    build_vector_store()