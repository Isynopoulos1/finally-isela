"""FinAlly FastAPI app: API routers plus the built frontend static export."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import chat, health, portfolio, stream, watchlist
from db import repository
from db.connection import get_connection
from market.factory import make_provider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_connection()
    provider = make_provider()
    await provider.start(repository.list_watchlist())
    app.state.provider = provider
    yield
    await provider.stop()


app = FastAPI(title="FinAlly", lifespan=lifespan)

app.include_router(health.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(stream.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
