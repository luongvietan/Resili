from fastapi import FastAPI
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Resili API",
        version="0.1.0",
        docs_url="/docs",
    )
    return app


app = create_app()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/")
async def root():
    return {"version": "v1", "docs": "/docs"}
