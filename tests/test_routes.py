import pytest
from fastapi.testclient import TestClient


def test_home_page(client: TestClient):
    """Test home page returns 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "WvW Analytics" in response.text


def test_analyze_page(client: TestClient):
    """Test analyze page returns 200."""
    response = client.get("/analyze")
    assert response.status_code == 200
    assert "Upload EVTC Log" in response.text


def test_meta_zerg_page(client: TestClient):
    """Test META zerg page returns 200."""
    response = client.get("/meta/zerg")
    assert response.status_code == 200
    assert "Zerg" in response.text


def test_meta_guild_raid_page(client: TestClient):
    """Test META guild raid page returns 200."""
    response = client.get("/meta/guild_raid")
    assert response.status_code == 200
    assert "Guild Raid" in response.text


def test_meta_roam_page(client: TestClient):
    """Test META roam page returns 200."""
    response = client.get("/meta/roam")
    assert response.status_code == 200
    assert "Roam" in response.text


def test_404_page(client: TestClient):
    """Test 404 page for non-existent route."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "404" in response.text


def test_fight_detail_not_found(client: TestClient):
    """Test fight detail page returns 404 for non-existent fight."""
    response = client.get("/analyze/fight/999")
    assert response.status_code == 404
