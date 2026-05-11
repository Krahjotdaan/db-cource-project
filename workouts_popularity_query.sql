SELECT 
    w.workout_name,
    COUNT(l.log_id) AS total_views,
    ROUND(AVG(l.watched_duration_sec::FLOAT / NULLIF(ws.duration_sec, 0) * 100)::numeric, 2) || '%' AS avg_completion_rate
FROM workouts w
JOIN workout_sessions ws ON w.workout_id = ws.workout_id
JOIN user_session_logs l ON ws.session_id = l.session_id
GROUP BY w.workout_name
ORDER BY avg_completion_rate DESC;