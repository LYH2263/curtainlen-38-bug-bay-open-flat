from fastapi import HTTPException
from app.engines.curtain_math import fabric_meters
from app.repositories import fabrics, history, settings_repo, windows

def run_estimate(window_id: int, fabric_id: int, save: bool, note: str):
    w = windows.get_window(window_id)
    f = fabrics.get_fabric(fabric_id)
    if not w or not f:
        raise HTTPException(404, "not found")
    if w.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty window")
    settings = settings_repo.get_all()
    fullness = float(w.get("fullness") or settings.get("default_fullness", 2.0))
    bay_enabled = bool(w.get("bay_enabled"))
    bay_depth = 0.0
    if bay_enabled:
        raw = w.get("bay_depth")
        bay_depth = float(raw) if raw is not None else float(settings.get("default_bay_depth") or 0)
        if bay_depth <= 0:
            raise HTTPException(422, "bay depth must be positive when bay window is enabled")
    calc = fabric_meters(w["width"], w["height"], fullness, f["hem_top"], f["hem_bottom"], f["fabric_width"], bay_depth=bay_depth)
    calc["bay_enabled"] = bay_enabled
    run_id = history.insert_run(window_id, fabric_id, calc, note) if save else None
    return {"window": w, "fabric": f, "run_id": run_id, **calc}
