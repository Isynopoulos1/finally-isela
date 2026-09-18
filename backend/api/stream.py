"""SSE stream of live prices for the current watchlist (PLAN.md §6)."""

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

TICK_SECONDS = 0.5


@router.get("/stream/prices")
async def stream_prices(request: Request):
    provider = request.app.state.provider

    async def event_generator():
        while not await request.is_disconnected():
            for update in provider.get_prices().values():
                payload = {
                    "ticker": update.ticker,
                    "price": update.price,
                    "prev_price": update.prev_price,
                    "change_pct": update.change_pct,
                    "timestamp": update.timestamp,
                }
                yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(TICK_SECONDS)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
