-- 03. Rep leaderboard: revenue, win rate, deal size and rank within region
-- Business question: who are the top performers, and who needs coaching?
-- Techniques: JOIN, conditional aggregation, RANK() OVER (PARTITION BY)
SELECT u.rep_name,
       u.region,
       u.team,
       COUNT(*)                                                    AS deals_closed,
       SUM(o.is_won)                                               AS deals_won,
       ROUND(100.0 * SUM(o.is_won) / COUNT(*), 1)                  AS win_rate_pct,
       ROUND(SUM(CASE WHEN o.is_won = 1 THEN o.amount END), 0)     AS won_revenue,
       ROUND(AVG(CASE WHEN o.is_won = 1 THEN o.amount END), 0)     AS avg_won_deal,
       RANK() OVER (PARTITION BY u.region
                    ORDER BY SUM(CASE WHEN o.is_won = 1 THEN o.amount END) DESC) AS rank_in_region
FROM opportunities o
JOIN users u ON u.user_id = o.owner_id
WHERE o.is_closed = 1
GROUP BY u.user_id
ORDER BY won_revenue DESC;
