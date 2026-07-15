from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.core.ai_registry import AIServiceRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):

    AIServiceRegistry.get_embedding_model()

    yield


app = FastAPI(
    lifespan=lifespan
)

app.include_router(upload_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to AI Knowledge Assistant"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/users")
def users():
    return {"users": []}