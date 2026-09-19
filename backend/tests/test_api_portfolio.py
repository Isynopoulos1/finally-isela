def test_get_portfolio_shape_on_fresh_db(api_client):
    response = api_client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["cash_balance"] == 10000.0
    assert body["positions"] == []
    assert len(body["watchlist"]) == 10
    assert body["total_value"] == 10000.0


def test_trade_rejects_invalid_side(api_client):
    response = api_client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "hold"}
    )
    assert response.status_code == 400
    assert "side" in response.json()["detail"].lower()


def test_trade_rejects_insufficient_cash(api_client):
    response = api_client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1_000_000, "side": "buy"}
    )
    assert response.status_code == 400
    assert "insufficient cash" in response.json()["detail"].lower()


def test_trade_rejects_insufficient_shares(api_client):
    response = api_client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "sell"}
    )
    assert response.status_code == 400
    assert "insufficient shares" in response.json()["detail"].lower()


def test_buy_updates_cash_and_creates_position(api_client):
    response = api_client.post(
        "/api/portfolio/trade", json={"ticker": "aapl", "quantity": 2, "side": "buy"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["positions"]) == 1
    position = body["positions"][0]
    assert position["ticker"] == "AAPL"
    assert position["quantity"] == 2
    cost = 2 * position["current_price"]
    assert body["cash_balance"] == 10000.0 - cost

    history = api_client.get("/api/portfolio/history").json()
    assert len(history) == 2  # seed snapshot + trade snapshot


def test_sell_full_position_removes_it_and_refunds_cash(api_client):
    api_client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 2, "side": "buy"})
    response = api_client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 2, "side": "sell"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["positions"] == []
    assert body["cash_balance"] == 10000.0
