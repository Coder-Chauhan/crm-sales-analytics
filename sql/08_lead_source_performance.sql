-- 08. Lead source performance: lead to opportunity to won conversion and revenue
-- Business question: which channels should marketing invest in?
WITH lead_stats AS (
    SELECT lead_source,
           COUNT(*)                                             AS leads,
           SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS converted_leads
    FROM leads
    GROUP BY lead_source
),
opp_stats AS (
    SELECT lead_source,
           SUM(is_closed)                                       AS closed_opps,
           SUM(is_won)                                          AS won_opps,
           SUM(CASE WHEN is_won = 1 THEN amount ELSE 0 END)     AS won_revenue
    FROM opportunities
    GROUP BY lead_source
)
SELECT l.lead_source,
       l.leads,
       ROUND(100.0 * l.converted_leads / l.leads, 1)            AS lead_to_opp_pct,
       ROUND(100.0 * o.won_opps / o.closed_opps, 1)             AS opp_win_rate_pct,
       ROUND(100.0 * o.won_opps / l.leads, 2)                   AS lead_to_win_pct,
       ROUND(o.won_revenue, 0)                                  AS won_revenue,
       ROUND(o.won_revenue / l.leads, 0)                        AS revenue_per_lead
FROM lead_stats l
JOIN opp_stats o USING (lead_source)
ORDER BY revenue_per_lead DESC;
