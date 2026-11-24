-- 07. Average days spent in each stage (stage velocity)
-- Business question: where do deals stall?
-- Techniques: LEAD() over each deal's history to find when it left a stage
WITH timeline AS (
    SELECT opportunity_id,
           stage,
           entered_date,
           LEAD(entered_date) OVER (PARTITION BY opportunity_id ORDER BY entered_date) AS left_date
    FROM opportunity_history
)
SELECT stage,
       COUNT(*)                                                         AS deals_passed_through,
       ROUND(AVG(julianday(left_date) - julianday(entered_date)), 1)    AS avg_days_in_stage,
       MAX(julianday(left_date) - julianday(entered_date))              AS max_days_in_stage
FROM timeline
WHERE left_date IS NOT NULL
GROUP BY stage
ORDER BY CASE stage WHEN 'Prospecting' THEN 1 WHEN 'Qualification' THEN 2
                    WHEN 'Needs Analysis' THEN 3 WHEN 'Proposal' THEN 4 ELSE 5 END;
