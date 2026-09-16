"""
services/__init__.py

Business logic layer.

This package exposes factories for all service classes used by the API layer.
"""

from .auth import AuthService, get_auth_service
from .conversation import ConversationService, get_conversation_service
from .health import HealthCheckService, get_health_check_service
from .memory import MemoryService, get_memory_service
from .project import ProjectService, get_project_service
from .providers import ProviderService, get_provider_service
from .search import RetrievalService, get_retrieval_service

__all__ = [
    "AuthService",
    "get_auth_service",
    "ConversationService",
    "get_conversation_service",
    "HealthCheckService",
    "get_health_check_service",
    "MemoryService",
    "get_memory_service",
    "ProjectService",
    "get_project_service",
    "ProviderService",
    "get_provider_service",
    "RetrievalService",
    "get_retrieval_service",
]
