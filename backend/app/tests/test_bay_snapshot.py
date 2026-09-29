import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="curtainlen-snapshot-test-")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def restore_seed_bay_state(client):
    # 测试模块共享同一 sqlite 文件，每个用例后把窗户/设置恢复到种子值，
    # 避免污染其它测试文件。
    yield
    client.put("/api/windows/1/bay", json={"bay_enabled": False, "bay_depth": None})
    client.put("/api/windows/2/bay", json={"bay_enabled": True, "bay_depth": 0.45})
    client.put("/api/settings/default_bay_depth", json={"value": "0.5"})


def set_bay(client, wid, enabled, depth):
    r = client.put(f"/api/windows/{wid}/bay", json={"bay_enabled": enabled, "bay_depth": depth})
    assert r.status_code == 200
    return r.json()


def open_run_three_ways(client, run_id):
    """同一编号的三路裁高/米数：列表摘要、详情主字段、飘窗摘要。"""
    listed = next(x for x in client.get("/api/runs").json()["items"] if x["id"] == run_id)
    detail = client.get(f"/api/runs/{run_id}").json()
    return {
        "list": (listed["result"]["cut_height"], listed["result"]["meters"]),
        "list_summary": (listed["bay_summary"]["cut_height"], listed["bay_summary"]["meters"]),
        "detail": (detail["result"]["cut_height"], detail["result"]["meters"]),
        "bay_summary": (detail["bay_summary"]["cut_height"], detail["bay_summary"]["meters"]),
    }


def test_written_snapshot_is_truth_after_depth_change_and_bay_toggle(client):
    # 写入：窗户1 + 面料1，开启飘窗、进深 0.4
    set_bay(client, 1, True, 0.4)
    written = client.post(
        "/api/estimate", json={"window_id": 1, "fabric_id": 1, "save": True, "note": "快照"}
    ).json()
    run_id = written["run_id"]
    assert written["cut_height"] == 3.25
    assert written["meters"] == 16.25
    # 进深与裁高分列
    assert written["bay_depth"] == 0.4
    assert written["cut_height"] != written["bay_depth"]

    # 先改窗户侧进深，再改设置侧进深口径，然后关掉飘窗再打开
    set_bay(client, 1, True, 0.9)
    client.put("/api/settings/default_bay_depth", json={"value": "1.2"})
    set_bay(client, 1, False, 0.9)
    set_bay(client, 1, True, 0.9)
    # 飘窗开关此时仍为开启
    assert client.get("/api/windows/1").json()["bay_enabled"] == 1

    views = open_run_three_ways(client, run_id)
    # 裁高不得退回未加进深口径（2.85），米数不得跟着掉
    assert views["list"] == (3.25, 16.25)
    assert views["detail"] == (3.25, 16.25)
    # 列表、详情与飘窗摘要三路须一致且等于写入快照
    assert views["list_summary"] == views["list"]
    assert views["bay_summary"] == views["detail"]
    assert views["list"] == views["detail"]

    listed = next(x for x in client.get("/api/runs").json()["items"] if x["id"] == run_id)
    assert listed["result"]["bay_enabled"] is True
    assert listed["result"]["bay_depth"] == 0.4
    # 落库行不得被打开视图打上任何实时重算标记
    assert "open_bay_flat" not in listed["result"]
    assert "open_bay_rebased" not in listed["result"]
    assert "open_live_synced" not in listed["result"]


def test_nonpositive_depth_fails_whole_order_without_new_row(client):
    before = len(client.get("/api/runs").json()["items"])
    for depth in (0.0, -0.3):
        set_bay(client, 2, True, depth)
        assert client.get(
            "/api/estimate", params={"window_id": 2, "fabric_id": 1}
        ).status_code == 422
        r = client.post(
            "/api/estimate", json={"window_id": 2, "fabric_id": 1, "save": True}
        )
        assert r.status_code == 422
    after = len(client.get("/api/runs").json()["items"])
    assert after == before  # 整单失败，不增行


def test_bench_recompute_matches_snapshot_flat_is_smaller_and_does_not_rewrite(client):
    # 算料台恢复写入时同参（进深 0.4、开启飘窗）再算
    set_bay(client, 1, True, 0.4)
    again = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).json()
    assert again["cut_height"] == 3.25
    assert again["meters"] == 16.25

    # 找到此前写入的编号，回看值须与再算一致
    run_id = next(
        x["id"]
        for x in client.get("/api/runs").json()["items"]
        if x["note"] == "快照"
    )
    detail = client.get(f"/api/runs/{run_id}").json()
    assert detail["result"]["cut_height"] == again["cut_height"]
    assert detail["result"]["meters"] == again["meters"]

    # 同参关闭飘窗干算：裁高与米数必须更小
    set_bay(client, 1, False, 0.4)
    flat = client.get("/api/estimate", params={"window_id": 1, "fabric_id": 1}).json()
    assert flat["bay_enabled"] is False
    assert flat["cut_height"] == 2.85 < 3.25
    assert flat["meters"] == 14.25 < 16.25

    # 干算不得改写已写入编号
    detail = client.get(f"/api/runs/{run_id}").json()
    assert detail["result"]["cut_height"] == 3.25
    assert detail["result"]["meters"] == 16.25
    assert detail["result"]["bay_enabled"] is True
    assert detail["result"]["bay_depth"] == 0.4
