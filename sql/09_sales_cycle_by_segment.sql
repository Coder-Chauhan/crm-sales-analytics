-- 09. Sales cycle length by deal type and deal size band
-- Business question: how long do different kinds of deals take to close?
SELECT type,
       CASE WHEN amount < 15000  THEN '1. Under 15k'
            WHEN amount < 50000  THEN '2. 15k to 50k'
            WHEN amount < 100000 THEN '3. 50k to 100k'
            ELSE '4. 100k and over' END                                   AS size_band,
       COUNT(*)                                                           AS deals_won,
       ROUND(AVG(julianday(close_date) - julianday(created_date)), 0)     AS avg_cycle_days,
       ROUND(AVG(amount), 0)                                              AS avg_amount
FROM opportunities
WHERE is_won = 1 AND amount IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;
