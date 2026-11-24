-- 12. CRM data quality checks
-- Business question: can we trust the pipeline? Flags records a sales ops analyst would chase.
SELECT 'Missing amount' AS issue, COUNT(*) AS records
FROM opportunities WHERE amount IS NULL
UNION ALL
SELECT 'Open deal with close date in the past', COUNT(*)
FROM opportunities WHERE is_closed = 0 AND close_date < '2026-09-30'
UNION ALL
SELECT 'Current stage disagrees with stage history', COUNT(*)
FROM opportunities o
WHERE o.stage <> (SELECT h.stage FROM opportunity_history h
                  WHERE h.opportunity_id = o.opportunity_id
                  ORDER BY h.entered_date DESC LIMIT 1)
UNION ALL
SELECT 'Converted lead with no opportunity', COUNT(*)
FROM leads WHERE status = 'Converted' AND converted_opportunity_id IS NULL
UNION ALL
SELECT 'Open deal with no activity in 30 days', COUNT(*)
FROM opportunities o
WHERE o.is_closed = 0
  AND NOT EXISTS (SELECT 1 FROM activities a
                  WHERE a.opportunity_id = o.opportunity_id
                    AND a.activity_date >= date('2026-09-30', '-30 days'));
