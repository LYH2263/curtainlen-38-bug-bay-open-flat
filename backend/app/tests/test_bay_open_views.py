from app.services.bay_open import detail_view_bay, list_view_bay, restore_snapshot, summary_view_bay

RAW = {"bay_enabled": True, "bay_depth": 0.3, "cut_height": 2.8, "meters": 8.4, "panels": 3}
DIMS = {"height": 2.4, "hem_top": 0.1, "hem_bottom": 0.1, "width": 2.0, "fabric_width": 1.4, "fullness": 2.0}


def test_list_returns_written_snapshot_ignoring_live_depth():
    out = list_view_bay(RAW, DIMS, live_depth=0.5)
    assert out["cut_height"] == 2.8          # 不得拍平成去进深口径
    assert out["meters"] == 8.4              # 米数随裁高钉住
    assert out["bay_depth"] == 0.3           # 不被现行进深 0.5 覆盖
    assert out["bay_enabled"] is True


def test_detail_matches_list_snapshot():
    out = detail_view_bay(RAW, DIMS, live_depth=0.5)
    assert out["cut_height"] == 2.8          # 不得用 flat+live 重加成 3.1
    assert out["meters"] == 8.4
    assert out["bay_depth"] == 0.3
    assert "open_view" not in out
    assert "open_bay_rebased" not in out


def test_summary_carries_same_cut_meters_and_separate_depth():
    out = summary_view_bay(RAW, DIMS, live_depth=0.5)
    assert out["cut_height"] == 2.8
    assert out["meters"] == 8.4
    assert out["bay_depth"] == 0.3           # 进深与裁高分列
    assert out["bay_enabled"] is True


def test_legacy_restamped_row_is_restored_to_pin_on_read():
    # 旧 live sync 留下的污染行：主字段被拍平/重加，真值只在 pin 里。
    polluted = dict(RAW)
    polluted.update({
        "cut_height": 2.5,            # 被错误拍平
        "meters": 7.5,
        "bay_depth": 0.5,             # 被现行进深覆盖
        "list_cut_height_pin": 2.8,
        "list_meters_pin": 8.4,
        "open_bay_flat": True,
        "open_view": "list",
        "open_live_synced": True,
    })
    out = restore_snapshot(polluted)
    assert out["cut_height"] == 2.8
    assert out["meters"] == 8.4
    for k in ("list_cut_height_pin", "list_meters_pin", "open_bay_flat", "open_view", "open_live_synced"):
        assert k not in out


def test_non_bay_snapshot_passes_through():
    flat = {"bay_enabled": False, "bay_depth": 0.0, "cut_height": 2.0, "meters": 4.0, "panels": 2}
    assert detail_view_bay(flat, DIMS, live_depth=0.9) == flat
