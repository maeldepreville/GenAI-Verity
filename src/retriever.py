"""
The Search engine : it loads the saved FAISS index and provides functions to 
find the most relevant regulatory paragraphs based on a specific query.
"""

from pathlib import Path
from typing import List

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from config.settings import get_settings
import logging

# AWS
from requests_aws4auth import AWS4Auth
from opensearchpy import RequestsHttpConnection
import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_vector_store():
    """
    Load the persisted ECR vector store from AWS.
    """
    logger.info("Initialisation du Vector Store OpenSearch...")
    settings = get_settings()
    logger.info("Starting with AWS Credentials loading...")
    aws = settings._aws_credentials()
    
    
    # MUST MATCH ingestion.py model size of [768]
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    try:
        docsearch = OpenSearchVectorSearch(
            opensearch_url=aws.opsearch_endpoint,
            index_name=aws.index_name,
            embedding_function=embeddings,
            http_auth=aws.aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            vector_field="vector_field",
            text_field="text",
            timeout=120
        )
        logger.info("Client OpenSearch instancié avec succès !")
        return docsearch
    except Exception as e:
        logger.error(f"Impossible de créer le client OpenSearch : {e}")
        raise

def retrieve(vectorstore, query: str, k: int = 4) -> List[Document]:
    return vectorstore.similarity_search(query, k=k)

def retrieve_with_scores(vectorstore, query: str, k: int = 4):
    return vectorstore.similarity_search_with_score(query, k=k)