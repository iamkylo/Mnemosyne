"""
api/router.py

Central API router registry.

This is the single place where all versioned routers are assembled.
The pattern intentionally mirrors how LangSmith, OpenWebUI, and Dify
organise their API layers — a top-level router that composes version
sub-routers, which in turn compose feature routers.

Adding a new feature:
  1. Create `api/v1/your_feature.py`
  2. Import its router below
  3. Add one `v1_router.include_router(...)` line

Nothing else changes.
"""

from fastapi import APIRouter

from api.v1 import (
    auth,
    conversations,
    health,
    memory,
    providers,
    projects,
    retrieval,
    evaluation,
)

# ─────────────────────────────────────────────
# V1 sub-router
# ─────────────────────────────────────────────

v1_router = APIRouter()

v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
v1_router.include_router(
    conversations.router, prefix="/conversations", tags=["Conversations"]
)
v1_router.include_router(memory.router, prefix="/memory", tags=["Memory"])
v1_router.include_router(retrieval.router, prefix="/retrieval", tags=["Retrieval"])
v1_router.include_router(providers.router, prefix="/providers", tags=["Providers"])
v1_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation"])
v1_router.include_router(health.router, prefix="/health", tags=["Health"])

# Future v1 routes — append new feature routers here.

# ─────────────────────────────────────────────
# Top-level API router (mounts all versions)
# ─────────────────────────────────────────────

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1")

# When v2 is needed:
# api_router.include_router(v2_router, prefix="/v2")
