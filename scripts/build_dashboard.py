"""
Build the interactive dashboard (docs/index.html) from the CRM data.

Reads data/*.csv, packs opportunity-level rows into compact JSON and injects it into
dashboard/template.html. The page recomputes every KPI and chart in the browser when
the region / team / year filters change, the same way a Power BI report slices a model.

Usage:  python scripts/build_dashboard.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
read = lambda name: pd.read_csv(DATA / f"{name}.csv", keep_default_na=False, na_values=[""])

users, opps, hist, leads = read("users"), read("opportunities"), read("opportunity_history"), read("leads")

STAGES = ["Prospecting", "Qualification", "Needs Analysis", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
FUNNEL_ORDER = {s: i for i, s in enumerate(STAGES[:6])}
sources = sorted(opps.lead_source.unique())
types = sorted(opps.type.unique())
reasons = sorted(opps.loss_reason.dropna().unique())
rep_index = {u: i for i, u in enumerate(users.user_id)}

# furthest funnel stage each deal reached (0 = Prospecting ... 5 = Closed Won)
hist["n"] = hist.stage.map(FUNNEL_ORDER)
max_reached = hist.dropna(subset=["n"]).groupby("opportunity_id").n.max().astype(int)

rows = []
for o in opps.itertuples():
    cycle = (pd.Timestamp(o.close_date) - pd.Timestamp(o.created_date)).days
    rows.append([
        rep_index[o.owner_id], sources.index(o.lead_source), types.index(o.type),
        STAGES.index(o.stage), 0 if pd.isna(o.amount) else int(o.amount),
        o.created_date[:7], o.close_date[:7], int(o.is_closed), int(o.is_won), cycle,
        int(max_reached.get(o.opportunity_id, 0)),
        reasons.index(o.loss_reason) if isinstance(o.loss_reason, str) else -1,
    ])

# leads aggregated by owner region / team / created year / source -> [leads, converted]
lu = leads.merge(users[["user_id", "region", "team"]], left_on="owner_id", right_on="user_id")
lu["year"] = lu.created_date.str[:4]
lead_agg = {}
for (r, t, y, s), g in lu.groupby(["region", "team", "year", "lead_source"]):
    lead_agg[f"{r}|{t}|{y}|{s}"] = [len(g), int((g.status == "Converted").sum())]

# data-quality counts, same rules as sql/12_crm_data_quality.sql
acts = read("activities")
recent = set(acts[acts.activity_date >= "2026-08-31"].opportunity_id)
last_stage = hist.sort_values("entered_date").groupby("opportunity_id").stage.last()
open_opps = opps[opps.is_closed == 0]
dq = {
    "missingAmount": int(opps.amount.isna().sum()),
    "pastClose": int((open_opps.close_date < "2026-09-30").sum()),
    "stageMismatch": int((opps.set_index("opportunity_id").stage != last_stage).sum()),
    "noActivity": int((~open_opps.opportunity_id.isin(recent)).sum()),
}

payload = {
    "reps": users[["rep_name", "region", "team", "quarterly_quota"]].values.tolist(),
    "sources": sources, "types": types, "stages": STAGES, "reasons": reasons,
    "rows": rows, "leads": lead_agg, "dq": dq, "snapshot": "2026-09-30",
}
template = (ROOT / "dashboard" / "template.html").read_text()
html = template.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
out = ROOT / "docs" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html)
print(f"wrote {out.relative_to(ROOT)} ({len(html) / 1024:.0f} KB, {len(rows)} opportunities)")
