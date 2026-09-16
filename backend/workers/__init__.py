"""
workers/__init__.py

Background task workers.

Long-running or compute-intensive operations (document ingestion,
embedding generation, memory consolidation) are offloaded to workers
so they never block the HTTP request/response cycle.

Future workers (added in Milestone 5+):
  ingestion_worker.py     — Process uploaded documents asynchronously
  embedding_worker.py     — Generate and store vector embeddings
  consolidation_worker.py — Periodic memory graph consolidation
  cleanup_worker.py       — Prune stale chunks and expired sessions
"""
