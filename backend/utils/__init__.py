"""
utils/__init__.py

Shared utility functions and helpers.

Small, stateless, pure functions that are used across multiple
modules but don't belong to any specific domain layer.

Rules:
  * No business logic — that belongs in services/.
  * No database access — that belongs in repositories/.
  * No AI logic — that belongs in memory_engine/.
  * Every function here should be trivially unit-testable.

Future utilities (added as needed):
  text.py       — Text cleaning, normalisation, truncation
  hashing.py    — Content fingerprinting (SHA-256, xxHash)
  datetime.py   — Timezone-aware datetime helpers
  pagination.py — Cursor and offset pagination helpers
  retry.py      — Exponential backoff decorator
"""
