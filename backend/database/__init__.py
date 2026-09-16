"""
database/__init__.py

Database infrastructure.

Centralises all SQLAlchemy and Alembic configuration:
  session.py     — Async SQLAlchemy engine + session factory
  base.py        — Declarative base shared by all ORM models
  migrations/    — Alembic migration scripts

Nothing outside this package creates database sessions directly.
All session access flows through the dependency injector in api/deps.py.
"""
