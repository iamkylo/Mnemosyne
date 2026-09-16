# 🧠 Mnemosyne - Interview Preparation Report

This document serves as a comprehensive guide to understanding the **Mnemosyne** project. It is structured to help you quickly review the project's architecture, key components, and prepare for potential interview questions.

---

## 1. Project Overview

### What is Mnemosyne?
Mnemosyne is a **persistent memory and knowledge-synthesis layer** designed for Large Language Models (LLMs). It acts as a digital hippocampus, ensuring that AI assistants (like ChatGPT, Claude, Gemini) retain context, specifications, and project choices across separate conversations.

### What problem does it solve?
Current LLM assistants are **stateless**. Every new chat requires the user to re-explain project goals, architecture, configurations, and past bug fixes. Mnemosyne solves this by continuously observing developer chats, distilling unstructured conversations into facts and intents, and storing them in a vector index. It automatically injects relevant past context into new chats.

---

## 2. Technology Stack

*   **Backend Framework:** Python 3.12, FastAPI
*   **Databases:**
    *   **PostgreSQL:** Relational database for user profiles, authentication, and project metadata.
    *   **Qdrant:** Vector database for storing and querying dense embeddings (semantic memory).
    *   **Redis:** Memory cache and asynchronous task queue.
*   **Client Interface:** Chrome Extension (Manifest V3) using local storage and service workers.
*   **AI Integration:** Adapters for Google Gemini, Groq, Ollama, and Hugging Face.
*   **Infrastructure:** Docker & Docker Compose for orchestration.

---

## 3. System Architecture

The architecture is split into three main layers: Client Side, Backend Core Service, and Storage.

### Client Side (Chrome Extension)
*   **Background Service Worker:** Captures chat messages and makes secure REST requests to the FastAPI backend.
*   **Content Script:** Observes the DOM to capture user inputs/AI responses and auto-injects retrieved context into the AI chat interface.

### Backend Core Service
*   **API Routers:** Handles authentication (JWT), project management, memory ingestion, and context retrieval.
*   **Memory Ingestion Pipeline (Async):** 
    1. Queues raw conversation.
    2. Fragments sentences (Chunking Engine).
    3. Extracts intents and bugs (LLM Fact Extractor).
    4. Computes embeddings.
    5. Relates entities (Knowledge Graph Engine).
    6. Synthesizes a "Project DNA".
*   **Retrieval Pipeline:**
    1. Performs semantic queries to the Qdrant database.
    2. Reranks and assembles facts (Context Builder).
    3. Optimizes the prompt context before sending it back to the client.

### Storage & Persistence
*   **PostgreSQL:** Source of truth for users and workspaces.
*   **Qdrant:** Stores the generated dense embeddings for fast similarity search.
*   **Redis:** Handles caching and the async job queue.

---

## 4. Key Workflows to Discuss

### 1. The Ingestion Flow (How memory is stored)
When a user chats with an LLM, the Chrome extension captures the text and sends it to the backend's `/api/v1/memory/ingest` endpoint. Because LLM extraction can be slow, this task is pushed to a **Redis queue**. A background worker picks it up, uses an AI Provider to extract facts, generates vector embeddings, and stores them in Qdrant.

### 2. The Retrieval Flow (How memory is used)
When a user starts a new chat, the extension requests context from the `/api/v1/retrieval` endpoint based on the initial prompt. The backend generates an embedding for the prompt, queries **Qdrant** for semantic similarity, retrieves the most relevant past facts, and the extension injects this into the LLM's prompt window.

---

## 5. Potential Interview Questions & Answers

**Q1: Why did you choose FastAPI for the backend?**
> **Answer:** FastAPI was chosen for its high performance, native support for asynchronous programming (critical for I/O bound tasks like calling external LLM APIs and databases), and automatic data validation using Pydantic. It also automatically generates Swagger documentation which made testing the API much easier.

**Q2: How do you handle the latency of processing memory?**
> **Answer:** Processing conversational text into facts and embeddings can be slow. I decoupled the ingestion process by using a message queue (Redis). The API responds immediately to the client acknowledging the data, while a background worker processes the chunking, LLM fact extraction, and vector storage asynchronously.

**Q3: Why use a Vector Database (Qdrant) instead of a traditional relational database?**
> **Answer:** While I use PostgreSQL for structured data (users, projects), a vector database is essential for semantic search. Traditional databases search by keyword matches, but Qdrant allows the system to search by *meaning*. If a user asks about "deployment", Qdrant can retrieve facts related to "Docker" or "CI/CD" because their vector embeddings are mathematically similar in the high-dimensional space.

**Q4: How does the Chrome Extension interact with the AI platforms?**
> **Answer:** The extension uses a Content Script injected into pages like ChatGPT or Claude. It observes the chat interface to capture what is being discussed. When a new chat starts, the extension fetches the context from the local FastAPI backend and dynamically manipulates the DOM to inject this context seamlessly into the prompt area before the user hits send.

**Q5: What was the most challenging part of this project?**
> **Answer:** *(Personalize this based on your experience. A good example is below)*
> Designing the memory extraction pipeline. Raw chat logs are noisy. The challenge was writing the right prompts for the "LLM Fact Extractor" to reliably separate useful project decisions and bug fixes from casual conversation, and assigning an "Importance Score" so that only high-quality facts are injected back into future context.

**Q6: How is the application deployed and managed locally?**
> **Answer:** I used Docker and Docker Compose to containerize the entire stack. This ensures that the FastAPI app, PostgreSQL, Redis, and Qdrant all run consistently across any machine without manual setup, solving the "it works on my machine" problem.

---

## 6. Closing Thoughts for the Interview
*   **Highlight the real-world value:** Emphasize that Mnemosyne reduces cognitive load and saves developers time.
*   **Demonstrate system design knowledge:** Talk confidently about decoupling components (using Redis for async tasks) and choosing the right database for the right job (PostgreSQL vs. Qdrant).
*   **Showcase modern tech:** Utilizing Vector Databases, LLM orchestration, and modern async Python puts you at the cutting edge of AI engineering.
