import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="curtainlen-bay-test-")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def set_bay(client, wid, enabled, depth):
    r = client.put(f"/api/windows/{wid}/bay", json={"bay_enabled": enabled, "bay_depth": depth})
    assert r.status_code == 200
    return r.json()


def test_bay_off_keeps_base_cut_height(client):
    set_bay(client, 1, False, None)
    r = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["bay_enabled"] is False
    assert body["bay_depth"] == 0.0
    assert body["cut_height"] == 2.85
    assert body["meters"] == 14.25


def test_bay_on_adds_depth_to_cut_height(client):
    set_bay(client, 1, True, 0.4)
    r = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["bay_enabled"] is True
    assert body["bay_depth"] == 0.4
    assert body["cut_height"] == 3.25
    assert body["panels"] == 5
    assert body["meters"] == 16.25


def test_seeded_bay_window_estimates_with_depth(client):
    r = client.get("/api/estimate", params={"window_id": 2, "fabric_id": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["bay_enabled"] is True
    assert body["bay_depth"] == 0.45
    assert body["cut_height"] == 2.2
    assert body["meters"] == 8.8


def test_bay_on_with_nonpositive_depth_rejected(client):
    set_bay(client, 1, True, 0.0)
    assert client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).status_code == 422
    set_bay(client, 1, True, -0.5)
    assert client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).status_code == 422
    r = client.post("/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True})
    assert r.status_code == 422


def test_bay_depth_falls_back_to_default_setting(client):
    set_bay(client, 1, True, None)
    r = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1})
    assert r.status_code == 200
    assert r.json()["bay_depth"] == 0.5
    assert r.json()["cut_height"] == 3.35
    client.put("/api/settings/default_bay_depth", json={"value": "0.6"})
    r = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1})
    assert r.json()["bay_depth"] == 0.6
    assert r.json()["cut_height"] == 3.45


def test_saved_run_is_pinned_against_later_changes(client):
    set_bay(client, 1, True, 0.4)
    client.put("/api/settings/default_bay_depth", json={"value": "0.5"})
    r = client.post("/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True, "note": "钉住"})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    assert run_id
    # 之后改窗户进深与默认进深，甚至关掉飘窗，都不应改写旧单
    set_bay(client, 1, False, 0.9)
    client.put("/api/settings/default_bay_depth", json={"value": "1.2"})
    runs = client.get("/api/runs").json()["items"]
    saved = next(x for x in runs if x["id"] == run_id)
    assert saved["result"]["bay_enabled"] is True
    assert saved["result"]["bay_depth"] == 0.4
    assert saved["result"]["cut_height"] == 3.25
    assert saved["result"]["meters"] == 16.25
