from fastapi.testclient import TestClient

from app.main import app
from app.services.web_action_planner import make_web_action_plan

client = TestClient(app)


def test_direct_website_plan_uses_only_user_http_url() -> None:
    plan = make_web_action_plan("Please open https://example.org/products?tag=jarvis")
    assert plan == {
        "kind": "open_website",
        "label": "example.org",
        "url": "https://example.org/products?tag=jarvis",
    }


def test_youtube_plan_uses_generated_search_url(monkeypatch) -> None:
    monkeypatch.setattr("app.services.web_action_planner._model_classification", lambda _: None)
    plan = make_web_action_plan("Play lofi coding music on YouTube")
    assert plan["kind"] == "youtube_search"
    assert plan["url"] == "https://www.youtube.com/results?search_query=lofi+coding+music"


def test_web_action_endpoint_returns_constrained_plan(monkeypatch) -> None:
    monkeypatch.setattr("app.services.web_action_planner._model_classification", lambda _: None)
    response = client.post("/api/web-actions/plan", json={"text": "open the official NASA website"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "web_search"
    assert body["url"].startswith("https://www.google.com/search?q=")


def test_spotify_plan_uses_generated_search_url(monkeypatch) -> None:
    monkeypatch.setattr("app.services.web_action_planner._model_classification", lambda _: None)
    plan = make_web_action_plan("Play Hans Zimmer on Spotify")
    assert plan["kind"] == "spotify_search"
    assert plan["url"] == "https://open.spotify.com/search/Hans+Zimmer"


def test_hotstar_plan_uses_search_url(monkeypatch) -> None:
    monkeypatch.setattr("app.services.web_action_planner._model_classification", lambda _: None)
    plan = make_web_action_plan("Watch Stranger Things on JioHotstar")
    assert plan["kind"] == "hotstar_search"
    assert plan["url"] == "https://www.hotstar.com/in/explore?search_query=Stranger+Things"


def test_prime_video_plan_uses_search_url(monkeypatch) -> None:
    monkeypatch.setattr("app.services.web_action_planner._model_classification", lambda _: None)
    plan = make_web_action_plan("Watch The Boys on Prime Video")
    assert plan["kind"] == "prime_video_search"
    assert plan["url"] == "https://www.primevideo.com/search/ref=atv_nb_sr?phrase=The+Boys"


def test_netflix_plan_uses_search_url(monkeypatch) -> None:
    monkeypatch.setattr("app.services.web_action_planner._model_classification", lambda _: None)
    plan = make_web_action_plan("Watch Dark on Netflix")
    assert plan["kind"] == "netflix_search"
    assert plan["url"] == "https://www.netflix.com/search?q=Dark"


def test_github_plan_uses_search_url(monkeypatch) -> None:
    monkeypatch.setattr("app.services.web_action_planner._model_classification", lambda _: None)
    plan = make_web_action_plan("Search fast-api on GitHub")
    assert plan["kind"] == "github_search"
    assert plan["url"] == "https://github.com/search?q=fast-api"
