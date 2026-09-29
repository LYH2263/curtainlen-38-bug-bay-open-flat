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


def set_default_depth(client, value):
    client.put("/api/settings/default_bay_depth", json={"value": str(value)})


def run_count(client):
    return len(client.get("/api/runs").json()["items"])


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
    set_default_depth(client, 0.6)
    r = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1})
    assert r.json()["bay_depth"] == 0.6
    assert r.json()["cut_height"] == 3.45


def test_saved_run_is_pinned_against_later_changes(client):
    set_bay(client, 1, True, 0.4)
    set_default_depth(client, 0.5)
    r = client.post("/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True, "note": "钉住"})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    assert run_id
    # 之后改窗户进深与默认进深，甚至关掉飘窗，都不应改写旧单
    set_bay(client, 1, False, 0.9)
    set_default_depth(client, 1.2)
    runs = client.get("/api/runs").json()["items"]
    saved = next(x for x in runs if x["id"] == run_id)
    assert saved["result"]["bay_enabled"] is True
    assert saved["result"]["bay_depth"] == 0.4
    assert saved["result"]["cut_height"] == 3.25
    assert saved["result"]["meters"] == 16.25


def test_three_views_equal_written_snapshot_after_depth_change_and_bay_toggle(client):
    # 以同参写入一编号
    set_bay(client, 1, True, 0.4)
    set_default_depth(client, 0.5)
    written = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).json()
    cut_w, meters_w, depth_w = written["cut_height"], written["meters"], written["bay_depth"]
    run_id = client.post(
        "/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True, "note": "三路一致"}
    ).json()["run_id"]

    # 先改窗户登记进深、再改设置侧默认进深口径，然后关掉飘窗再打开（开关最终仍为开启）
    set_bay(client, 1, True, 0.9)
    set_default_depth(client, 1.2)
    set_bay(client, 1, False, 0.9)
    set_bay(client, 1, True, 0.9)

    # 历史列表：主字段与飘窗摘要
    row = next(x for x in client.get("/api/runs").json()["items"] if x["id"] == run_id)
    assert row["result"]["bay_enabled"] is True
    assert row["result"]["bay_depth"] == depth_w          # 不被现行 0.9 覆盖
    assert row["result"]["cut_height"] == cut_w           # 不退回未加进深口径
    assert row["result"]["meters"] == meters_w            # 米数不跟着掉
    assert row["bay_summary"]["bay_depth"] == depth_w
    assert row["bay_summary"]["cut_height"] == cut_w
    assert row["bay_summary"]["meters"] == meters_w

    # 详情：主字段与飘窗摘要
    d = client.get(f"/api/runs/{run_id}").json()
    assert d["result"]["bay_depth"] == depth_w
    assert d["result"]["cut_height"] == cut_w
    assert d["result"]["meters"] == meters_w
    assert d["bay_summary"]["bay_depth"] == depth_w
    assert d["bay_summary"]["cut_height"] == cut_w
    assert d["bay_summary"]["meters"] == meters_w

    # 三路裁高/米数互比，全部等于写入快照
    three = [
        (row["result"]["cut_height"], row["result"]["meters"]),
        (d["result"]["cut_height"], d["result"]["meters"]),
        (d["bay_summary"]["cut_height"], d["bay_summary"]["meters"]),
    ]
    assert three == [(cut_w, meters_w)] * 3

    # 重复打开幂等：底层落库 JSON 从未被回写
    d2 = client.get(f"/api/runs/{run_id}").json()
    assert (d2["result"]["cut_height"], d2["result"]["meters"]) == (cut_w, meters_w)


def test_nonpositive_depth_with_bay_on_fails_order_without_inserting(client):
    before = run_count(client)
    set_bay(client, 1, True, 0.0)
    r = client.post("/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True})
    assert r.status_code == 422
    assert run_count(client) == before                    # 整单失败，不增行


def test_bench_recompute_matches_snapshot_bayoff_dryrun_smaller_and_no_rewrite(client):
    set_bay(client, 1, True, 0.4)
    set_default_depth(client, 0.5)
    run_id = client.post(
        "/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True, "note": "算料台"}
    ).json()["run_id"]
    snap = client.get(f"/api/runs/{run_id}").json()["result"]

    # 算料台以写入时同参再算：裁高与米数等于该编号回看值
    again = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).json()
    assert (again["cut_height"], again["meters"]) == (snap["cut_height"], snap["meters"])

    # 同参关闭飘窗干算：裁高/米数更小
    set_bay(client, 1, False, None)
    off = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).json()
    assert off["bay_enabled"] is False
    assert off["cut_height"] < snap["cut_height"]
    assert off["meters"] < snap["meters"]

    # 干算不得改写已写入编号
    snap2 = client.get(f"/api/runs/{run_id}").json()["result"]
    assert snap2["bay_enabled"] is True
    assert (snap2["cut_height"], snap2["meters"], snap2["bay_depth"]) == (
        snap["cut_height"], snap["meters"], 0.4,
    )


def test_current_window_and_settings_depth_only_bind_new_runs(client):
    # 先开进深 0.4 落一单旧快照
    set_bay(client, 1, True, 0.4)
    set_default_depth(client, 0.5)
    old_id = client.post(
        "/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True, "note": "旧单0.4"}
    ).json()["run_id"]

    # 现行进深改 0.7、设置侧口径改 1.1：只作用于此后新算
    set_bay(client, 1, True, 0.7)
    set_default_depth(client, 1.1)
    new = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).json()
    assert new["bay_depth"] == 0.7
    assert new["cut_height"] == round(2.85 + 0.7, 3)

    old = client.get(f"/api/runs/{old_id}").json()["result"]
    assert (old["bay_depth"], old["cut_height"]) == (0.4, 3.25)
