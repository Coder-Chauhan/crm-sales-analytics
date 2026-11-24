-- 04. Quarterly quota attainment per rep
-- Business question: which reps hit quota each quarter, and how consistent are they?
-- Techniques: quarter derivation, CROSS JOIN to keep quarters with zero wins, LEFT JOIN, CASE banding
WITH quarters AS (
    SELECT DISTINCT strftime('%Y', close_date) || '-Q' ||
           ((CAST(strftime('%m', close_date) AS INTEGER) + 2) / 3) AS quarter
    FROM opportunities
    WHERE is_won = 1 AND close_date <= '2026-09-30'
),
won AS (
    SELECT owner_id,
           strftime('%Y', close_date) || '-Q' ||
           ((CAST(strftime('%m', close_date) AS INTEGER) + 2) / 3) AS quarter,
           SUM(amount) AS won_revenue
    FROM opportunities
    WHERE is_won = 1
    GROUP BY 1, 2
)
SELECT q.quarter,
       u.rep_name,
       u.region,
       u.quarterly_quota,
       ROUND(COALESCE(w.won_revenue, 0), 0)                               AS won_revenue,
       ROUND(100.0 * COALESCE(w.won_revenue, 0) / u.quarterly_quota, 1)   AS attainment_pct,
       CASE WHEN COALESCE(w.won_revenue, 0) >= u.quarterly_quota       THEN 'Hit'
            WHEN COALESCE(w.won_revenue, 0) >= 0.8 * u.quarterly_quota THEN 'Near (80-99%)'
            ELSE 'Missed' END                                             AS status
FROM quarters q
CROSS JOIN users u
LEFT JOIN won w ON w.owner_id = u.user_id AND w.quarter = q.quarter
ORDER BY q.quarter, attainment_pct DESC;
