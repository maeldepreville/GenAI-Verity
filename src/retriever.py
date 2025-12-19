from pathlib import Path
from typing import List

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config.settings import get_settings

VECTOR_STORE_DIR = Path("data/vector_store/faiss_index")

def load_vector_store():
    """
    Load the persisted FAISS vector store from disk.
    """
    _ = get_settings()
    
    # MUST MATCH ingestion.py model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    return FAISS.load_local(
        VECTOR_STORE_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )

def retrieve(vectorstore, query: str, k: int = 4) -> List[Document]:
    return vectorstore.similarity_search(query, k=k)

def retrieve_with_scores(vectorstore, query: str, k: int = 4):
    return vectorstore.similarity_search_with_score(query, k=k)