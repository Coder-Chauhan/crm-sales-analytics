# Building the dashboard in Tableau

This guide builds the CRM sales dashboard in **Tableau Public** (free) from the extracts in
`tableau/data/`. Budget about 3 to 4 hours. When you finish, publish it to your Tableau Public
profile, save the workbook as `tableau/CRM_Sales_Analytics.twbx`, and add the public link and a
screenshot to the README.

Regenerate the extracts at any time with `python scripts/export_tableau.py`.

## 1. Connect the data

Tableau Public > Connect > Text file, and add each CSV as a **separate data source** (they are at
different grains, so do not join or relate them):

| Data source | Grain | Used for |
|---|---|---|
| `opportunities.csv` | one row per deal | KPIs, revenue trend, reps, pipeline, loss reasons |
| `funnel.csv` | one row per deal per stage reached | funnel |
| `rep_quota_by_quarter.csv` | one row per rep per quarter | quota attainment |
| `lead_source_summary.csv` | region, team, year, source | lead source table |
| `data_quality.csv` | one row per check | data quality table |

In `opportunities`, check the field types: `created_date` and `close_date` as Date, `amount`,
`weighted_amount` as Number (decimal), `is_closed`, `is_won` as Number (whole). Four `amount`
values are empty on purpose (dirty data for the quality checks).

## 2. Calculated fields

### opportunities

```
// Won Revenue
SUM(IF [is_won] = 1 THEN [amount] END)

// Deals Won
SUM([is_won])

// Deals Closed
SUM([is_closed])

// Win Rate            (format as percentage, 1 decimal)
SUM([is_won]) / SUM([is_closed])

// Avg Won Deal
[Won Revenue] / [Deals Won]

// Avg Sales Cycle (days)
AVG(IF [is_won] = 1 THEN [cycle_days] END)

// Open Pipeline
SUM(IF [is_closed] = 0 THEN [amount] END)

// Weighted Pipeline
SUM(IF [is_closed] = 0 THEN [weighted_amount] END)

// Lost Revenue
SUM(IF [status] = "Lost" THEN [amount] END)

// Won Revenue 3M Avg   (table calculation, compute along Month of close_date)
WINDOW_AVG([Won Revenue], -2, 0)

// Won Revenue YoY %    (table calculation, compute along Year of close_date)
([Won Revenue] - LOOKUP([Won Revenue], -1)) / ABS(LOOKUP([Won Revenue], -1))

// Activities per Week  (engagement, normalised for deal length)
[activities] * 7 / MAX([cycle_days], 7)
```

### funnel

```
// Deals Reached
COUNTD([opportunity_id])

// % of Created         (table calculation, compute along stage)
COUNTD([opportunity_id]) / WINDOW_MAX(COUNTD([opportunity_id]))

// Step Conversion      (table calculation, compute along stage)
COUNTD([opportunity_id]) / LOOKUP(COUNTD([opportunity_id]), -1)
```

### rep_quota_by_quarter

```
// Quota Attainment
SUM([won_revenue]) / SUM([quarterly_quota])

// Attainment Band
IF [Quota Attainment] >= 1 THEN "Hit"
ELSEIF [Quota Attainment] >= 0.8 THEN "Near (80-99%)"
ELSE "Missed" END
```

### lead_source_summary

```
// Lead to Opp %
SUM([converted_leads]) / SUM([leads])

// Opp Win Rate
SUM([won_opps]) / SUM([closed_opps])

// Revenue per Lead
SUM([won_revenue]) / SUM([leads])
```

Add a data source filter on `year` >= 2024 (a few converted leads were created in late 2023).

## 3. Parameters and filters

Create three filters and apply them across worksheets (Apply to Worksheets > Selected worksheets):

- **Region** and **Team**: on every sheet. They exist under the same names in every data source, so
  use them as filters on each source, or create a parameter for each and filter with
  `[region] = [Region Parameter] OR [Region Parameter] = "All"` to drive all sources at once
  (parameters are the reliable way to filter across unrelated sources).
- **Close Year**: on revenue, reps, quota, loss and lead-source sheets. Leave it **off** the open
  pipeline sheet, because pipeline is a snapshot as of 30 September 2026.

## 4. Worksheets

| Sheet | How to build it |
|---|---|
| **KPI cards** (5 sheets) | One measure each on Text: Won Revenue, Win Rate, Avg Won Deal, Avg Sales Cycle, Open Pipeline (add Weighted Pipeline as a second line) |
| **Revenue trend** | Columns: MONTH(close_date) continuous. Rows: Won Revenue as bars, plus Won Revenue 3M Avg as a line on a **dual axis, synchronised** (same scale, so it is one axis visually). Filter status = Won |
| **Funnel** | funnel source. Rows: stage (sort by stage_no). Columns: Deals Reached as bars. Labels: % of Created and Step Conversion |
| **Lead sources** | Rows: lead_source. Text table with Leads, Lead to Opp %, Opp Win Rate, Revenue per Lead; sort by Revenue per Lead descending |
| **Rep table** | rep_quota_by_quarter source. Rows: rep_name, region, team. Columns: Measure Names with won_revenue and Quota Attainment. Colour Quota Attainment with a diverging palette centred at 1 (red below 80%, green at 100% and up). Add Win Rate and Avg Won Deal from opportunities as a separate sheet next to it, or blend on rep_name |
| **Pipeline by stage** | Filter status = Open. Rows: stage (sorted by probability). Columns: SUM(amount). Label with count of deals |
| **Loss reasons** | Filter status = Lost. Rows: loss_reason. Columns: Lost Revenue, quick table calculation Percent of Total |
| **Data quality** | data_quality source, a simple text table of issue and records |

## 5. Dashboard layout

Size: Automatic, or fixed 1200 x 1600 for Tableau Public.

1. Title (the finding): "Referral leads bring in six times the revenue per lead of web leads"
2. Filter row: Region, Team, Close Year
3. KPI cards in one horizontal container
4. Revenue trend, full width
5. Funnel and Lead sources side by side
6. Rep table, full width
7. Pipeline by stage and Loss reasons side by side
8. Data quality, with a text box listing recommended actions
9. A footnote: "Synthetic data. Source and SQL: github.com/Coder-Chauhan/crm-sales-analytics"

Optional: add a **dashboard action** (Filter) so clicking a rep in the rep table filters the
trend and loss reasons to that rep.

## 6. Check your numbers

With no filters, your figures should match `outputs/` from the SQL scripts:

| Measure | Expected |
|---|---|
| Won Revenue | $21,499,700 |
| Deals Won / Deals Closed | 591 / 2,104 |
| Win Rate | 28.1% |
| Avg Sales Cycle | 113 days |
| Open Pipeline | $6,577,600 across 179 deals |
| Deals reaching each funnel stage | 2,283 / 1,661 / 1,239 / 924 / 696 / 592 |
| Revenue per lead: Referral, Web | $5,658, $900 |

If they differ, the usual cause is the empty `amount` values or the 2023 rows in the lead summary.

## 7. Publish

File > Save to Tableau Public. In the workbook settings on Tableau Public, allow downloads so
reviewers can open it. Then put the link at the top of the README.
