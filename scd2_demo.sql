SELECT setval('subscriptions_subscription_id_seq', (SELECT COALESCE(MAX(subscription_id), 0) FROM subscriptions));

SELECT subscription_id, user_id, valid_from, valid_to 
FROM subscriptions 
WHERE user_id = 1 
ORDER BY valid_from DESC;

-- 1. Валидные данные
INSERT INTO tmp_subscriptions (user_id, valid_from, valid_to)
VALUES (1, '2026-06-01', '2026-06-30');
CALL load_scd2_subscriptions();

SELECT subscription_id, user_id, valid_from, valid_to 
FROM subscriptions 
WHERE user_id = 1 
ORDER BY valid_from;

-- 2. Начало позже конца
INSERT INTO tmp_subscriptions (user_id, valid_from, valid_to)
VALUES (1, '2026-07-01', '2026-06-01');
CALL load_scd2_subscriptions();

-- 3. Пересечение периодов
INSERT INTO tmp_subscriptions (user_id, valid_from, valid_to)
VALUES (1, '2026-06-05', '2026-07-05');
CALL load_scd2_subscriptions();

-- 4. Начало в прошлом
INSERT INTO tmp_subscriptions (user_id, valid_from, valid_to)
VALUES (1, CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE + INTERVAL '30 days');
CALL load_scd2_subscriptions();