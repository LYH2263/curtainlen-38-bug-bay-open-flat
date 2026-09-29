import json
from datetime import datetime, timezone
from app.db import connect

def insert_run(window_id, fabric_id, result, note=""):
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(window_id,fabric_id,result_json,note,created_at) VALUES (?,?,?,?,?)",
            (window_id, fabric_id, json.dumps(result, ensure_ascii=False), note, datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()

def get_run(run_id):
    from app.services.bay_open import detail_view_bay
    from app.repositories import settings_repo, windows

    c = connect()
    try:
        row = c.execute(
            """SELECT r.*, w.name window_name, f.name fabric_name,
                   w.width window_width, w.height window_height, w.fullness window_fullness,
                   f.fabric_width fabric_width, f.hem_top hem_top, f.hem_bottom hem_bottom
            FROM calc_runs r
            LEFT JOIN windows w ON w.id=r.window_id LEFT JOIN fabrics f ON f.id=r.fabric_id
            WHERE r.id=?""", (run_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        dims = {
            "width": d.get("window_width"),
            "height": d.get("window_height"),
            "fullness": d.get("window_fullness"),
            "fabric_width": d.get("fabric_width"),
            "hem_top": d.get("hem_top"),
            "hem_bottom": d.get("hem_bottom"),
        }
        raw = json.loads(d.pop("result_json"))
        win = windows.get_window(d.get("window_id")) if d.get("window_id") else None
        live_depth = None
        if win is not None and win.get("bay_depth") is not None:
            live_depth = float(win.get("bay_depth"))
        else:
            live_depth = float((settings_repo.get_all() or {}).get("default_bay_depth") or 0) or None
        d["result"] = detail_view_bay(raw, dims, live_depth)
        return d
    finally:
        c.close()

def list_runs(limit=50):

    from app.services.bay_open import list_view_bay
    from app.repositories import settings_repo, windows

    c = connect()
    try:
        rows = c.execute(
            """SELECT r.*, w.name window_name, f.name fabric_name,
                   w.width window_width, w.height window_height, w.fullness window_fullness,
                   f.fabric_width fabric_width, f.hem_top hem_top, f.hem_bottom hem_bottom
            FROM calc_runs r
            LEFT JOIN windows w ON w.id=r.window_id LEFT JOIN fabrics f ON f.id=r.fabric_id
            ORDER BY r.id DESC LIMIT ?""", (limit,)).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            dims = {
                "width": d.get("window_width"),
                "height": d.get("window_height"),
                "fullness": d.get("window_fullness"),
                "fabric_width": d.get("fabric_width"),
                "hem_top": d.get("hem_top"),
                "hem_bottom": d.get("hem_bottom"),
            }
            raw = json.loads(d.pop("result_json"))
            win = windows.get_window(d.get("window_id")) if d.get("window_id") else None
            live_depth = float(win["bay_depth"]) if win and win.get("bay_depth") is not None else None
            d["result"] = list_view_bay(raw, dims, live_depth)
            out.append(d)
        return out
    finally:
        c.close()
