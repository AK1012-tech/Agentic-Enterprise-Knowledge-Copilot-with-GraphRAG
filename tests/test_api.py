import pytest
from app.main import create_app

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_feedback_endpoint():
    client = TestClient(create_app())
    response = client.post(
        "/feedback",
        json={
            "session_id": "s1",
            "question": "q",
            "answer": "a",
            "rating": 5,
            "comment": "useful",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"
