import sentry_sdk
from fastapi import FastAPI, Request

from app.core.config import settings
from app.core.errors import register_exception_handlers

_sentry_initialized: bool = False


def create_app() -> FastAPI:
    global _sentry_initialized
    if settings.SENTRY_DSN and not _sentry_initialized:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
        )
        _sentry_initialized = True

    app = FastAPI(
        title="Resili API",
        version="0.1.0",
        docs_url="/docs",
    )

    # Register error handlers
    register_exception_handlers(app)

    # BSD Attribution header middleware (NFR-11)
    @app.middleware("http")
    async def add_attribution_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Powered-By"] = "Resili (built on Scrapling - BSD License)"
        return response

    return app


app = create_app()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/")
async def root():
    return {"version": "v1", "docs": "/docs"}
