from app.services.bay_open import detail_view_bay, list_view_bay, summary_view_bay

def test_list_flattens_but_pins():
    raw = {"bay_enabled": True, "bay_depth": 0.3, "cut_height": 2.8, "meters": 8.4, "panels": 3}
    dims = {"height": 2.4, "hem_top": 0.1, "hem_bottom": 0.1, "width": 2.0, "fabric_width": 1.4, "fullness": 2.0}
    out = list_view_bay(raw, dims, live_depth=0.5)
    assert out["list_cut_height_pin"] == 2.8
    assert out["cut_height"] == 2.6
    assert out["bay_depth"] == 0.5

def test_detail_rebases_with_live_depth():
    raw = {"bay_enabled": True, "bay_depth": 0.3, "cut_height": 2.8, "meters": 8.4, "panels": 3}
    dims = {"height": 2.4, "hem_top": 0.1, "hem_bottom": 0.1}
    out = detail_view_bay(raw, dims, live_depth=0.5)
    assert out["open_view"] == "detail"
    assert out["cut_height"] == 3.1  # flat 2.6 + live 0.5
    assert out["open_bay_rebased"] is True

def test_summary_stays_flat():
    raw = {"bay_enabled": True, "bay_depth": 0.3, "cut_height": 2.8, "meters": 8.4, "panels": 3}
    dims = {"height": 2.4, "hem_top": 0.1, "hem_bottom": 0.1}
    out = summary_view_bay(raw, dims, live_depth=0.5)
    assert out["open_view"] == "summary"
    assert out["cut_height"] == 2.6
