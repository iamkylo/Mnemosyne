"""
providers/__init__.py

AI provider abstraction layer.

Each file wraps one external AI API behind a consistent interface.
The application never calls Groq, Gemini, or Ollama directly —
it always goes through a provider module.

This means:
  * Switching from Groq to Gemini is a one-line config change.
  * Rate limiting, retry logic, and timeout handling live in one place.
  * Mocking providers in tests is straightforward.

Provider modules (added in Milestone 4+):
  groq.py         — Groq Cloud (LLaMA, Mixtral, Gemma)
  gemini.py       — Google Gemini
  ollama.py       — Local Ollama models
  huggingface.py  — HuggingFace Inference API
  router.py       — Intelligent provider routing / fallback logic
"""
