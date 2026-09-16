"""
middleware/__init__.py

FastAPI / Starlette middleware modules.

Each file in this package defines one middleware class.
Middleware intercepts every HTTP request and response, making it
the right place for cross-cutting concerns that don't belong in
individual route handlers.

Future middleware (added in Milestone 2+):
  request_id.py      — Attach a unique UUID to every request
  timing.py          — Measure and log request processing time
  rate_limiting.py   — Per-user / per-IP request rate limits
  authentication.py  — Token validation for protected routes
  error_handler.py   — Global exception → structured JSON conversion
"""
