from fastapi import FastAPI

app = FastAPI(
    title="AI Knowledge Assistant",
    version="1.0.0"
)


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