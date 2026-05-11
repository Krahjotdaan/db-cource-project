EXPLAIN ANALYZE
SELECT 
    l.session_id,
    l.started_at,
    l.watched_duration_sec
FROM user_session_logs l
WHERE l.user_id = 10
  AND l.started_at > '2025-06-01'
ORDER BY l.started_at DESC;