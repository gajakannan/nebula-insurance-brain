from __future__ import annotations

from fastapi import FastAPI

from brain_api.errors import install_problem_details_handlers
from brain_api.health import router as health_router
from brain_api.routes.content import router as content_router
from brain_api.routes.facts import router as facts_router
from brain_api.routes.reviews import router as reviews_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Nebula Insurance Brain API",
        version="0.1.0",
        openapi_url="/openapi.json",
    )
    install_problem_details_handlers(app)
    app.include_router(health_router)
    app.include_router(reviews_router)
    app.include_router(content_router)
    app.include_router(facts_router)
    return app


app = create_app()
