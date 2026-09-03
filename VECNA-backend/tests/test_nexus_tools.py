from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_telemetry() -> None:
    response = client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert "power_status" in data
    assert "system_time" in data


def test_vector_memory_flow() -> None:
    # Add memory
    add_res = client.post("/api/memory/add", json={"text": "User enjoys dark atmospheric audio design."})
    assert add_res.status_code == 200
    assert add_res.json()["ok"] is True

    # List memories
    list_res = client.get("/api/memory")
    assert list_res.status_code == 200
    memories = list_res.json()["memories"]
    assert any("dark atmospheric" in m["text"] for m in memories)


def test_system_tools_volume_and_media() -> None:
    # Test volume
    vol_res = client.post("/api/tools/execute", json={"tool": "volume", "level": 60})
    assert vol_res.status_code == 200
    assert vol_res.json()["ok"] is True

    # Test media
    media_res = client.post("/api/tools/execute", json={"tool": "media", "action": "play"})
    assert media_res.status_code == 200
    assert media_res.json()["ok"] is True


def test_silent_web_search(monkeypatch) -> None:
    def fake_search(query: str, max_results: int = 3):
        return [{"title": "Test Title", "snippet": "Test snippet", "href": "https://example.com"}]

    monkeypatch.setattr("app.api.nexus_tools.silent_web_search", fake_search)
    res = client.post("/api/tools/execute", json={"tool": "web_search", "query": "Vecna season 5"})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert len(res.json()["data"]) == 1


def test_screen_analyze(monkeypatch) -> None:
    def fake_analyze(query: str):
        return "I see code editors and terminal sessions open on your mortal screen."

    monkeypatch.setattr("app.api.nexus_tools.analyze_desktop", fake_analyze)
    res = client.post("/api/screen/analyze", json={"query": "What is open?"})
    assert res.status_code == 200
    assert "mortal screen" in res.json()["analysis"]
