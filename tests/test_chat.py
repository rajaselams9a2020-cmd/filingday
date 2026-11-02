from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.llm.fake import FakeProvider
from app.main import app


def test_chat_streams_sse_events(monkeypatch):
    app.dependency_overrides[get_settings] = lambda: Settings(
        environment="test"
    )
    monkeypatch.setattr(
        "app.main.build_provider",
        lambda settings: FakeProvider(model="fake-model"),
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ],
                    "temperature": 0.2,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )
    assert "event: token" in response.text
    assert "Hello" in response.text
    assert "event: done" in response.text
    assert '"provider": "fake"' in response.text