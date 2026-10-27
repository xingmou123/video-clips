"""Validate video snapshots. No data fetching, identity matching, or causal ranking.

Percent values use 0..100. Timestamps must include a UTC offset.
Missing values remain None. See assets/snapshot.template.json.
"""
import argparse
from datetime import datetime
import itertools
import json
import math
from pathlib import Path

UNITS = {
    "views": "count", "bounce_2s_pct": "percent",
    "retention_3s_pct": "percent", "retention_5s_pct": "percent",
    "avg_watch_seconds": "seconds", "completion_pct": "percent",
}
LEADS = ("confirmed_wechat", "qualified_wechat", "qualified_consultations", "paid_enrollments")


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def stamp(value, field, errors):
    if value is None:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("timezone missing")
        return result
    except (ValueError, AttributeError, TypeError):
        errors.append(f"{field}: use ISO timestamp with timezone")
        return None


def review_one(row):
    if not isinstance(row, dict):
        return {"errors": ["snapshot must be an object"], "warnings": [], "valid": False}
    errors, warnings = [], []
    for key in ("work_id", "account"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            errors.append(f"{key}: non-empty string required")
    pub = stamp(row.get("published_at"), "published_at", errors)
    cap = stamp(row.get("captured_at"), "captured_at", errors)
    cutoff = stamp(row.get("data_as_of"), "data_as_of", errors)
    if pub and cap and cap < pub:
        errors.append("capture precedes publication")
    if cutoff and cap and cutoff > cap:
        errors.append("data cutoff is later than capture")
    if cutoff and pub and cutoff < pub:
        errors.append("data cutoff precedes publication")
    age = (cap - pub).total_seconds() / 3600 if cap and pub else None
    metric_age = (cutoff - pub).total_seconds() / 3600 if cutoff and pub else None
    if cutoff is None:
        warnings.append("data cutoff unknown; capture age is not necessarily metric age")
    duration = row.get("duration_seconds")
    if duration is not None and (not number(duration) or duration <= 0):
        errors.append("duration_seconds must be positive or null")
        duration = None
    metrics = row.get("metrics") or {}
    if not isinstance(metrics, dict):
        errors.append("metrics must be an object")
        metrics = {}
    values = {}
    for key, unit in UNITS.items():
        item = metrics.get(key) or {}
        if not isinstance(item, dict):
            errors.append(f"{key}: metric must be an object")
            values[key] = None
            continue
        value = item.get("value")
        values[key] = value
        if value is None:
            continue
        valid = number(value) and value >= 0 and (unit != "percent" or value <= 100)
        if not valid:
            errors.append(f"{key}: invalid numeric value")
            values[key] = None
            continue
        if item.get("unit") != unit:
            errors.append(f"{key}: expected unit {unit}")
        if not item.get("raw_name") or not item.get("source"):
            errors.append(f"{key}: raw_name and source required for observed value")
        if key == "views" and item.get("exact") is True and int(value) != value:
            errors.append("exact views must be an integer")
    leads = row.get("leads") or {}
    attr = row.get("attribution") or {}
    if not isinstance(leads, dict) or not isinstance(attr, dict):
        errors.append("leads and attribution must be objects")
        leads, attr = {}, {}
    counts = {}
    for key in LEADS:
        value = leads.get(key)
        if value is not None and (not number(value) or value < 0 or int(value) != value):
            errors.append(f"{key}: nonnegative integer or null required")
            value = None
        counts[key] = value
    if any(value is not None for value in counts.values()) and not leads.get("source"):
        errors.append("lead counts need a source")
    if attr.get("same_cohort") is True:
        # A buyer need not have a recorded consultation. Both are subsets of
        # the qualified cohort, not necessarily subsets of each other.
        for a, b in ((LEADS[0], LEADS[1]), (LEADS[1], LEADS[2]), (LEADS[1], LEADS[3])):
            if counts[a] is not None and counts[b] is not None and counts[b] > counts[a]:
                errors.append(f"same-cohort funnel inversion: {b} > {a}")
    avg = values.get("avg_watch_seconds")
    avg_pct = avg / duration * 100 if avg is not None and duration else None
    views = values.get("views")
    qualified = counts["qualified_wechat"]
    known = attr.get("basis") == "confirmed_work" and attr.get("coverage") == "complete"
    aligned = known and attr.get("same_cohort") is True and attr.get("view_window_aligned") is True
    exact = isinstance(metrics.get("views"), dict) and metrics["views"].get("exact") is True
    yield_rate = qualified / views * 1000 if aligned and exact and views and qualified is not None else None
    if yield_rate is None:
        warnings.append("lead yield unavailable: need confirmed complete attribution, aligned window, same cohort and exact nonzero views")
    if attr.get("window_mature") is not True:
        warnings.append("lead observation window not confirmed mature")
    if row.get("traffic_basis") in (None, "unknown"):
        warnings.append("traffic basis unknown")
    # Invalid input never produces a trustworthy derived result.
    derived = {
        "avg_watch_pct_derived": round(avg_pct, 4) if avg_pct is not None and not errors else None,
        "qualified_wechat_per_1000_views": round(yield_rate, 4) if yield_rate is not None and not errors else None,
    }
    return {
        "work_id": row.get("work_id"), "account": row.get("account"),
        "capture_age_hours": round(age, 4) if age is not None else None,
        "metric_age_hours": round(metric_age, 4) if metric_age is not None else None,
        "observed_metrics": values,
        "metric_context": {key: {field: item.get(field) for field in
            ("raw_name", "unit", "exact", "source", "data_as_of")}
            for key, item in metrics.items() if isinstance(item, dict)},
        "published_at": row.get("published_at"), "captured_at": row.get("captured_at"),
        "data_as_of": row.get("data_as_of"), "capture_note": row.get("capture_note"),
        "duration_seconds": duration, "method_version": row.get("method_version"),
        "lead_counts": counts, "derived": derived,
        "valid": not errors, "errors": errors, "warnings": warnings,
    }


def review(data, age_tolerance_hours=1.0):
    rows = data if isinstance(data, list) else [data]
    if not rows:
        return {"snapshots": [], "comparisons": [], "valid": False,
                "errors": ["no snapshots supplied; no observation has been validated"]}
    reports = [review_one(row) for row in rows]
    pairs = []
    for (i, a), (j, b) in itertools.combinations(enumerate(rows), 2):
        if not isinstance(a, dict) or not isinstance(b, dict):
            continue
        ra, rb = reports[i], reports[j]
        barriers = []
        if not ra["valid"] or not rb["valid"]:
            barriers.append("invalid input")
        for key in ("account", "content_type", "traffic_basis", "measurement_scope"):
            if not a.get(key) or not b.get(key) or a.get(key) == "unknown" or b.get(key) == "unknown" or a[key] != b[key]:
                barriers.append(f"{key} differs or unknown")
        aa, ba = ra.get("metric_age_hours"), rb.get("metric_age_hours")
        if aa is None or ba is None or abs(aa - ba) > age_tolerance_hours:
            barriers.append("metric ages differ or unknown")
        pairs.append({
            "a": a.get("work_id"), "b": b.get("work_id"),
            "basic_comparison_barriers": barriers,
            "interpretation": "Descriptive only; manually check topic, audience, duration and metric definitions. Not a causal test or winner ranking.",
        })
    return {"snapshots": reports, "comparisons": pairs, "valid": all(r["valid"] for r in reports)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--age-tolerance-hours", type=float, default=1.0)
    args = parser.parse_args()
    if args.age_tolerance_hours < 0 or not math.isfinite(args.age_tolerance_hours):
        parser.error("age tolerance must be finite and nonnegative")
    try:
        result = review(json.loads(args.input.read_text(encoding="utf-8-sig")), args.age_tolerance_hours)
    except (OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{len(result['snapshots'])} snapshots; valid={result['valid']}; output={args.output}")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
