import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.project import ProjectService


@pytest.mark.asyncio
async def test_delete_project_coordinates_vector_and_db_cleanup() -> None:
    session = MagicMock()

    with (
        patch("services.project.ProjectRepository") as mock_repo_cls,
        patch(
            "memory_engine.retrieval.vector_store.QdrantVectorStore"
        ) as mock_vector_cls,
    ):
        mock_repo = mock_repo_cls.return_value
        mock_repo.delete = AsyncMock(return_value=True)

        mock_vector = mock_vector_cls.return_value
        mock_vector.delete_memories_by_project = AsyncMock()

        service = ProjectService(session)
        result = await service.delete_project("test-project-123")

        # Verify vector store delete was called with the project_id
        mock_vector.delete_memories_by_project.assert_called_once_with(
            "test-project-123"
        )

        # Verify repository delete was called with the project_id
        mock_repo.delete.assert_called_once_with("test-project-123")

        # Verify final return value
        assert result is True
