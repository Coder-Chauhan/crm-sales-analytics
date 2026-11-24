"""
Generate a synthetic, Salesforce-style CRM dataset for a fictional B2B SaaS company.

Objects (modelled on standard Salesforce objects):
  users               -> sales reps (User), with region, team and quarterly quota
  accounts            -> customer companies (Account)
  leads               -> inbound and outbound leads (Lead), some converted
  opportunities       -> deals (Opportunity), with stage, amount, close date
  opportunity_history -> stage changes per deal (OpportunityFieldHistory)
  activities          -> calls, emails and meetings logged against deals (Task / Event)

All data is fictional. The random seed is fixed so results are reproducible.
Reporting window: 2024-01-01 to 2026-09-30 (the "today" of the CRM).
"""
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

START = date(2024, 1, 1)          # first day of the reporting window
GEN_START = date(2023, 7, 1)      # warm-up so early 2024 already has a mature pipeline
SNAPSHOT = date(2026, 9, 30)
OUT = Path(__file__).resolve().parent.parent / "data"
OUT.mkdir(exist_ok=True)

STAGES = ["Prospecting", "Qualification", "Needs Analysis", "Proposal", "Negotiation"]
PROBABILITY = {"Prospecting": 10, "Qualification": 20, "Needs Analysis": 40,
               "Proposal": 60, "Negotiation": 80, "Closed Won": 100, "Closed Lost": 0}
FORECAST = {"Prospecting": "Pipeline", "Qualification": "Pipeline", "Needs Analysis": "Pipeline",
            "Proposal": "Best Case", "Negotiation": "Commit", "Closed Won": "Closed",
            "Closed Lost": "Omitted"}
# probability a deal advances out of each stage (before rep / source adjustments)
ADVANCE = {"Prospecting": 0.70, "Qualification": 0.72, "Needs Analysis": 0.75,
           "Proposal": 0.70, "Negotiation": 0.78}
# mean days spent in each stage
STAGE_DAYS = {"Prospecting": 14, "Qualification": 20, "Needs Analysis": 28,
              "Proposal": 24, "Negotiation": 18}
LOSS_REASONS = ["Price", "Chose competitor", "No budget", "No decision", "Timing", "Missing feature"]

# ---------------------------------------------------------------- users (reps)
first = ["Aarav", "Mia", "Lucas", "Priya", "Noah", "Chloe", "Ethan", "Ananya",
         "Oliver", "Sofia", "Jack", "Isla", "Rohan", "Grace"]
last = ["Sharma", "Nguyen", "Smith", "Patel", "Brown", "Wilson", "Taylor", "Iyer",
        "Martin", "Rossi", "Kelly", "Chen", "Mehta", "Walker"]
regions = ["APAC", "APAC", "APAC", "APAC", "APAC", "EMEA", "EMEA", "EMEA", "EMEA",
           "AMER", "AMER", "AMER", "AMER", "AMER"]
users = []
for i in range(14):
    skill = np.clip(np.random.normal(1.0, 0.09), 0.82, 1.18)
    users.append({
        "user_id": f"U{i+1:03d}",
        "rep_name": f"{first[i]} {last[i]}",
        "region": regions[i],
        "team": "Enterprise" if i % 3 == 0 else "Mid-Market",
        "hire_date": (START - timedelta(days=random.randint(60, 900))).isoformat(),
        "quarterly_quota": 0,  # filled below
        "_skill": skill,
    })
users_df = pd.DataFrame(users)

# ---------------------------------------------------------------- accounts
industries = {"Technology": 1.25, "Financial Services": 1.40, "Healthcare": 1.15,
              "Retail": 0.85, "Manufacturing": 1.00, "Education": 0.70,
              "Hospitality": 0.80, "Logistics": 0.95}
name_a = ["Blue", "North", "Bright", "Summit", "Harbour", "Silver", "Coral", "Iron", "Maple",
          "Swift", "Lumen", "Apex", "Cedar", "Nova", "Orbit", "Prime", "Quartz", "River"]
name_b = ["Labs", "Systems", "Group", "Health", "Retail", "Logistics", "Partners", "Works",
          "Analytics", "Foods", "Capital", "Studios", "Networks", "Holdings"]
accounts, used = [], set()
for i in range(420):
    while True:
        nm = f"{random.choice(name_a)} {random.choice(name_b)}"
        nm = nm if nm not in used else f"{nm} {random.choice(['Co', 'Pty Ltd', 'Inc', 'Ltd'])}"
        if nm not in used:
            used.add(nm)
            break
    owner = users_df.sample(1).iloc[0]
    size = random.choices(["1-50", "51-200", "201-1000", "1000+"], [0.30, 0.35, 0.23, 0.12])[0]
    accounts.append({
        "account_id": f"A{i+1:04d}",
        "account_name": nm,
        "industry": random.choice(list(industries)),
        "employee_band": size,
        "region": owner.region,
        "owner_id": owner.user_id,
        "created_date": (START + timedelta(days=random.randint(-400, 900))).isoformat(),
    })
acc_df = pd.DataFrame(accounts)
size_mult = {"1-50": 0.45, "51-200": 0.9, "201-1000": 1.6, "1000+": 2.8}

# ---------------------------------------------------------------- leads
sources = {  # (share of leads, lead->opp conversion, win-rate multiplier, deal-size multiplier)
    "Web": (0.34, 0.16, 0.92, 0.85),
    "Referral": (0.12, 0.38, 1.20, 1.10),
    "Event": (0.14, 0.22, 1.00, 1.05),
    "Outbound": (0.26, 0.13, 0.85, 1.15),
    "Partner": (0.14, 0.30, 1.10, 1.25),
}
n_days = (SNAPSHOT - GEN_START).days
leads, opps, history, activities = [], [], [], []
lead_no = opp_no = act_no = 0


def seasonal_day():
    """Pick a creation day with a Q4 (Oct to Dec) bump and a January dip."""
    while True:
        d = GEN_START + timedelta(days=random.randint(0, n_days - 1))
        w = {1: 0.75, 10: 1.2, 11: 1.3, 12: 1.05}.get(d.month, 1.0)
        # gentle company growth over time
        w *= 0.65 + 0.7 * (d - GEN_START).days / n_days
        if random.random() < w / 1.9:
            return d


for _ in range(12000):
    lead_no += 1
    src = random.choices(list(sources), [v[0] for v in sources.values()])[0]
    share, conv, win_m, size_m = sources[src]
    created = seasonal_day()
    acc = acc_df.sample(1).iloc[0]
    rep = users_df[users_df.region == acc.region].sample(1).iloc[0]
    age = (SNAPSHOT - created).days
    converted = random.random() < conv and age > 5
    status = "Converted" if converted else (
        "Open" if age < 45 and random.random() < 0.6 else random.choice(["Unqualified", "Nurturing", "Unqualified"]))
    lead = {"lead_id": f"L{lead_no:05d}", "lead_source": src, "created_date": created.isoformat(),
            "status": status, "owner_id": rep.user_id, "account_id": acc.account_id,
            "converted_date": None, "converted_opportunity_id": None}

    if converted:
        opp_no += 1
        oid = f"O{opp_no:05d}"
        o_created = created + timedelta(days=random.randint(1, 14))
        if o_created > SNAPSHOT:
            o_created = SNAPSHOT
        lead["converted_date"] = o_created.isoformat()
        lead["converted_opportunity_id"] = oid
        opp_type = random.choices(["New Business", "Upsell", "Renewal"], [0.62, 0.23, 0.15])[0]
        type_m = {"New Business": 1.0, "Upsell": 0.55, "Renewal": 0.8}[opp_type]
        type_win = {"New Business": 1.0, "Upsell": 1.12, "Renewal": 1.25}[opp_type]
        team_m = 1.6 if rep.team == "Enterprise" else 1.0
        amount = np.random.lognormal(mean=np.log(24000), sigma=0.55)
        amount *= industries[acc.industry] * size_mult[acc.employee_band] * size_m * type_m * team_m
        amount = round(amount / 100) * 100

        # walk through the stages
        d = o_created
        stage = "Prospecting"
        history.append({"opportunity_id": oid, "stage": stage, "entered_date": d.isoformat()})
        is_closed = is_won = False
        loss_reason = None
        idx = 0
        while True:
            # bigger deals take longer
            dwell = max(1, int(np.random.gamma(2.0, STAGE_DAYS[stage] / 2.0) * (1 + 0.25 * np.log10(amount / 20000 + 1))))
            nxt = d + timedelta(days=dwell)
            if nxt > SNAPSHOT:
                break  # still sitting in this stage today
            p = ADVANCE[stage] * rep._skill * win_m ** 0.5 * type_win ** 0.5
            if amount > 90000:
                p *= 0.95
            d = nxt
            if random.random() < min(p, 0.97):
                if idx == len(STAGES) - 1:
                    stage, is_closed, is_won = "Closed Won", True, True
                else:
                    idx += 1
                    stage = STAGES[idx]
            else:
                stage, is_closed = "Closed Lost", True
                loss_reason = random.choices(LOSS_REASONS, [0.24, 0.26, 0.16, 0.16, 0.10, 0.08])[0]
            history.append({"opportunity_id": oid, "stage": stage, "entered_date": d.isoformat()})
            if is_closed:
                break

        if is_closed:
            close_date = d
        else:  # expected close date in the future
            remaining = sum(STAGE_DAYS[s] for s in STAGES[idx:])
            close_date = SNAPSHOT + timedelta(days=max(7, int(remaining * random.uniform(0.6, 1.5))))

        # activities: winners and engaged deals get more touches
        span = max(1, (min(d, SNAPSHOT) - o_created).days)
        base = span / 6
        n_act = max(1, int(np.random.poisson(base * (1.35 if is_won else 1.0) * rep._skill)))
        for _a in range(min(n_act, 60)):
            act_no += 1
            activities.append({
                "activity_id": f"T{act_no:06d}", "opportunity_id": oid, "owner_id": rep.user_id,
                "activity_type": random.choices(["Call", "Email", "Meeting", "Demo"], [0.35, 0.40, 0.17, 0.08])[0],
                "activity_date": (o_created + timedelta(days=random.randint(0, span))).isoformat(),
            })

        opps.append({
            "opportunity_id": oid, "opportunity_name": f"{acc.account_name} - {opp_type}",
            "account_id": acc.account_id, "owner_id": rep.user_id, "lead_source": src,
            "type": opp_type, "amount": amount, "stage": stage,
            "probability": PROBABILITY[stage], "forecast_category": FORECAST[stage],
            "created_date": o_created.isoformat(), "close_date": close_date.isoformat(),
            "is_closed": int(is_closed), "is_won": int(is_won), "loss_reason": loss_reason,
        })
    leads.append(lead)

opp_df = pd.DataFrame(opps)
leads_df = pd.DataFrame(leads)
hist_df = pd.DataFrame(history)
act_df = pd.DataFrame(activities)

# ---------------------------------------------------------------- trim the warm-up period
# keep deals still open or closed inside the reporting window, and leads created in it
# (plus older leads whose deal is kept)
keep = opp_df[(opp_df.is_closed == 0) | (opp_df.close_date >= START.isoformat())].opportunity_id
opp_df = opp_df[opp_df.opportunity_id.isin(keep)].reset_index(drop=True)
hist_df = hist_df[hist_df.opportunity_id.isin(keep)]
act_df = act_df[act_df.opportunity_id.isin(keep)]
leads_df = leads_df[(leads_df.created_date >= START.isoformat()) |
                    (leads_df.converted_opportunity_id.isin(keep))]

# ---------------------------------------------------------------- quotas
# set quarterly quota near each rep's typical won revenue so attainment varies around 100%
won = opp_df[opp_df.is_won == 1].copy()
won["q"] = pd.to_datetime(won.close_date).dt.to_period("Q")
per_rep = won.groupby("owner_id").amount.sum() / won.q.nunique()
users_df["_won_q"] = users_df.user_id.map(per_rep).fillna(per_rep.mean())
team_avg = users_df.groupby("team")._won_q.mean()
for i, u in users_df.iterrows():
    # quota is set per team (same target for peers), lifted slightly as companies do
    base = team_avg[u.team] * 0.95
    users_df.at[i, "quarterly_quota"] = int(round(base / 5000) * 5000)
users_df = users_df.drop(columns="_won_q")

# ---------------------------------------------------------------- a few realistic data-quality issues
# CRM data is never perfectly clean; these give the hygiene queries something to find
dq = opp_df.sample(9, random_state=1).index
opp_df.loc[dq[:4], "amount"] = None                      # missing amount
opp_df.loc[dq[4:7], "close_date"] = "2026-06-15"           # open deals with a past close date
opp_df.loc[dq[4:7], ["is_closed", "is_won"]] = 0
opp_df.loc[dq[4:7], "stage"] = "Proposal"
opp_df.loc[dq[4:7], "probability"] = 60
opp_df.loc[dq[4:7], "forecast_category"] = "Best Case"

users_df.drop(columns="_skill").to_csv(OUT / "users.csv", index=False)
acc_df.to_csv(OUT / "accounts.csv", index=False)
leads_df.to_csv(OUT / "leads.csv", index=False)
opp_df.to_csv(OUT / "opportunities.csv", index=False)
hist_df.to_csv(OUT / "opportunity_history.csv", index=False)
act_df.to_csv(OUT / "activities.csv", index=False)

print(f"users {len(users_df)}, accounts {len(acc_df)}, leads {len(leads_df)}, "
      f"opportunities {len(opp_df)}, stage changes {len(hist_df)}, activities {len(act_df)}")
