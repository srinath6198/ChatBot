rag-project/
├── docker-compose.yml          # MySQL + Ollama + backend, wired together
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app entrypoint, CORS, router mounting
│       ├── config.py           # Settings (env-driven)
│       ├── database.py         # SQLAlchemy engine/session (MySQL)
│       ├── models.py           # User, Document, DocumentChunk, ChatSession, ChatMessage
│       ├── schemas.py          # Pydantic request/response models
│       ├── auth.py             # JWT + password hashing + auth dependencies
│       │
│       ├── api/                # ← Document API / Chat API / Admin API
│       │   ├── __init__.py
│       │   ├── auth_routes.py  # /auth/register, /login, /me
│       │   ├── documents.py    # /documents (upload, list, get, delete)
│       │   ├── chat.py         # /chat/sessions, /chat/message
│       │   └── admin.py        # /admin/stats, /admin/users, /admin/documents
│       │
│       └── services/           # ← Document Processing / Retriever / Reranker / LLM
│           ├── __init__.py
│           ├── document_processor.py  # extract text (PDF/txt/md) + chunk
│           ├── embeddings.py          # HuggingFace embeddings
│           ├── vector_store.py        # Chroma persistent client
│           ├── retriever.py           # similarity search + cross-encoder rerank
│           ├── llm.py                 # Ollama (Llama 3.2) client
│           └── rag_chain.py           # ties retrieve → rerank → generate (+ Langfuse hook)
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx              # auth gate + shell layout
        ├── index.css
        ├── api/
        │   └── client.ts        # axios client + typed API calls
        └── components/
            ├── Auth.tsx          # login/register
            ├── DocumentSidebar.tsx  # upload + doc list/status
            └── Chat.tsx          # sessions + chat window

=========================================================


            React Frontend
      ↓
FastAPI Backend
      ↓
   RAG Pipeline
      ↓
   ChromaDB
      ↓
   Ollama
      ↓
 llama3.2