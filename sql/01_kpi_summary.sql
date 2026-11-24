-- 01. Headline KPIs: won revenue, win rate, average deal size, sales cycle, open pipeline
-- Business question: how is the sales team performing overall?
WITH closed AS (
    SELECT *,
           julianday(close_date) - julianday(created_date) AS cycle_days
    FROM opportunities
    WHERE is_closed = 1
),
open_pipe AS (
    SELECT SUM(amount)                      AS open_pipeline,
           SUM(amount * probability / 100.0) AS weighted_pipeline,
           COUNT(*)                          AS open_deals
    FROM opportunities
    WHERE is_closed = 0
)
SELECT
    ROUND(SUM(CASE WHEN is_won = 1 THEN amount END), 0)                     AS won_revenue,
    SUM(is_won)                                                             AS deals_won,
    COUNT(*)                                                                AS deals_closed,
    ROUND(100.0 * SUM(is_won) / COUNT(*), 1)                                AS win_rate_pct,
    ROUND(AVG(CASE WHEN is_won = 1 THEN amount END), 0)                     AS avg_won_deal,
    ROUND(AVG(CASE WHEN is_won = 1 THEN cycle_days END), 0)                 AS avg_cycle_days_won,
    (SELECT ROUND(open_pipeline, 0)     FROM open_pipe)                     AS open_pipeline,
    (SELECT ROUND(weighted_pipeline, 0) FROM open_pipe)                     AS weighted_pipeline,
    (SELECT open_deals                  FROM open_pipe)                     AS open_deals
FROM closed;
