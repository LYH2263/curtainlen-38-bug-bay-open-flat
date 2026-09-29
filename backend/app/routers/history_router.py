from fastapi import APIRouter, HTTPException
from app.repositories import history as repo

router = APIRouter()


def bay_snapshot(result: dict) -> dict:
    """Project the persisted bay fields. Cut height already includes bay depth;
    the two fields are reported separately and never recomputed on read."""
    result = result or {}
    return {
        "bay_enabled": bool(result.get("bay_enabled")),
        "bay_depth": result.get("bay_depth"),
        "cut_height": result.get("cut_height"),
        "meters": result.get("meters"),
    }


@router.get("/runs")
def runs(limit: int = 50):
    items = repo.list_runs(limit)
    for it in items:
        it["bay_summary"] = bay_snapshot(it.get("result") or {})
    return {"items": items}


@router.get("/runs/{run_id}")
def run(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404, "not found")
    r["bay_summary"] = bay_snapshot(r.get("result") or {})
    return r
