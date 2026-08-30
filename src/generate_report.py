"""
Generates REPORT.html: a single, self-contained, offline static file from
logs/audit_log.jsonl - no server, no framework, no CDN dependency, matching
this project's own "no live UI" scope decision (BUILD_LOG.md §8) while
still being watchable in 10 seconds on camera instead of scrolled through
as raw JSONL. Re-run any time after a batch run to refresh it.

Usage: python generate_report.py
"""

import html
import json
from pathlib import Path

AUDIT_PATH = Path(__file__).parent.parent / "logs" / "audit_log.jsonl"
REPORT_PATH = Path(__file__).parent.parent / "REPORT.html"


def _load_events() -> list[dict]:
    if not AUDIT_PATH.exists():
        raise SystemExit(f"No audit log found at {AUDIT_PATH}. Run agent.py first.")
    with AUDIT_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _bar(label: str, value: int, max_value: int, color: str) -> str:
    pct = (value / max_value * 100) if max_value else 0
    # decline_code/final_action are a small fixed enum today, but this is
    # a cheap, zero-downside defense-in-depth escape regardless - HTML is
    # built by string interpolation here, not a templating engine with
    # auto-escaping, so nothing else protects against a value containing
    # HTML-special characters if that ever changes.
    safe_label = html.escape(str(label))
    return (
        f'<div class="bar-row">'
        f'<span class="bar-label">{safe_label}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
        f'<span class="bar-value">{value}</span>'
        f"</div>"
    )


def build_report():
    events = _load_events()
    gate_decisions = [e for e in events if e["event_type"] == "gate_decision"]

    if not gate_decisions:
        REPORT_PATH.write_text(
            "<title>Report</title><p>No gate_decision events in the audit log yet. Run agent.py first.</p>",
            encoding="utf-8",
        )
        print(f"Wrote {REPORT_PATH} (empty - no gate_decision events yet)")
        return

    total = len(gate_decisions)
    matched = sum(1 for d in gate_decisions if d["llm_matched_policy"])
    mismatched = total - matched

    by_code: dict[str, dict] = {}
    for d in gate_decisions:
        c = by_code.setdefault(d["decline_code"], {"total": 0, "matched": 0})
        c["total"] += 1
        if d["llm_matched_policy"]:
            c["matched"] += 1

    final_action_counts: dict[str, int] = {}
    for d in gate_decisions:
        final_action_counts[d["final_action"]] = final_action_counts.get(d["final_action"], 0) + 1

    max_code_total = max(c["total"] for c in by_code.values())
    max_action_count = max(final_action_counts.values())

    code_rows = ""
    for code, c in sorted(by_code.items(), key=lambda kv: -kv[1]["total"]):
        rate = c["matched"] / c["total"] * 100
        color = "#2ea043" if rate >= 70 else "#d29922" if rate >= 40 else "#f85149"
        safe_code = html.escape(str(code))
        code_rows += (
            f'<tr data-code="{safe_code}">'
            f"<td>{safe_code}</td><td>{c['total']}</td><td>{c['matched']}</td>"
            f"<td>{c['total'] - c['matched']}</td>"
            f'<td><span class="pill" style="background:{color}22;color:{color}">{rate:.0f}%</span></td>'
            f"</tr>"
        )

    action_bars = "".join(
        _bar(action, count, max_action_count, "#58a6ff")
        for action, count in sorted(final_action_counts.items(), key=lambda kv: -kv[1])
    )
    code_bars = "".join(
        _bar(code, c["total"], max_code_total, "#8957e5")
        for code, c in sorted(by_code.items(), key=lambda kv: -kv[1]["total"])
    )

    page_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Subscription Recovery Agent - Report</title>
<style>
  body {{ font: 14px/1.5 -apple-system, Segoe UI, sans-serif; background:#0d1117; color:#c9d1d9; margin:0; padding:32px; }}
  h1 {{ font-size:20px; color:#f0f6fc; margin-bottom:4px; }}
  .sub {{ color:#8b949e; margin-bottom:24px; }}
  .stats {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:32px; }}
  .stat {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px 20px; min-width:150px; }}
  .stat .n {{ font-size:26px; font-weight:600; color:#f0f6fc; }}
  .stat .l {{ color:#8b949e; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
  h2 {{ font-size:15px; color:#f0f6fc; margin:32px 0 12px; border-bottom:1px solid #30363d; padding-bottom:6px; }}
  .bar-row {{ display:flex; align-items:center; gap:10px; margin:6px 0; }}
  .bar-label {{ width:220px; flex-shrink:0; color:#c9d1d9; font-size:13px; }}
  .bar-track {{ flex:1; background:#161b22; border-radius:4px; height:16px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:4px; }}
  .bar-value {{ width:36px; text-align:right; color:#8b949e; font-size:12px; }}
  table {{ border-collapse:collapse; width:100%; margin-top:8px; }}
  th, td {{ text-align:left; padding:8px 12px; border-bottom:1px solid #21262d; font-size:13px; }}
  th {{ color:#8b949e; font-weight:500; text-transform:uppercase; font-size:11px; letter-spacing:.04em; }}
  .pill {{ padding:2px 8px; border-radius:10px; font-weight:600; font-size:12px; }}
  input#filter {{ background:#161b22; border:1px solid #30363d; color:#c9d1d9; padding:6px 10px; border-radius:6px; width:260px; margin-bottom:8px; }}
  .note {{ color:#8b949e; font-size:12px; margin-top:24px; }}
</style></head>
<body>
<h1>Subscription Recovery Agent — Audit Report</h1>
<div class="sub">Generated directly from logs/audit_log.jsonl. No AI, no server, no external service involved in this page.</div>

<div class="stats">
  <div class="stat"><div class="n">{total}</div><div class="l">Decisions</div></div>
  <div class="stat"><div class="n">{matched}</div><div class="l">LLM matched policy</div></div>
  <div class="stat"><div class="n">{mismatched}</div><div class="l">Gate overrode LLM</div></div>
  <div class="stat"><div class="n">{mismatched/total*100:.0f}%</div><div class="l">Override rate</div></div>
</div>

<h2>Final action distribution (after the gate)</h2>
{action_bars}

<h2>Volume by decline code</h2>
{code_bars}

<h2>LLM proposal accuracy by decline code</h2>
<input id="filter" placeholder="Filter by decline code...">
<table id="codeTable">
<thead><tr><th>Decline code</th><th>Total</th><th>Matched</th><th>Mismatched</th><th>Match rate</th></tr></thead>
<tbody>
{code_rows}
</tbody>
</table>

<div class="note">
  "Matched policy" = the LLM's raw proposal, before the gate touched it, was
  identical to the one action config/decline_policy.json assigns that code.
  A low match rate is not a hidden problem - it is exactly what the gate
  exists to catch; see METRICS.md for the full breakdown and the two
  systematic biases behind it.
</div>

<script>
  document.getElementById('filter').addEventListener('input', function(e) {{
    var q = e.target.value.toLowerCase();
    document.querySelectorAll('#codeTable tbody tr').forEach(function(row) {{
      row.style.display = row.dataset.code.toLowerCase().includes(q) ? '' : 'none';
    }});
  }});
</script>
</body></html>
"""
    REPORT_PATH.write_text(page_html, encoding="utf-8")
    print(f"Wrote {REPORT_PATH} ({total} gate decisions as of this generation)")


if __name__ == "__main__":
    build_report()
