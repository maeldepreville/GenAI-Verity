from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.retriever import (
    load_vector_store,
    retrieve,
    retrieve_with_scores,
)

# ---------------------------------------------------------------------
# retrieve()
# ---------------------------------------------------------------------


def test_retrieve_calls_similarity_search() -> None:
    mock_store = MagicMock()
    expected_docs: list[Document] = [
        Document(page_content="doc 1"),
        Document(page_content="doc 2"),
    ]
    mock_store.similarity_search.return_value = expected_docs

    result = retrieve(
        vectorstore=mock_store,
        query="access control",
        k=2,
    )

    mock_store.similarity_search.assert_called_once_with(
        "access control",
        k=2,
    )
    assert result == expected_docs


# ---------------------------------------------------------------------
# retrieve_with_scores()
# ---------------------------------------------------------------------


def test_retrieve_with_scores_calls_similarity_search_with_score() -> None:
    mock_store = MagicMock()
    expected_results: list[tuple[Document, float]] = [
        (Document(page_content="doc 1"), 0.9),
        (Document(page_content="doc 2"), 0.8),
    ]
    mock_store.similarity_search_with_score.return_value = expected_results

    result = retrieve_with_scores(
        vectorstore=mock_store,
        query="encryption",
        k=2,
    )

    mock_store.similarity_search_with_score.assert_called_once_with(
        "encryption",
        k=2,
    )
    assert result == expected_results


# ---------------------------------------------------------------------
# load_vector_store()
# ---------------------------------------------------------------------


@patch("src.retriever.OpenSearchVectorSearch")
@patch("src.retriever.GoogleGenerativeAIEmbeddings")
@patch("src.retriever.get_settings")
def test_load_vector_store_happy_path(
    mock_get_settings: MagicMock,
    mock_embeddings: MagicMock,
    mock_opensearch: MagicMock,
) -> None:
    mock_settings = MagicMock()
    mock_aws = MagicMock()

    mock_aws.opsearch_endpoint = "https://example-opensearch"
    mock_aws.index_name = "test-index"
    mock_aws.aws_auth = MagicMock()

    mock_settings._aws_credentials.return_value = mock_aws
    mock_get_settings.return_value = mock_settings

    store_instance = MagicMock()
    mock_opensearch.return_value = store_instance

    result = load_vector_store()

    mock_embeddings.assert_called_once()
    mock_opensearch.assert_called_once()
    assert result is store_instance
