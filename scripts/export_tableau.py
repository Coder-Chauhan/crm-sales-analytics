"""
Export Tableau-ready extracts to tableau/data/.

Tableau Public works best with a few flat, analysis-ready tables, so this script
pre-joins the CRM objects instead of making you model six tables:

  opportunities.csv          one row per deal, with rep, region, team, account and timing fields
  funnel.csv                 one row per deal per stage it reached (for the funnel chart)
  rep_quota_by_quarter.csv   one row per rep per quarter: quota and won revenue (attainment)
  lead_source_summary.csv    leads, conversions and won revenue by region / team / year / source
  data_quality.csv           CRM hygiene checks (same rules as sql/12_crm_data_quality.sql)

Usage:  python scripts/export_tableau.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "tableau" / "data"
OUT.mkdir(parents=True, exist_ok=True)
read = lambda n: pd.read_csv(DATA / f"{n}.csv", keep_default_na=False, na_values=[""])

users, accounts, opps = read("users"), read("accounts"), read("opportunities")
hist, leads, acts = read("opportunity_history"), read("leads"), read("activities")
SNAPSHOT = "2026-09-30"
FUNNEL = ["Prospecting", "Qualification", "Needs Analysis", "Proposal", "Negotiation", "Closed Won"]

# ---------------------------------------------------------------- opportunities (flat)
hist["stage_no"] = hist.stage.map({s: i + 1 for i, s in enumerate(FUNNEL)})
max_stage = hist.dropna(subset=["stage_no"]).groupby("opportunity_id").stage_no.max().astype(int)
touches = acts.groupby("opportunity_id").size()

o = (opps.merge(users[["user_id", "rep_name", "region", "team"]], left_on="owner_id", right_on="user_id")
         .merge(accounts[["account_id", "account_name", "industry", "employee_band"]], on="account_id"))
o["cycle_days"] = (pd.to_datetime(o.close_date) - pd.to_datetime(o.created_date)).dt.days
o["max_stage_no"] = o.opportunity_id.map(max_stage).fillna(1).astype(int)
o["activities"] = o.opportunity_id.map(touches).fillna(0).astype(int)
o["weighted_amount"] = o.amount * o.probability / 100
o["status"] = o.apply(lambda r: "Won" if r.is_won else ("Lost" if r.is_closed else "Open"), axis=1)
cols = ["opportunity_id", "opportunity_name", "account_name", "industry", "employee_band",
        "rep_name", "region", "team", "lead_source", "type", "stage", "status", "probability",
        "forecast_category", "amount", "weighted_amount", "created_date", "close_date",
        "is_closed", "is_won", "cycle_days", "max_stage_no", "activities", "loss_reason"]
o[cols].to_csv(OUT / "opportunities.csv", index=False)

# ---------------------------------------------------------------- funnel (long)
rows = []
for r in o.itertuples():
    for n in range(1, r.max_stage_no + 1):
        rows.append([r.opportunity_id, r.region, r.team, r.created_date, n, FUNNEL[n - 1]])
pd.DataFrame(rows, columns=["opportunity_id", "region", "team", "created_date", "stage_no", "stage"]) \
  .to_csv(OUT / "funnel.csv", index=False)

# ---------------------------------------------------------------- quota by rep and quarter
won = o[o.is_won == 1].copy()
won["quarter_start"] = pd.to_datetime(won.close_date).dt.to_period("Q").dt.start_time
won_q = won.groupby(["rep_name", "quarter_start"]).amount.sum()
quarters = pd.period_range("2024Q1", "2026Q3", freq="Q").start_time
q = pd.MultiIndex.from_product([users.rep_name, quarters], names=["rep_name", "quarter_start"]).to_frame(index=False)
q = q.merge(users[["rep_name", "region", "team", "quarterly_quota"]], on="rep_name")
q["won_revenue"] = q.set_index(["rep_name", "quarter_start"]).index.map(won_q).fillna(0).values
q["quarter_start"] = q.quarter_start.dt.date
q.to_csv(OUT / "rep_quota_by_quarter.csv", index=False)

# ---------------------------------------------------------------- lead source summary
lu = leads.merge(users[["user_id", "region", "team"]], left_on="owner_id", right_on="user_id")
lu["year"] = lu.created_date.str[:4].astype(int)
ld = lu.groupby(["region", "team", "year", "lead_source"]).agg(
    leads=("lead_id", "size"), converted_leads=("status", lambda s: int((s == "Converted").sum())))
closed = o[o.is_closed == 1].copy()
closed["year"] = closed.close_date.str[:4].astype(int)
od = closed.groupby(["region", "team", "year", "lead_source"]).agg(
    closed_opps=("is_closed", "sum"), won_opps=("is_won", "sum"),
    won_revenue=("amount", lambda s: s[closed.loc[s.index, "is_won"] == 1].sum()))
ld.join(od, how="outer").fillna(0).astype(int).reset_index().to_csv(OUT / "lead_source_summary.csv", index=False)

# ---------------------------------------------------------------- data quality
recent = set(acts[acts.activity_date >= "2026-08-31"].opportunity_id)
last_stage = hist.sort_values("entered_date").groupby("opportunity_id").stage.last()
open_o = opps[opps.is_closed == 0]
pd.DataFrame([
    ["Open deal with no activity in 30 days", int((~open_o.opportunity_id.isin(recent)).sum())],
    ["Missing amount", int(opps.amount.isna().sum())],
    ["Open deal with close date in the past", int((open_o.close_date < SNAPSHOT).sum())],
    ["Current stage disagrees with stage history", int((opps.set_index("opportunity_id").stage != last_stage).sum())],
], columns=["issue", "records"]).to_csv(OUT / "data_quality.csv", index=False)

for f in sorted(OUT.glob("*.csv")):
    print(f"{f.relative_to(ROOT)}: {sum(1 for _ in open(f)) - 1} rows")
