-- 11. Why we lose: loss reasons with share of lost revenue
-- Business question: what should product and pricing teams act on?
SELECT loss_reason,
       COUNT(*)                                                    AS deals_lost,
       ROUND(SUM(amount), 0)                                       AS lost_revenue,
       ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 1)    AS pct_of_lost_revenue
FROM opportunities
WHERE is_closed = 1 AND is_won = 0
GROUP BY loss_reason
ORDER BY lost_revenue DESC;
