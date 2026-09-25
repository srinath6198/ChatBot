<<<<<<< HEAD
# RAG Document Q&A Platform

A full-stack Retrieval-Augmented Generation (RAG) application that lets you upload documents and chat with them using a local LLM via Ollama.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite |
| Backend | FastAPI, SQLAlchemy |
| Database | MySQL 8 |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | Ollama (llama3.2) |

---

## Prerequisites

Make sure the following are installed before running the project:

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [MySQL 8](https://dev.mysql.com/downloads/) or [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/download/windows)

---

## Option A — Run Locally (Without Docker)

### 1. Ollama Setup

Install Ollama from https://ollama.com/download/windows, then pull the model:

```cmd
ollama pull llama3.2
```

Ollama starts automatically as a background service on port `11434`.

---

### 2. MySQL Setup

Create the database and user in MySQL:

```sql
CREATE DATABASE rag_db;
CREATE USER 'rag_user'@'localhost' IDENTIFIED BY 'srinath@10';
GRANT ALL PRIVILEGES ON rag_db.* TO 'rag_user'@'localhost';
FLUSH PRIVILEGES;
```

---

### 3. Backend Setup

```cmd
cd "d:\AI Project\Backend"
```

Create and activate a virtual environment:

```cmd
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

Create your `.env` file from the example:

```cmd
copy .env.example .env
```

Edit `.env` and set your values (DB password, JWT secret, etc.).

Start the backend:

```cmd
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

---

### 4. Frontend Setup

```cmd
cd "d:\AI Project\Frontend\Frontend"
```

Install dependencies:

```cmd
npm install
```

Start the dev server:

```cmd
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Option B — Run with Docker

Make sure Docker Desktop is running, then from the project root:

```cmd
cd "d:\AI Project"
docker-compose up --build
```

This starts MySQL, Ollama, and the Backend automatically.

> **Note:** After Docker starts, pull the model inside the Ollama container:
> ```cmd
> docker exec -it <ollama_container_name> ollama pull llama3.2
> ```

Then start the frontend separately (Docker does not include the frontend):

```cmd
cd "d:\AI Project\Frontend\Frontend"
npm install
npm run dev
```

---

## Environment Variables

All backend config is in `Backend/.env`. Copy from `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `rag_user` | MySQL username |
| `DB_PASSWORD` | `srinath@10` | MySQL password |
| `DB_NAME` | `rag_db` | MySQL database name |
| `JWT_SECRET_KEY` | — | Secret key for JWT tokens (change this!) |
| `JWT_EXPIRE_MINUTES` | `60` | Token expiry in minutes |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | LLM model name |
| `CHROMA_PERSIST_DIR` | `./chroma_store` | ChromaDB storage path |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `1000` | Document chunk size |
| `CHUNK_OVERLAP` | `150` | Chunk overlap |
| `TOP_K` | `5` | Number of chunks retrieved |
| `RERANK_TOP_N` | `3` | Chunks after reranking |
| `MAX_UPLOAD_SIZE_MB` | `25` | Max file upload size |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed frontend origins |

---

## How to Use

1. **Register** an account at http://localhost:5173
2. **Upload** PDF documents via the Documents page
3. Wait for the status to change to `embedded` (processing happens automatically)
4. **Create a chat session** and start asking questions about your documents

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user info |
| POST | `/api/v1/documents/upload` | Upload a PDF document |
| GET | `/api/v1/documents` | List all documents |
| DELETE | `/api/v1/documents/{id}` | Delete a document |
| POST | `/api/v1/chat/sessions` | Create a chat session |
| GET | `/api/v1/chat/sessions` | List chat sessions |
| GET | `/api/v1/chat/sessions/{id}/messages` | Get messages in a session |
| POST | `/api/v1/chat/message` | Send a message (RAG pipeline) |

Full interactive docs: http://localhost:8000/docs

---

## Troubleshooting

**`RAG pipeline error: No connection could be made`**
- Ollama is not running. Install from https://ollama.com/download/windows and pull the model: `ollama pull llama3.2`

**`Request canceled` or timeout in frontend**
- The LLM is taking too long. This is normal on first run or slow hardware. Wait for the model to warm up.

**`500 Internal Server Error` on chat**
- Check backend logs: `uvicorn` terminal output will show the exact error.

**MySQL connection error**
- Ensure MySQL is running and the `rag_db` database and `rag_user` exist with correct permissions.

**Frontend shows blank page**
- Make sure the backend is running on port `8000` before starting the frontend.
=======
# ChatBot
Chat Bot
>>>>>>> 08afb3a5d1e5db6e8f763640ea7f9b0451eea22b
