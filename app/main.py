from fastapi import FastAPI
from app.api.upload import router as upload_router

app = FastAPI(
    title="AI Knowledge Assistant",
    version="1.0.0"
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