"""
schemas/__init__.py

Pydantic v2 schema definitions.

Schemas define the shape of data crossing API boundaries:
  * Request bodies — what the client sends
  * Response bodies — what the API returns
  * Internal DTOs — data transferred between service layers

Schemas are intentionally separate from SQLAlchemy models.
A database model describes storage; a schema describes the API contract.
"""
