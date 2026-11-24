-- 02. Monthly won revenue with running total, 3-month moving average and month-over-month change
-- Business question: is revenue growing, and is it seasonal?
-- Techniques: GROUP BY on a derived month, window functions SUM() OVER, AVG() OVER (ROWS), LAG()
WITH monthly AS (
    SELECT strftime('%Y-%m', close_date) AS month,
           SUM(amount)                   AS won_revenue,
           COUNT(*)                      AS deals_won
    FROM opportunities
    WHERE is_won = 1
    GROUP BY 1
)
SELECT month,
       ROUND(won_revenue, 0)                                                     AS won_revenue,
       deals_won,
       ROUND(SUM(won_revenue) OVER (PARTITION BY substr(month, 1, 4) ORDER BY month), 0) AS ytd_revenue,
       ROUND(AVG(won_revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0) AS moving_avg_3m,
       ROUND(100.0 * (won_revenue - LAG(won_revenue) OVER (ORDER BY month))
             / LAG(won_revenue) OVER (ORDER BY month), 1)                         AS mom_change_pct
FROM monthly
ORDER BY month;
