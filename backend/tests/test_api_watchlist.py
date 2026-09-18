def test_get_watchlist_has_ten_seeded_tickers(api_client):
    response = api_client.get("/api/watchlist")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    assert all("price" in entry for entry in body)


def test_add_ticker(api_client):
    response = api_client.post("/api/watchlist", json={"ticker": "pypl"})
    assert response.status_code == 200
    tickers = [entry["ticker"] for entry in response.json()]
    assert "PYPL" in tickers
    assert len(tickers) == 11


def test_add_duplicate_ticker_rejected(api_client):
    response = api_client.post("/api/watchlist", json={"ticker": "AAPL"})
    assert response.status_code == 400


def test_remove_ticker(api_client):
    response = api_client.delete("/api/watchlist/AAPL")
    assert response.status_code == 200
    tickers = [entry["ticker"] for entry in response.json()]
    assert "AAPL" not in tickers
    assert len(tickers) == 9


def test_remove_nonexistent_ticker_returns_404(api_client):
    response = api_client.delete("/api/watchlist/ZZZZ")
    assert response.status_code == 404
