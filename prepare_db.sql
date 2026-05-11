DROP TABLE IF EXISTS user_session_logs CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS workout_sessions CASCADE;
DROP TABLE IF EXISTS workouts CASCADE;
DROP TABLE IF EXISTS trainers CASCADE;
DROP TABLE IF EXISTS workout_type CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS tmp_subscriptions CASCADE;


-- 1. DDL
CREATE TABLE users (
	user_id SERIAL PRIMARY KEY,
	user_name VARCHAR(255) NOT NULL,
	email VARCHAR(255) NOT NULL,
	phone_number VARCHAR(20) NOT NULL,
	registration_dttm TIMESTAMP DEFAULT NOW() 
);

CREATE TABLE workout_type (
	type_id SERIAL PRIMARY KEY,
	type_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE trainers (
	trainer_id SERIAL PRIMARY KEY,
	trainer_name VARCHAR(255) NOT NULL
);

CREATE TABLE workouts (
	workout_id SERIAL PRIMARY KEY,
	type_id INT REFERENCES workout_type(type_id),
	workout_name VARCHAR(255) NOT NULL,
	session_numbers INT DEFAULT 0
);

CREATE TABLE workout_sessions (
	session_id SERIAL PRIMARY KEY,
	workout_id INT REFERENCES workouts(workout_id),
	trainer_id INT REFERENCES trainers(trainer_id),
	session_name VARCHAR(255) NOT NULL,
	duration_sec INT NOT NULL,
	video_link VARCHAR(1000) NOT NULL
);

CREATE TABLE subscriptions (
	subscription_id SERIAL PRIMARY KEY,
	user_id INT REFERENCES users(user_id),
	valid_from DATE NOT NULL DEFAULT NOW(),
	valid_to DATE NOT NULL,
	CONSTRAINT chk_dates CHECK (valid_to >= valid_from)
);

CREATE TABLE user_session_logs (
	log_id BIGSERIAL PRIMARY KEY,
	user_id INT REFERENCES users(user_id),
	session_id INT REFERENCES workout_sessions(session_id),
	started_at TIMESTAMP DEFAULT NOW(),
	watched_duration_sec INT NOT NULL CHECK (watched_duration_sec >= 0)
);

CREATE TABLE IF NOT EXISTS tmp_subscriptions (
    user_id INT,
    valid_from DATE,
    valid_to DATE
);


-- 2. Загрузка данных
COPY users(user_id, user_name, email, phone_number, registration_dttm) 
FROM '/tmp/csv_data/users.csv' 
DELIMITER ',' CSV HEADER;

COPY workout_type(type_id, type_name) 
FROM '/tmp/csv_data/workout_type.csv' 
DELIMITER ',' CSV HEADER;

COPY trainers(trainer_id, trainer_name) 
FROM '/tmp/csv_data/trainers.csv' 
DELIMITER ',' CSV HEADER;

COPY workouts(workout_id, type_id, workout_name, session_numbers) 
FROM '/tmp/csv_data/workouts.csv' 
DELIMITER ',' CSV HEADER;

COPY workout_sessions(session_id, workout_id, trainer_id, session_name, duration_sec, video_link) 
FROM '/tmp/csv_data/workout_sessions.csv' 
DELIMITER ',' CSV HEADER;

COPY subscriptions(subscription_id, user_id, valid_from, valid_to) 
FROM '/tmp/csv_data/subscriptions.csv' 
DELIMITER ',' CSV HEADER;

COPY user_session_logs(log_id, user_id, session_id, started_at, watched_duration_sec) 
FROM '/tmp/csv_data/user_session_logs.csv' 
DELIMITER ',' CSV HEADER;


-- 3. Индексы
CREATE INDEX IF NOT EXISTS idx_logs_user_time ON user_session_logs (user_id, started_at);
CREATE INDEX IF NOT EXISTS idx_subs_user_dates ON subscriptions (user_id, valid_from, valid_to);


-- 4. Триггер
CREATE OR REPLACE FUNCTION validate_user_contacts()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.email IS NOT NULL AND NEW.email !~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' THEN
        RAISE EXCEPTION 'Невалидный формат email';
    END IF;

    IF NEW.phone_number IS NOT NULL AND NEW.phone_number !~ '^\+?[0-9\s\-\(\)]{7,20}$' THEN
        RAISE EXCEPTION 'Невалидный формат телефона';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_validate_contacts ON users;
CREATE TRIGGER trigger_validate_contacts BEFORE INSERT OR UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION validate_user_contacts();


-- 5. SCD2
CREATE OR REPLACE PROCEDURE load_scd2_subscriptions()
LANGUAGE plpgsql
AS $$
DECLARE
    r RECORD;
    overlap_count INT;
BEGIN
    FOR r IN SELECT * FROM tmp_subscriptions LOOP
        
        IF r.valid_from >= r.valid_to THEN
            RAISE EXCEPTION 'Дата начала не может быть позже или равна дате окончания';
        END IF;

		IF r.valid_from < CURRENT_DATE THEN
            RAISE EXCEPTION 'Дата начала не может быть в прошлом';
        END IF;

        SELECT COUNT(*) INTO overlap_count
        FROM subscriptions
        WHERE user_id = r.user_id
        AND r.valid_from < valid_to 
        AND r.valid_to > valid_from;

        IF overlap_count > 0 THEN
            RAISE EXCEPTION 'Новая подписка пересекается с существующей подпиской';
        END IF;

        INSERT INTO subscriptions (user_id, valid_from, valid_to)
        VALUES (r.user_id, r.valid_from, r.valid_to);
        
    END LOOP;
    
    DELETE FROM tmp_subscriptions;
END;
$$;