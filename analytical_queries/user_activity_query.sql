EXPLAIN ANALYZE
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
        LEAD(valid_from) OVER (PARTITION BY user_id ORDER BY valid_from) AS next_start,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY valid_to DESC) as rn_last
    FROM subscriptions
),
retention_status AS (
    SELECT 
        user_id,
        CASE 
            -- 1. Active: Последняя подписка еще действует
            WHEN MAX(CASE WHEN rn_last = 1 THEN valid_to END) >= CURRENT_DATE THEN 'Active'
            
            -- 2. Retained: Последняя подписка закончилась менее 45 дней назад или есть следующая запланированная подписка
            WHEN MAX(CASE WHEN rn_last = 1 THEN next_start END) IS NOT NULL THEN 'Retained'
            WHEN MAX(CASE WHEN rn_last = 1 THEN valid_to END) >= CURRENT_DATE - INTERVAL '45 days' THEN 'Retained'
            
            -- 3. Churned: Последняя подписка закончилась давно и продолжения нет
            ELSE 'Churned'
        END AS retention_status
    FROM subscription_history
    GROUP BY user_id
)
SELECT 
    ua.user_id,
    ua.user_name,
    ua.total_sessions,
    ua.avg_watched_sec,
    COALESCE(rs.retention_status, 'No Subscriptions') AS retention_status
FROM user_activity ua
LEFT JOIN retention_status rs ON ua.user_id = rs.user_id
ORDER BY ua.total_sessions DESC;