"""When window bay fields change, restamp open history (incorrect live sync)."""

from __future__ import annotations

import json

from app.db import connect
from app.services.bay_open import detail_view_bay


def restamp_bay_history(window_id: int, live_depth: float | None, dims: dict | None = None) -> int:
    c = connect()
    try:
        rows = c.execute(
            "SELECT id, result_json FROM calc_runs WHERE window_id=? ORDER BY id DESC LIMIT 40",
            (window_id,),
        ).fetchall()
        n = 0
        for row in rows:
            raw = json.loads(row["result_json"] if isinstance(row, dict) else row[1])
            if not isinstance(raw, dict):
                continue
            if not (raw.get("bay_enabled") or float(raw.get("bay_depth") or 0) > 0):
                continue
            shaped = detail_view_bay(raw, dims, live_depth)
            shaped["open_live_synced"] = True
            rid = row["id"] if isinstance(row, dict) else row[0]
            c.execute(
                "UPDATE calc_runs SET result_json=? WHERE id=?",
                (json.dumps(shaped, ensure_ascii=False), rid),
            )
            n += 1
        c.commit()
        return n
    finally:
        c.close()
