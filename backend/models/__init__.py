"""
models/__init__.py

SQLAlchemy ORM model definitions.

Each file in this package maps to one or more database tables.
Models define the shape of persisted data — they are never used
directly in API responses (that's the schemas package's job).
"""

from .user import User
from .project import Project
from .conversation import Conversation
from .message import Message
from .chunk import Chunk
from .memory import Memory
from .relationship import KnowledgeRelationship
from .project_dna import ProjectDna
from .provider_config import ProviderConfig

__all__ = [
    "User",
    "Project",
    "Conversation",
    "Message",
    "Chunk",
    "Memory",
    "KnowledgeRelationship",
    "ProjectDna",
    "ProviderConfig",
]
