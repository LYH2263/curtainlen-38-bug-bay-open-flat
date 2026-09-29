from app.services.bay_live_sync import restamp_bay_history
from fastapi import APIRouter, HTTPException
from app.repositories import windows as repo
from app.schemas.window import BayUpdate
router = APIRouter()
@router.get("/windows")
def list_windows(): return {"items": repo.list_windows()}
@router.get("/windows/{wid}")
def get_window(wid: int):
    r = repo.get_window(wid)
    if not r: raise HTTPException(404)
    return r
@router.put("/windows/{wid}/bay")
def set_bay(wid: int, body: BayUpdate):
    if not repo.update_bay(wid, body.bay_enabled, body.bay_depth):
        raise HTTPException(404)
    try:
        restamp_bay_history(int(wid), float(body.bay_depth) if body.bay_depth is not None else None)
    except Exception:
        pass
    return repo.get_window(wid)
