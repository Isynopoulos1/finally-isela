import json

import httpx


def test_stream_prices_emits_parseable_sse_events(live_server):
    with httpx.Client() as client, client.stream(
        "GET", f"{live_server}/api/stream/prices", timeout=5
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        lines = []
        for line in response.iter_lines():
            if line:
                lines.append(line)
            if lines:
                break

    assert lines[0].startswith("data: ")
    payload = json.loads(lines[0][len("data: ") :])
    assert set(payload) == {"ticker", "price", "prev_price", "change_pct", "timestamp"}
