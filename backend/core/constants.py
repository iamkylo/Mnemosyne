"""
core/constants.py

Application-wide constants.

Rule: nothing here is environment-specific. If a value might differ
between development, staging, and production it belongs in config.py.
"""

from enum import Enum


# ─────────────────────────────────────────────────────────────────────────────
# Environment identifiers
# ─────────────────────────────────────────────────────────────────────────────


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# ─────────────────────────────────────────────────────────────────────────────
# Response status strings
# ─────────────────────────────────────────────────────────────────────────────


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


# ─────────────────────────────────────────────────────────────────────────────
# API
# ─────────────────────────────────────────────────────────────────────────────

API_V1_PREFIX: str = "/api/v1"

# ─────────────────────────────────────────────────────────────────────────────
# HTTP header names  (avoids magic strings scattered across the codebase)
# ─────────────────────────────────────────────────────────────────────────────

HEADER_REQUEST_ID: str = "X-Request-ID"
HEADER_PROCESS_TIME: str = "X-Process-Time"
HEADER_API_VERSION: str = "X-API-Version"

# ─────────────────────────────────────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# ─────────────────────────────────────────────────────────────────────────────
# Timeouts (seconds)
# ─────────────────────────────────────────────────────────────────────────────

HTTP_CLIENT_TIMEOUT: int = 30  # outbound calls to AI providers
DATABASE_QUERY_TIMEOUT: int = 10  # per-query budget
