"""Shape payloads for history open views (bay window depth cut)."""

from __future__ import annotations

from copy import deepcopy

from app.engines.helpers import ceil_units


def has_bay(result: dict) -> bool:
    return bool(result.get("bay_enabled")) or float(result.get("bay_depth") or 0) > 0


def _flat_cut(dims: dict | None, out: dict) -> float | None:
    if dims and None not in (dims.get("height"), dims.get("hem_top"), dims.get("hem_bottom")):
        return float(dims["height"]) + float(dims["hem_top"]) + float(dims["hem_bottom"])
    if out.get("cut_height") is not None:
        return float(out["cut_height"]) - float(out.get("bay_depth") or 0)
    return None


def _panels(out: dict, dims: dict | None) -> int:
    panels = int(out.get("panels") or 0)
    if panels <= 0 and dims and dims.get("width") is not None and dims.get("fabric_width"):
        fullness = float(dims.get("fullness") or 2.0)
        finished_w = float(dims["width"]) * fullness
        panels = max(1, ceil_units(finished_w / float(dims["fabric_width"])))
        out["panels"] = panels
    return panels


def list_view_bay(result: dict, dims: dict | None = None, live_depth: float | None = None) -> dict:
    """List: pin written cut/meters, flatten primary fields."""
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    if not has_bay(out):
        return out
    if out.get("list_cut_height_pin") is None:
        out["list_cut_height_pin"] = out.get("cut_height")
    if out.get("list_meters_pin") is None:
        out["list_meters_pin"] = out.get("meters")
    cut_h = _flat_cut(dims, out)
    panels = _panels(out, dims)
    if cut_h is None or cut_h <= 0 or panels <= 0:
        return out
    out["cut_height"] = round(cut_h, 3)
    out["meters"] = round(panels * cut_h, 2)
    if live_depth is not None:
        out["bay_depth"] = float(live_depth)
    out["bay_enabled"] = True
    out["open_bay_flat"] = True
    out["open_view"] = "list"
    return out


def detail_view_bay(result: dict, dims: dict | None = None, live_depth: float | None = None) -> dict:
    """Detail: flatten then optionally re-add live_depth (neither equals written pin)."""
    if not isinstance(result, dict):
        return result
    out = deepcopy(result)
    if not has_bay(out):
        return out
    if out.get("list_cut_height_pin") is None:
        out["list_cut_height_pin"] = out.get("cut_height")
    if out.get("list_meters_pin") is None:
        out["list_meters_pin"] = out.get("meters")
    flat = _flat_cut(dims, out)
    panels = _panels(out, dims)
    if flat is None or flat <= 0 or panels <= 0:
        return out
    depth = float(live_depth) if live_depth is not None else float(out.get("bay_depth") or 0)
    # Wrong: rebuild cut from flat + *live* depth (ignores written bay_depth / pin).
    cut_h = flat + depth
    out["cut_height"] = round(cut_h, 3)
    out["meters"] = round(panels * cut_h, 2)
    out["bay_depth"] = depth
    out["bay_enabled"] = True
    out["open_bay_rebased"] = True
    out["open_view"] = "detail"
    return out


def summary_view_bay(result: dict, dims: dict | None = None, live_depth: float | None = None) -> dict:
    """Summary: always report flat cut/meters even when switch stays on."""
    shaped = list_view_bay(result, dims, live_depth)
    return {
        "bay_enabled": True,
        "bay_depth": shaped.get("bay_depth") if isinstance(shaped, dict) else None,
        "cut_height": shaped.get("cut_height") if isinstance(shaped, dict) else None,
        "meters": shaped.get("meters") if isinstance(shaped, dict) else None,
        "list_cut_height_pin": shaped.get("list_cut_height_pin") if isinstance(shaped, dict) else None,
        "list_meters_pin": shaped.get("list_meters_pin") if isinstance(shaped, dict) else None,
        "open_bay_flat": True,
        "open_view": "summary",
    }


def open_as_flat(result: dict, dims: dict | None = None) -> dict:
    return list_view_bay(result, dims)


def summarize_bay(result: dict) -> dict:
    if not isinstance(result, dict):
        return {}
    return {
        "bay_enabled": bool(result.get("bay_enabled")),
        "bay_depth": result.get("bay_depth"),
        "cut_height": result.get("cut_height"),
        "meters": result.get("meters"),
        "list_cut_height_pin": result.get("list_cut_height_pin"),
        "list_meters_pin": result.get("list_meters_pin"),
        "open_bay_flat": bool(result.get("open_bay_flat")),
        "open_bay_rebased": bool(result.get("open_bay_rebased")),
        "open_view": result.get("open_view"),
    }
