from app.db import connect

def list_windows():
    c = connect()
    try:
        return [dict(r) for r in c.execute("SELECT * FROM windows ORDER BY id").fetchall()]
    finally:
        c.close()

def get_window(wid: int):
    c = connect()
    try:
        r = c.execute("SELECT * FROM windows WHERE id=?", (wid,)).fetchone()
        return dict(r) if r else None
    finally:
        c.close()

def update_bay(wid: int, bay_enabled: bool, bay_depth):
    # Window-side bay settings only constrain NEW estimates; saved calc runs are
    # immutable snapshots and must never be restamped here.
    c = connect()
    try:
        cur = c.execute(
            "UPDATE windows SET bay_enabled=?, bay_depth=? WHERE id=?",
            (1 if bay_enabled else 0, bay_depth, wid),
        )
        c.commit()
        return cur.rowcount > 0
    finally:
        c.close()
