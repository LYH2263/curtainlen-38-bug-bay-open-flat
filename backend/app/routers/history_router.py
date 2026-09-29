from fastapi import APIRouter, HTTPException
from app.repositories import history as repo
from app.services.bay_open import detail_view_bay, list_view_bay, summary_view_bay

router = APIRouter()


@router.get("/runs")
def runs(limit: int = 50):
    items = repo.list_runs(limit)
    for it in items:
        raw = it.get("result") or {}
        it["result"] = list_view_bay(raw)
        it["bay_summary"] = summary_view_bay(raw)
    return {"items": items}


@router.get("/runs/{run_id}")
def run(run_id: int):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(404, "not found")
    raw = r.get("result") or {}
    r["result"] = detail_view_bay(raw)
    r["bay_summary"] = summary_view_bay(raw)
    return r
