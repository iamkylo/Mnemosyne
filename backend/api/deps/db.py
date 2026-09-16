"""
api/deps/db.py

FastAPI dependency for database sessions.

By importing `get_db` from here, endpoints remain decoupled from the
underlying database implementation details in `database/session.py`.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db_session

# Type alias for cleaner endpoint signatures.
# Instead of `db: AsyncSession = Depends(get_db_session)`,
# endpoints can just use `db: AsyncSessionDep`.
AsyncSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
