"""
repositories/__init__.py

The data access layer.

Repositories are the only place that issues database queries.
They abstract all SQLAlchemy operations so that:
  * Services never touch the ORM directly
  * Database logic is centralised and testable in isolation
  * Swapping the underlying storage is a repository-level change only
"""

from .user import UserRepository
from .project import ProjectRepository
from .conversation import ConversationRepository
from .memory import MemoryRepository
from .provider import ProviderConfigRepository

__all__ = [
    "UserRepository",
    "ProjectRepository",
    "ConversationRepository",
    "MemoryRepository",
    "ProviderConfigRepository",
]
