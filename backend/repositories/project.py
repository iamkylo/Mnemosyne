"""
repositories/project.py

Data access for projects and project DNA.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.project import Project
from models.project_dna import ProjectDna


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: str) -> Project | None:
        statement = select(Project).where(Project.id == project_id)
        result = await self._session.execute(statement)
        return result.scalars().first()

    async def create(self, project: Project) -> Project:
        self._session.add(project)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def update(self, project: Project, values: dict) -> Project:
        for key, value in values.items():
            setattr(project, key, value)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def list_for_owner(self, owner_id: int) -> list[Project]:
        statement = (
            select(Project).where(Project.owner_id == owner_id).order_by(Project.name)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get_dna(self, project_id: str) -> ProjectDna | None:
        statement = select(ProjectDna).where(ProjectDna.project_id == project_id)
        result = await self._session.execute(statement)
        return result.scalars().first()

    async def upsert_dna(self, project_id: str, dna: dict[str, object]) -> ProjectDna:
        existing = await self.get_dna(project_id)
        if existing is None:
            dna_model = ProjectDna(project_id=project_id, dna=dna)
            self._session.add(dna_model)
            await self._session.commit()
            await self._session.refresh(dna_model)
            return dna_model

        existing.dna = dna
        await self._session.commit()
        await self._session.refresh(existing)
        return existing

    async def delete(self, project_id: str) -> bool:
        from sqlalchemy import delete
        from models.memory import Memory
        from models.relationship import KnowledgeRelationship
        from models.chunk import Chunk
        from models.message import Message
        from models.conversation import Conversation
        from models.project_dna import ProjectDna
        from models.project import Project

        # 1. Delete memories
        await self._session.execute(
            delete(Memory).where(Memory.project_id == project_id)
        )
        # 2. Delete relationships
        await self._session.execute(
            delete(KnowledgeRelationship).where(
                KnowledgeRelationship.project_id == project_id
            )
        )
        # 3. Delete chunks
        await self._session.execute(delete(Chunk).where(Chunk.project_id == project_id))
        # 4. Delete messages
        await self._session.execute(
            delete(Message).where(
                Message.conversation_id.in_(
                    select(Conversation.id).where(Conversation.project_id == project_id)
                )
            )
        )
        # 5. Delete conversations
        await self._session.execute(
            delete(Conversation).where(Conversation.project_id == project_id)
        )
        # 6. Delete project DNA
        await self._session.execute(
            delete(ProjectDna).where(ProjectDna.project_id == project_id)
        )
        # 7. Delete the project itself
        result = await self._session.execute(
            delete(Project).where(Project.id == project_id)
        )
        await self._session.commit()
        return result.rowcount > 0
