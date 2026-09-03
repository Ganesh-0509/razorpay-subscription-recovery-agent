"""
Generates POLICY_DASHBOARD.html: a single, self-contained, offline static
page rendering config/decline_policy.json for a merchant - no server, no
framework, no CDN dependency, same architecture decision as
generate_report.py (BUILD_LOG.md §8, README.md §5): this project's static
pages must never depend on the internet being up during a demo.

This is a READ-ONLY view, on purpose. It exists to close a real gap found
during review: a merchant editing config/decline_policy.json by hand had no
way to know what an allowed_action like "payment_link_nudge" actually does
without opening a .py file - the opposite of the "no code, no redeploy"
pitch. This page answers that in plain English, with filters, straight from
the same file the gate actually enforces - nothing here is a separate copy
that could drift out of sync.

It is deliberately NOT an editable dashboard - see README.md's Known
Limitations for exactly why (no access control, no audit trail on policy
changes, matching real security concerns Razorpay's own docs raise for
anything that can change how money moves). Editing the policy still means
editing config/decline_policy.json directly, whose own git history is the
audit trail for who changed what and when.

Usage: python generate_policy_dashboard.py
"""

import html
import json
from pathlib import Path

POLICY_PATH = Path(__file__).parent.parent / "config" / "decline_policy.json"
DASHBOARD_PATH = Path(__file__).parent.parent / "POLICY_DASHBOARD.html"

SOURCE_COLORS = {
    "customer": "#58a6ff",
    "bank": "#d29922",
    "gateway": "#8957e5",
    "network": "#3fb950",
}

ACTION_COLORS = {
    "immediate_retry": "#3fb950",
    "delayed_retry": "#58a6ff",
    "payment_link_nudge": "#d29922",
    "no_action_fraud": "#f85149",
    "no_action_unrecoverable": "#8b949e",
}

ACTION_LABELS = {
    "immediate_retry": "Immediate retry",
    "delayed_retry": "Delayed retry",
    "payment_link_nudge": "Payment link nudge",
    "no_action_fraud": "No action — fraud",
    "no_action_unrecoverable": "No action — unrecoverable",
}


def _load_policy() -> tuple[dict, dict]:
    if not POLICY_PATH.exists():
        raise SystemExit(f"No policy file found at {POLICY_PATH}.")
    raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    glossary = raw.get("_action_glossary", {})
    codes = {k: v for k, v in raw.items() if not k.startswith("_")}
    return codes, glossary


def _bar(label: str, value: int, max_value: int, color: str) -> str:
    pct = (value / max_value * 100) if max_value else 0
    safe_label = html.escape(str(label))
    return (
        f'<div class="bar-row">'
        f'<span class="bar-label">{safe_label}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
        f'<span class="bar-value">{value}</span>'
        f"</div>"
    )


def _donut(counts: dict[str, int], colors: dict[str, str], total: int) -> str:
    # Pure-CSS conic-gradient donut - no chart library, no CDN, works
    # completely offline. Segments in a fixed, deterministic order so the
    # legend below always lines up with what's drawn.
    stops = []
    angle = 0.0
    for key, count in counts.items():
        if count == 0:
            continue
        span = count / total * 360
        color = colors.get(key, "#8b949e")
        stops.append(f"{color} {angle:.2f}deg {angle + span:.2f}deg")
        angle += span
    gradient = ", ".join(stops)
    return f'<div class="donut" style="background:conic-gradient({gradient})"></div>'


def build_dashboard():
    codes, glossary = _load_policy()
    if not codes:
        raise SystemExit(f"{POLICY_PATH} has no decline codes to render.")

    total = len(codes)

    by_source: dict[str, int] = {}
    by_action: dict[str, int] = {}
    for entry in codes.values():
        by_source[entry["source"]] = by_source.get(entry["source"], 0) + 1
        by_action[entry["allowed_action"]] = by_action.get(entry["allowed_action"], 0) + 1

    # Fixed action order everywhere (cards, donut, legend, filter pills) so
    # colors and labels always mean the same thing across the whole page.
    action_order = [a for a in ACTION_LABELS if a in by_action] + [
        a for a in by_action if a not in ACTION_LABELS
    ]
    ordered_by_action = {a: by_action[a] for a in action_order}

    max_source = max(by_source.values())
    source_bars = "".join(
        _bar(source.capitalize(), n, max_source, SOURCE_COLORS.get(source, "#8b949e"))
        for source, n in sorted(by_source.items(), key=lambda kv: -kv[1])
    )

    donut_html = _donut(ordered_by_action, ACTION_COLORS, total)
    legend_html = "".join(
        f'<div class="legend-row"><span class="swatch" style="background:{ACTION_COLORS.get(a, "#8b949e")}"></span>'
        f'<span>{html.escape(ACTION_LABELS.get(a, a))}</span><span class="legend-count">{n}</span></div>'
        for a, n in ordered_by_action.items()
    )

    cards_html = ""
    for code, entry in sorted(codes.items()):
        source = entry["source"]
        action = entry["allowed_action"]
        desc = html.escape(entry["description"])
        explanation = html.escape(glossary.get(action, "(no explanation on file for this action)"))
        action_label = html.escape(ACTION_LABELS.get(action, action))
        action_color = ACTION_COLORS.get(action, "#8b949e")
        source_color = SOURCE_COLORS.get(source, "#8b949e")
        rate = entry.get("simulated_success_rate", 0.0)
        safe_code = html.escape(code)
        cards_html += f"""
<div class="card" data-code="{safe_code}" data-source="{html.escape(source)}" data-action="{html.escape(action)}"
     data-search="{safe_code} {desc}">
  <div class="card-top">
    <code class="code-name">{safe_code}</code>
    <span class="pill" style="background:{source_color}22;color:{source_color}">{html.escape(source)}</span>
  </div>
  <div class="desc">{desc}</div>
  <div class="action-row">
    <span class="pill" style="background:{action_color}22;color:{action_color}">{action_label}</span>
  </div>
  <div class="explain">{explanation}</div>
  <div class="sim-note">Simulated success rate: {rate * 100:.0f}% <span class="sim-caveat">(test-data only, not a real guarantee — see note below)</span></div>
</div>"""

    source_pills = "".join(
        f'<button class="pill-btn" data-filter-source="{html.escape(s)}">{html.escape(s.capitalize())}</button>'
        for s in sorted(by_source)
    )
    action_pills = "".join(
        f'<button class="pill-btn" data-filter-action="{html.escape(a)}">{html.escape(ACTION_LABELS.get(a, a))}</button>'
        for a in action_order
    )

    page_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Recovery Policy - Merchant View</title>
<style>
  body {{ font: 14px/1.5 -apple-system, Segoe UI, sans-serif; background:#0d1117; color:#c9d1d9; margin:0; padding:32px; }}
  h1 {{ font-size:20px; color:#f0f6fc; margin-bottom:4px; }}
  .sub {{ color:#8b949e; margin-bottom:24px; max-width:760px; }}
  h2 {{ font-size:15px; color:#f0f6fc; margin:32px 0 12px; border-bottom:1px solid #30363d; padding-bottom:6px; }}
  .stats {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:8px; }}
  .stat {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px 20px; min-width:150px; }}
  .stat .n {{ font-size:26px; font-weight:600; color:#f0f6fc; }}
  .stat .l {{ color:#8b949e; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}

  .charts {{ display:flex; gap:32px; flex-wrap:wrap; align-items:flex-start; margin-top:16px; }}
  .chart-block {{ flex:1; min-width:280px; }}
  .bar-row {{ display:flex; align-items:center; gap:10px; margin:6px 0; }}
  .bar-label {{ width:110px; flex-shrink:0; color:#c9d1d9; font-size:13px; }}
  .bar-track {{ flex:1; background:#161b22; border-radius:4px; height:16px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:4px; }}
  .bar-value {{ width:28px; text-align:right; color:#8b949e; font-size:12px; }}

  .donut-wrap {{ display:flex; gap:24px; align-items:center; flex-wrap:wrap; }}
  .donut {{ width:140px; height:140px; border-radius:50%; flex-shrink:0;
            mask: radial-gradient(farthest-side, transparent calc(100% - 22px), #000 calc(100% - 22px));
            -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 22px), #000 calc(100% - 22px)); }}
  .legend-row {{ display:flex; align-items:center; gap:8px; font-size:13px; margin:4px 0; }}
  .swatch {{ width:10px; height:10px; border-radius:2px; flex-shrink:0; }}
  .legend-count {{ color:#8b949e; margin-left:auto; padding-left:12px; }}

  .controls {{ display:flex; gap:24px; flex-wrap:wrap; align-items:flex-start; margin:8px 0 20px; }}
  input#search {{ background:#161b22; border:1px solid #30363d; color:#c9d1d9; padding:6px 10px; border-radius:6px; width:260px; }}
  .filter-group {{ display:flex; flex-direction:column; gap:4px; }}
  .filter-group .label {{ color:#8b949e; font-size:11px; text-transform:uppercase; letter-spacing:.04em; }}
  .pill-row {{ display:flex; gap:6px; flex-wrap:wrap; }}
  .pill-btn {{ background:#161b22; border:1px solid #30363d; color:#c9d1d9; padding:4px 10px; border-radius:14px;
               font-size:12px; cursor:pointer; }}
  .pill-btn.active {{ background:#1f6feb; border-color:#1f6feb; color:#fff; }}

  .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:14px; margin-top:8px; }}
  .card {{ background:#161b22; border:1px solid #30363d; border-radius:10px; padding:14px 16px; }}
  .card-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
  .code-name {{ font-size:13px; color:#f0f6fc; }}
  .desc {{ color:#c9d1d9; font-size:13px; margin-bottom:10px; min-height:36px; }}
  .action-row {{ margin-bottom:8px; }}
  .pill {{ padding:2px 8px; border-radius:10px; font-weight:600; font-size:11px; }}
  .explain {{ color:#8b949e; font-size:12.5px; margin-bottom:10px; }}
  .sim-note {{ color:#6e7681; font-size:11px; border-top:1px solid #21262d; padding-top:8px; }}
  .sim-caveat {{ font-style:italic; }}
  .empty {{ color:#8b949e; padding:24px; text-align:center; display:none; }}
  .note {{ color:#8b949e; font-size:12px; margin-top:32px; max-width:760px; }}
  .note b {{ color:#c9d1d9; }}
</style></head>
<body>
<h1>Recovery Policy — Merchant View</h1>
<div class="sub">Generated directly from <code>config/decline_policy.json</code> — the exact live policy the gate
enforces, not a mockup or a separate copy. Read-only by design; see the note at the bottom for why.</div>

<div class="stats">
  <div class="stat"><div class="n">{total}</div><div class="l">Decline codes covered</div></div>
  <div class="stat"><div class="n">{len(by_source)}</div><div class="l">Failure sources</div></div>
  <div class="stat"><div class="n">{len(by_action)}</div><div class="l">Distinct actions used</div></div>
</div>

<div class="charts">
  <div class="chart-block">
    <h2>By who/what caused the failure</h2>
    {source_bars}
  </div>
  <div class="chart-block">
    <h2>By what the system does about it</h2>
    <div class="donut-wrap">
      {donut_html}
      <div>{legend_html}</div>
    </div>
  </div>
</div>

<h2>Every decline code, in plain English</h2>
<div class="controls">
  <div class="filter-group">
    <span class="label">Search</span>
    <input id="search" placeholder="Search code or description...">
  </div>
  <div class="filter-group">
    <span class="label">Source</span>
    <div class="pill-row" id="sourceFilters">
      <button class="pill-btn active" data-filter-source="all">All</button>
      {source_pills}
    </div>
  </div>
  <div class="filter-group">
    <span class="label">Action</span>
    <div class="pill-row" id="actionFilters">
      <button class="pill-btn active" data-filter-action="all">All</button>
      {action_pills}
    </div>
  </div>
</div>

<div class="grid" id="cardGrid">
{cards_html}
</div>
<div class="empty" id="emptyState">No decline codes match these filters.</div>

<div class="note">
  <b>Why this page is read-only, not an editable dashboard:</b> the policy below decides how real money-moving
  actions get triggered, so letting anyone change it through a web form needs real access control (who's allowed
  to edit) and an audit trail on the edit itself (who changed what, when) — neither of which this project has
  built. Changing the actual policy still means editing <code>config/decline_policy.json</code> directly; that
  file's own git history already serves as the audit trail for who changed what and when. See README.md's Known
  Limitations for the full reasoning.
</div>

<script>
  var search = document.getElementById('search');
  var sourceFilters = document.getElementById('sourceFilters');
  var actionFilters = document.getElementById('actionFilters');
  var cards = Array.prototype.slice.call(document.querySelectorAll('#cardGrid .card'));
  var empty = document.getElementById('emptyState');

  var state = {{ q: '', source: 'all', action: 'all' }};

  function applyFilters() {{
    var visible = 0;
    cards.forEach(function(card) {{
      var matchesSearch = !state.q || card.dataset.search.toLowerCase().includes(state.q);
      var matchesSource = state.source === 'all' || card.dataset.source === state.source;
      var matchesAction = state.action === 'all' || card.dataset.action === state.action;
      var show = matchesSearch && matchesSource && matchesAction;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    }});
    empty.style.display = visible === 0 ? 'block' : 'none';
  }}

  search.addEventListener('input', function(e) {{
    state.q = e.target.value.toLowerCase();
    applyFilters();
  }});

  function wirePillGroup(container, stateKey, datasetKey) {{
    container.addEventListener('click', function(e) {{
      var btn = e.target.closest('.pill-btn');
      if (!btn) return;
      container.querySelectorAll('.pill-btn').forEach(function(b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      state[stateKey] = btn.dataset[datasetKey];
      applyFilters();
    }});
  }}

  wirePillGroup(sourceFilters, 'source', 'filterSource');
  wirePillGroup(actionFilters, 'action', 'filterAction');
</script>
</body></html>
"""
    DASHBOARD_PATH.write_text(page_html, encoding="utf-8")
    print(f"Wrote {DASHBOARD_PATH} ({total} decline codes)")


if __name__ == "__main__":
    build_dashboard()
