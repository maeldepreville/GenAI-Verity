from unittest.mock import MagicMock, patch

from src.ingestion import build_vector_store

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


class DummyFile:
    def __init__(self, name: str, content: str) -> None:
        self.name = name
        self._content = content

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._content


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


@patch("src.ingestion.get_settings")
@patch("pathlib.Path.exists", return_value=False)
def test_build_vector_store_directory_missing(
    mock_exists: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    build_vector_store()

    mock_get_settings.assert_called_once()


@patch("src.ingestion.get_settings")
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.glob", return_value=[])
def test_build_vector_store_no_files(
    mock_glob: MagicMock,
    mock_exists: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    build_vector_store()

    mock_glob.assert_called_once()


@patch("src.ingestion.time.sleep")
@patch("src.ingestion.FAISS")
@patch("src.ingestion.GoogleGenerativeAIEmbeddings")
@patch("pathlib.Path.glob")
@patch("pathlib.Path.exists", return_value=True)
@patch("src.ingestion.get_settings")
def test_build_vector_store_happy_path(     # noqa: PLR0913
    mock_get_settings: MagicMock,
    mock_exists: MagicMock,
    mock_glob: MagicMock,
    mock_embeddings: MagicMock,
    mock_faiss: MagicMock,
    mock_sleep: MagicMock,
) -> None:
    dummy_files = [
        DummyFile("a.txt", "Regulation text A " * 100),
        DummyFile("b.txt", "Regulation text B " * 100),
    ]
    mock_glob.return_value = dummy_files

    vectorstore_instance = MagicMock()
    mock_faiss.from_texts.return_value = vectorstore_instance

    build_vector_store()

    mock_embeddings.assert_called_once()
    mock_faiss.from_texts.assert_called_once()
    vectorstore_instance.save_local.assert_called_once()
    assert mock_sleep.called
