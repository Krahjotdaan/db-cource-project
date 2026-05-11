SELECT MAX(user_id) FROM users;
SELECT setval('users_user_id_seq', (SELECT COALESCE(MAX(user_id), 0) FROM users));

INSERT INTO users (name, email, phone_number) 
VALUES ('Иванов Иван Иванович', 'ivan.valid@example.com', '+79001234567');
SELECT * FROM users WHERE email = 'ivan.valid@example.com';

INSERT INTO users (user_name, email, phone_number) 
VALUES ('Петров Петр Петрович', 'petr.invalid-email.com', '+79007654321');

INSERT INTO users (user_name, email, phone_number) 
VALUES ('Кеков Кек Кекович', 'kek@test.com', '123');