"""
Tests for Mergington High School API (src/app.py).

Uses starlette.testclient.TestClient (sync) which is bundled with FastAPI.
Each test runs against a fresh copy of the activities state via the
`reset_activities` autouse fixture — src/app.py is never modified.
"""

import copy
import pytest
from starlette.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after every test."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    response = client.get("/")
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_all_activities():
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == len(app_module.activities)


def test_get_activities_structure():
    response = client.get("/activities")
    data = response.json()
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]
    assert "newstudent@mergington.edu" in app_module.activities["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    # michael@mergington.edu is already in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


def test_unregister_not_enrolled_returns_404():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "noone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not signed up" in response.json()["detail"].lower()


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Nonexistent Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
