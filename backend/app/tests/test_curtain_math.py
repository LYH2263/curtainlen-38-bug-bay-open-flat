from app.engines.curtain_math import fabric_meters

def test_living_room():
    r = fabric_meters(3.0, 2.6, 2.0, 0.10, 0.15, 1.4)
    assert r["panels"] == 5
    assert r["cut_height"] == 2.85
    assert r["meters"] == 14.25

def test_single_panel_narrow():
    r = fabric_meters(1.0, 2.0, 1.5, 0.0, 0.0, 2.8)
    assert r["panels"] == 1
    assert r["meters"] == 2.0

def test_bay_depth_extends_cut_height():
    r = fabric_meters(3.0, 2.6, 2.0, 0.10, 0.15, 1.4, bay_depth=0.4)
    assert r["panels"] == 5
    assert r["cut_height"] == 3.25
    assert r["meters"] == 16.25
    assert r["bay_depth"] == 0.4

def test_bay_depth_defaults_to_zero():
    r = fabric_meters(3.0, 2.6, 2.0, 0.10, 0.15, 1.4)
    assert r["bay_depth"] == 0.0
    assert r["cut_height"] == 2.85
