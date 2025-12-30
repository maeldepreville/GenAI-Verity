"""
Search engine utilities: load the OpenSearch-backed vector store and retrieve
relevant regulatory documents.
"""

import logging

from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from opensearchpy import RequestsHttpConnection

from config.settings import get_settings

logger = logging.getLogger(__name__)


def load_vector_store() -> OpenSearchVectorSearch:
    """
    Load the persisted OpenSearch vector store from AWS.
    """
    logger.info("Initializing OpenSearch vector store...")
    settings = get_settings()
    aws = settings._aws_credentials()

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
    )

    try:
        vector_store = OpenSearchVectorSearch(
            opensearch_url=aws.opsearch_endpoint,
            index_name=aws.index_name,
            embedding_function=embeddings,
            http_auth=aws.aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            vector_field="vector_field",
            text_field="text",
            timeout=120,
        )
        logger.info("OpenSearch vector store initialized successfully.")
        return vector_store
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Failed to create OpenSearch vector store: %s",
            exc,
        )
        raise


def retrieve(
    vectorstore: OpenSearchVectorSearch,
    query: str,
    k: int = 4,
) -> list[Document]:
    """
    Retrieve the top-k most similar documents for a query.
    """
    return vectorstore.similarity_search(query, k=k)


def retrieve_with_scores(
    vectorstore: OpenSearchVectorSearch,
    query: str,
    k: int = 4,
) -> list[tuple[Document, float]]:
    """
    Retrieve the top-k most similar documents along with similarity scores.
    """
    return vectorstore.similarity_search_with_score(query, k=k)
