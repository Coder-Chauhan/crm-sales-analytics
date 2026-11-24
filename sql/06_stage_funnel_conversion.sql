-- 06. Stage-to-stage funnel conversion, built from stage history
-- Business question: where in the sales process do we lose the most deals?
-- Techniques: reaching a stage = having a history row for it or any later stage; LAG() for step conversion
WITH stage_order(stage, n) AS (
    VALUES ('Prospecting', 1), ('Qualification', 2), ('Needs Analysis', 3),
           ('Proposal', 4), ('Negotiation', 5), ('Closed Won', 6)
),
max_reached AS (            -- furthest stage each deal reached
    SELECT h.opportunity_id, MAX(s.n) AS max_n
    FROM opportunity_history h
    JOIN stage_order s ON s.stage = h.stage
    GROUP BY h.opportunity_id
),
reached AS (
    SELECT s.stage, s.n, COUNT(m.opportunity_id) AS deals_reached
    FROM stage_order s
    LEFT JOIN max_reached m ON m.max_n >= s.n
    GROUP BY s.stage, s.n
)
SELECT stage,
       deals_reached,
       ROUND(100.0 * deals_reached / FIRST_VALUE(deals_reached) OVER (ORDER BY n), 1) AS pct_of_created,
       ROUND(100.0 * deals_reached / LAG(deals_reached) OVER (ORDER BY n), 1)         AS step_conversion_pct
FROM reached
ORDER BY n;
