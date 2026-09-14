"""FastAPI entrypoint for Analytic Sages Data Portal."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from app.config import get_settings
from app.db import init_db
from app.routers import (
    admin_users,
    auth,
    dashboards,
    datasets,
    health,
    labs,
    query,
    studio,
    tokens,
    transfers,
    wallets,
)
from app.showcase import ensure_showcase

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    ensure_showcase()
    yield

app = FastAPI(
    title="Analytic Sages Data Portal API",
    description=(
        "API and catalog for Analytic Sages curated blockchain datasets. "
        "Learners discover schemas, SQL examples, labs, and sample queries "
        "on Analytic Sages curated blockchain datasets."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(datasets.router)
app.include_router(labs.router)
app.include_router(query.router)
app.include_router(studio.router)
app.include_router(dashboards.router)
app.include_router(tokens.router)
app.include_router(wallets.router)
app.include_router(transfers.router)


@app.get("/")
def root() -> dict:
    return {
        "product": "Analytic Sages Data Portal",
        "tagline": "Learn Blockchain Through Data.",
        "docs": "/docs",
        "catalog": "/datasets",
        "health": "/health",
        "query_policy": "/query/policy",
        "studio": "/studio/dashboards",
        "dashboards": "/dashboards",
        "learning_journey": "/learning-journey",
        "auth": "/auth/me",
        "admin_users": "/admin/users",
    }
