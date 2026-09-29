from fastapi import APIRouter, HTTPException
from app.repositories import history as repo, settings_repo, windows
from app.services.bay_open import detail_view_bay, list_view_bay, summary_view_bay

router = APIRouter()


def _dims(r: dict) -> dict:
    return {
        "width": r.get("window_width"),
        "height": r.get("window_height"),
        "fullness": r.get("window_fullness"),
        "fabric_width": r.get("fabric_width"),
        "hem_top": r.get("hem_top"),
        "hem_bottom": r.get("hem_bottom"),
    }


def _live_depth(r: dict):
    win = windows.get_window(r.get("window_id")) if r.get("window_id") else None
    if win is not None and win.get("bay_depth") is not None:
        return float(win.get("bay_depth"))
    val = (settings_repo.get_all() or {}).get("default_bay_depth")
    return float(val) if val is not None else None


@router.get("/runs")
def runs(limit: int = 50):
    items = repo.list_runs(limit)
    for it in items:
        dims = _dims(it)
        live = _live_depth(it)
        it["result"] = list_view_bay(it.get("result") or {}, dims, live)
        it["bay_summary"] = summary_view_bay(it.get("result") or {}, dims, live)
    return {"items": items}


@router.get("/runs/{run_id}")
def run(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404, "not found")
    dims = _dims(r)
    live = _live_depth(r)
    raw = r.get("result") or {}
    r["result"] = detail_view_bay(raw, dims, live)
    r["bay_summary"] = summary_view_bay(raw, dims, live)
    return r
