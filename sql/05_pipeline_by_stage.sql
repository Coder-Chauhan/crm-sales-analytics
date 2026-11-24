-- 05. Open pipeline by stage and forecast category
-- Business question: how much is in the pipeline, how far along is it, and what is it worth weighted?
SELECT stage,
       forecast_category,
       COUNT(*)                                     AS open_deals,
       ROUND(SUM(amount), 0)                        AS pipeline_amount,
       ROUND(SUM(amount * probability / 100.0), 0)  AS weighted_amount,
       ROUND(AVG(julianday('2026-09-30') - julianday(created_date)), 0) AS avg_age_days
FROM opportunities
WHERE is_closed = 0
GROUP BY stage, forecast_category
ORDER BY MIN(probability);
