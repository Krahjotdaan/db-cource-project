WITH user_activity AS (
    SELECT 
        u.user_id,
        u.user_name,
        COUNT(l.log_id) AS total_sessions,
        ROUND(AVG(l.watched_duration_sec)::numeric, 2) AS avg_watched_sec
    FROM users u
    LEFT JOIN user_session_logs l ON u.user_id = l.user_id
    GROUP BY u.user_id, u.user_name
),
subscription_history AS (
    SELECT 
        user_id,
        valid_from,
        valid_to,
        LEAD(valid_from) OVER (PARTITION BY user_id ORDER BY valid_from) AS next_start
    FROM subscriptions
),
retention_status AS (
    SELECT 
        user_id,
        CASE 
            WHEN BOOL_OR(
                next_start IS NOT NULL 
                AND next_start <= valid_to + INTERVAL '30 days'
            ) THEN 'Retained'
            ELSE 'Churned'
        END AS retention_status
    FROM subscription_history
    WHERE valid_to < CURRENT_DATE 
    GROUP BY user_id
)
SELECT 
    ua.user_id,
    ua.user_name,
    ua.total_sessions,
    ua.avg_watched_sec,
    COALESCE(rs.retention_status, 'No History') AS retention_status
FROM user_activity ua
LEFT JOIN retention_status rs ON ua.user_id = rs.user_id
ORDER BY ua.avg_watched_sec DESC;