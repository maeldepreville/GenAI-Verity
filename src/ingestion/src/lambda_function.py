import os
import json
import time
import logging
import urllib.parse
from typing import Any, Dict, List, Optional

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")


def _get_aoss_client() -> OpenSearch:
    """
    OpenSearch Serverless client using SigV4.
    - Local: uses AWS CLI profile (AWS_PROFILE)
    - Lambda: uses IAM execution role automatically
    """

    host = os.environ["OPENSEARCH_HOST"]
    region = os.environ.get("OPENSEARCH_REGION", "eu-north-1")

    # IMPORTANT:
    # If AWS_PROFILE is set, boto3 will use AWS CLI / SSO credentials.
    # If not (Lambda), it will fall back to the execution role.
    session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE"))

    credentials = session.get_credentials()
    frozen_creds = credentials.get_frozen_credentials()

    awsauth = AWS4Auth(
        frozen_creds.access_key,
        frozen_creds.secret_key,
        region,
        "aoss", # REQUIRED for OpenSearch Serverless
        session_token=frozen_creds.token,
    )

    return OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
        max_retries=0,
        retry_on_timeout=False,
    )

def _bulk_index(client: OpenSearch, index_name: str, docs: List[Dict[str, Any]]) -> None:
    """
    Indexation des vecteurs optimisée pour OpenSearch Serverless.
    Note : Serverless ne supporte pas l'ID personnalisé dans l'action bulk.
    """
    lines = []
    for d in docs:
        # Pour Serverless, on retire l'ID de l'en-tête de l'index
        # L'ID sera généré automatiquement par OpenSearch
        lines.append(json.dumps({"index": {"_index": index_name}}))
        
        # On prépare le corps du document
        doc_source = dict(d)
        
        # stocker l'ID de base
        if "_id" in doc_source:
            doc_source["doc_id_reference"] = doc_source.pop("_id")
            
        lines.append(json.dumps(doc_source))

    if not lines:
        return

    payload = "\n".join(lines) + "\n"
    resp = client.bulk(body=payload)

    if resp.get("errors"):
        for item in resp.get('items', []):
            index_action = item.get('index', {})
            if index_action.get('error'):
                logger.info(f"Détail de l'erreur d'indexation : {index_action['error']}")
        raise RuntimeError("Bulk indexing failed")
    
    logger.info(f"Indexation successfull of {len(docs)} documents. Alright !")


def lambda_handler(event, context):
    """
    Trigger: S3 ObjectCreated
    Writes to an EXISTING OpenSearch index that uses:
      - embedding (knn_vector, dim 768)
      - text (text)
      - metadata.source, metadata.article
    """
    
    logger.info("Event: %s", json.dumps(event))

    index_name = os.environ.get("OPENSEARCH_INDEX", "index-gemini")
    chunk_size = int(os.environ.get("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", "200"))
    embed_batch_size = int(os.environ.get("EMBED_BATCH_SIZE", "10"))
    sleep_seconds = float(os.environ.get("EMBED_SLEEP_SECONDS", "0"))
    
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
    except Exception as e:
        logger.warning(f"Erreur SSM : {e}")
        api_key = None

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key = api_key) # W/ Gemini

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "],
    )

    os_client = _get_aoss_client()

    records = event.get("Records", [])
    if not records:
        return {"statusCode": 400, "body": "No Records in event"}

    for r in records:
        bucket = r["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(r["s3"]["object"]["key"])

        # Optional Filters
        allowed_suffixes = tuple(x.strip().lower() for x in os.environ.get("ALLOWED_SUFFIXES", ".txt").split(","))
        if allowed_suffixes and not key.lower().endswith(allowed_suffixes):
            logger.info("Skipping object (suffix filter): %s", key)
            continue

        logger.info("Processing s3://%s/%s", bucket, key)

        obj = s3.get_object(Bucket=bucket, Key=key)
        raw = obj["Body"].read()
        text = raw.decode("utf-8", errors="replace")

        chunks = splitter.split_text(text)
        if not chunks:
            logger.warning("No chunks produced for %s", key)
            continue

        filename = key.split("/")[-1]
        article = os.path.splitext(filename)[0]

        # Embed + bulk index
        for i in range(0, len(chunks), embed_batch_size):
            batch_chunks = chunks[i : i + embed_batch_size]
            vectors = embeddings.embed_documents(batch_chunks)

            docs = []
            for j, (chunk_text, vec) in enumerate(zip(batch_chunks, vectors)):
                chunk_id = i + j

                doc = {
                    "_id": f"{bucket}/{key}#{chunk_id}",
                    "vector_field": vec,  
                    "text": chunk_text,
                    "metadata": {
                        "source": f"s3://{bucket}/{key}",
                        "article": article,
                    },
                }
                docs.append(doc)
            
            _bulk_index(os_client, index_name, docs)

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            if context.get_remaining_time_in_millis() < 3000:
                raise TimeoutError("Not enough time left to finish safely")

    return {"statusCode": 200, "body": " OK !!!"}
