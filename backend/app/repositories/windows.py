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
    c = connect()
    try:
        cur = c.execute(
            "UPDATE windows SET bay_enabled=?, bay_depth=? WHERE id=?",
            (1 if bay_enabled else 0, bay_depth, wid),
        )
        c.commit()
        # 只改窗户自身的飘窗口径，仅作用于此后新算的单；绝不回写已保存的历史快照。
        return cur.rowcount > 0
    finally:
        c.close()
