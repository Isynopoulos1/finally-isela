def test_health_ok(api_client):
    response = api_client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "market_provider": "simulator"}
