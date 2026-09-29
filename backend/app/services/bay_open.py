"""Open views for saved runs: the persisted snapshot is the single source of truth.

历史单的裁高与米数在写入那一刻即冻结。此后无论窗户飘窗开关、窗户登记进深，
还是设置侧默认进深口径如何变化，列表摘要、详情主字段、飘窗摘要三路都必须回显
同一份落库快照：飘窗开关可以仍为开启，裁高不得退回未加进深的口径，米数不得
跟着掉。任何一路都不得按"现行进深"重算，更不得把重算结果写回 calc_runs。
"""

from __future__ import annotations

from copy import deepcopy

# 旧版本 live sync 留在脏行上的整形/回写标记，恢复快照后一并清掉。
_STALE_KEYS = (
    "list_cut_height_pin",
    "list_meters_pin",
    "open_bay_flat",
    "open_bay_rebased",
    "open_view",
    "open_live_synced",
)


def has_bay(result: dict) -> bool:
    return bool(result.get("bay_enabled")) or float(result.get("bay_depth") or 0) > 0


def restore_snapshot(result: dict) -> dict:
    """Return the written snapshot as-is.

    旧版本曾把飘窗单裁高拍平 / 用现行进深重加后回写 result_json；当时的写入真值
    保存在 pin 字段里，这里仅在读取时把被污染的主字段复位为 pin，不触碰数据库。
    """
    out = deepcopy(result)
    if not has_bay(out):
        # 非飘窗行不带旧整形标记，原样回显即可。
        return out
    pinned_cut = out.get("list_cut_height_pin")
    pinned_meters = out.get("list_meters_pin")
    if pinned_cut is not None:
        out["cut_height"] = pinned_cut
    if pinned_meters is not None:
        out["meters"] = pinned_meters
    for k in _STALE_KEYS:
        out.pop(k, None)
    return out


def list_view_bay(result: dict, dims: dict | None = None, live_depth: float | None = None) -> dict:
    """列表摘要：回显写入快照（dims/live_depth 仅为兼容旧签名，一律忽略）。"""
    if not isinstance(result, dict):
        return result
    return restore_snapshot(result)


def detail_view_bay(result: dict, dims: dict | None = None, live_depth: float | None = None) -> dict:
    """详情主字段：与列表同一份写入快照，绝不按现行进深 rebases。"""
    if not isinstance(result, dict):
        return result
    return restore_snapshot(result)


def summary_view_bay(result: dict, dims: dict | None = None, live_depth: float | None = None) -> dict:
    """飘窗摘要：进深与裁高分列，裁高/米数等于写入快照。"""
    if not isinstance(result, dict):
        return {}
    snap = restore_snapshot(result)
    return {
        "bay_enabled": bool(snap.get("bay_enabled")),
        "bay_depth": snap.get("bay_depth") or 0.0,
        "cut_height": snap.get("cut_height"),
        "meters": snap.get("meters"),
    }


def open_as_flat(result: dict, dims: dict | None = None) -> dict:
    if not isinstance(result, dict):
        return result
    return restore_snapshot(result)


def summarize_bay(result: dict) -> dict:
    if not isinstance(result, dict):
        return {}
    return {
        "bay_enabled": bool(result.get("bay_enabled")),
        "bay_depth": result.get("bay_depth"),
        "cut_height": result.get("cut_height"),
        "meters": result.get("meters"),
    }
