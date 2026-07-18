from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.core.ai_registry import AIServiceRegistry
from app.api.routes import health

from app.core.exceptions import (
    DocumentProcessingException,
    VectorStoreException
)

from app.core.exception_handlers import (
    document_exception_handler,
    vector_exception_handler
)

from app.core.middleware import (
    RequestLoggingMiddleware
)

from app.api.routes import search

@asynccontextmanager
async def lifespan(app: FastAPI):

    AIServiceRegistry.get_embedding_model()

    yield


app = FastAPI(
    lifespan=lifespan
)

app.include_router(upload_router)

app.include_router(health.router) # pyright: ignore[reportFunctionMemberAccess]

app.include_router(search.router)

app.add_exception_handler(
    DocumentProcessingException,
    document_exception_handler # pyright: ignore[reportArgumentType]
)

app.add_exception_handler(
    VectorStoreException,
    vector_exception_handler # pyright: ignore[reportArgumentType]
)

app.add_middleware(
    RequestLoggingMiddleware
)


@app.get("/")
def home():
    return {
        "message": "Welcome to AI Knowledge Assistant"
    }

# @app.get("/health")
# def health():
#     return {
#         "status": "healthy"
#     }

@app.get("/users")
def users():
    return {"users": []}