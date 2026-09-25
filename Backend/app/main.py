from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import init_db, engine
from app.api import auth_routes, documents, chat, admin
from app.services.retriever import get_reranker
from app.services.embeddings import get_embedding_model


app = FastAPI(title=settings.APP_NAME)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup
@app.on_event("startup")
def on_startup():
    init_db()
    get_embedding_model()
    get_reranker()


# Root API
@app.get("/")
def root():
    return {
        "message": "API is running",
        "app": settings.APP_NAME
    }


# Health check
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME
    }


# Database connection test
@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "success",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "not connected",
            "error": str(e)
        }


# API routes
app.include_router(
    auth_routes.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    documents.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    chat.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    admin.router,
    prefix=settings.API_V1_PREFIX
)