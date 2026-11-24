-- 10. Does sales engagement relate to winning?
-- Business question: do deals that get more frequent touches (calls, emails, meetings) win more often?
-- Raw activity COUNT is biased: deals lost early are short, so they collect few activities by default.
-- Using activities per week the deal was open removes that bias. Still correlation, not causation.
WITH touches AS (
    SELECT o.opportunity_id,
           o.is_won,
           COUNT(a.activity_id) * 7.0 /
               MAX(julianday(o.close_date) - julianday(o.created_date), 7)   AS touches_per_week,
           SUM(CASE WHEN a.activity_type IN ('Meeting', 'Demo') THEN 1 ELSE 0 END) AS meetings_demos
    FROM opportunities o
    LEFT JOIN activities a ON a.opportunity_id = o.opportunity_id
    WHERE o.is_closed = 1
    GROUP BY o.opportunity_id
),
banded AS (
    SELECT *, NTILE(4) OVER (ORDER BY touches_per_week) AS quartile
    FROM touches
)
SELECT 'Q' || quartile ||
       CASE quartile WHEN 1 THEN ' (least engaged)' WHEN 4 THEN ' (most engaged)' ELSE '' END AS engagement_quartile,
       COUNT(*)                                  AS closed_deals,
       ROUND(MIN(touches_per_week), 2)           AS min_touches_per_week,
       ROUND(MAX(touches_per_week), 2)           AS max_touches_per_week,
       ROUND(100.0 * AVG(is_won), 1)             AS win_rate_pct
FROM banded
GROUP BY quartile
ORDER BY quartile;
