import random
import csv
from faker import Faker
from datetime import datetime, timedelta

Faker.seed(42)
fake = Faker('ru_RU')
random.seed(42)


NUM_USERS = 5000 # Пользователей
NUM_TYPES = 15 # Типов тренировок
NUM_TRAINERS = 30 # Тренеров
NUM_WORKOUTS = 70 # Комплексов тренировок
NUM_SESSIONS = 8000 # Занятий
NUM_LOGS = 100000 # Записей в логах просмотров
SUBSCRIPTION_HISTORY_AVG = 6 # Среднее кол-во подписок на пользователя

users_data = []
types_data = []
trainers_data = []
workouts_data = []
sessions_data = []
subscriptions_data = []
logs_data = []

# 1. Генерация справочников
for i in range(1, NUM_TYPES + 1):
    types_data.append((i, fake.word().capitalize() + " " + random.choice(["Фитнес", "Йога", "Кроссфит", "Кардио"])))

for i in range(1, NUM_TRAINERS + 1):
    trainers_data.append((i, fake.name()))

# 2. Генерация Workouts 
for i in range(1, NUM_WORKOUTS + 1):
    type_id = random.randint(1, NUM_TYPES)
    workouts_data.append((i, type_id, f"Курс {fake.word().capitalize()} {i}"))

# 3. Генерация Sessions
for i in range(1, NUM_SESSIONS + 1):
    workout_id = random.randint(1, NUM_WORKOUTS)
    trainer_id = random.randint(1, NUM_TRAINERS)
    duration = random.randint(600, 3600) # От 10 мин до 1 часа
    sessions_data.append((i, workout_id, trainer_id, f"Урок {i}", duration, f"http://video.host/v/{i}"))

# 4. Генерация Users
invalid_emails_count = 0
for i in range(1, NUM_USERS + 1):
    name = fake.name()
    email = fake.email()
    phone = fake.phone_number()
        
    reg_date = fake.date_between(start_date='-1y', end_date='-1d')
    users_data.append((i, name, email, phone, reg_date))

# 5. Генерация Subscriptions (SCD2 История)
sub_id = 1
user_ids_list = [u[0] for u in users_data]

for user_id in user_ids_list:
    reg_date = next(u[4] for u in users_data if u[0] == user_id)
    num_subs = random.randint(1, SUBSCRIPTION_HISTORY_AVG + 1)
    current_start = reg_date + timedelta(days=random.randint(1, 10))
    
    for _ in range(num_subs):
        valid_from = current_start
        valid_to = valid_from + timedelta(days=30) # Стандартный месяц
        
        subscriptions_data.append((sub_id, user_id, valid_from.strftime('%Y-%m-%d'), valid_to.strftime('%Y-%m-%d')))
        
        sub_id += 1
        # Следующая подписка начинается после окончания предыдущей (или с перерывом)
        gap = random.randint(0, 21)
        current_start = valid_to + timedelta(days=gap + 1)

# 6. Генерация Logs (Просмотры)
today = datetime.now()
one_year_ago = today - timedelta(days=365)

random_dates = []
for _ in range(NUM_LOGS):
    # Случайная дата между 'one_year_ago' и 'today'
    random_date = fake.date_time_between(start_date=one_year_ago, end_date=today)
    random_dates.append(random_date)

random_dates.sort()

for i in range(NUM_LOGS):
    user_id = random.choice(user_ids_list)
    session_id = random.randint(1, NUM_SESSIONS)
    
    # Получаем длительность сессии для расчета watched_duration
    session_duration = next(s[4] for s in sessions_data if s[0] == session_id)
    
    started_at = random_dates[i]
    
    # Watched duration: 
    # 60% смотрят полностью или почти полностью
    # 30% бросают на середине
    # 10% открывают и сразу закрывают (выбросы)
    roll = random.random()
    if roll > 0.4:
        watched = int(session_duration * random.uniform(0.9, 1.0))
    elif roll > 0.1:
        watched = int(session_duration * random.uniform(0.3, 0.8))
    else:
        watched = int(session_duration * random.uniform(0.01, 0.2))
        
    # Добавляем немного шума (кто-то может пересмотреть фрагмент, но не больше 1.1 от длительности)
    if random.random() > 0.95:
        watched = int(watched * 1.1)
        
    logs_data.append((i, user_id, session_id, started_at.strftime('%Y-%m-%d %H:%M:%S'), watched))

def save_csv(filename, data, header):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)
    print(f"Файл {filename} сохранен ({len(data)} строк)")

save_csv('users.csv', users_data, ['user_id', 'name', 'email', 'phone_number', 'registration_dttm'])
save_csv('workout_type.csv', types_data, ['type_id', 'type_name'])
save_csv('trainers.csv', trainers_data, ['trainer_id', 'trainer_name']) 
save_csv('workouts.csv', workouts_data, ['workout_id', 'type_id', 'workout_name'])
save_csv('workout_sessions.csv', sessions_data, ['session_id', 'workout_id', 'trainer_id', 'session_name', 'duration_sec', 'video_link'])
save_csv('subscriptions.csv', subscriptions_data, ['subscription_id', 'user_id', 'valid_from', 'valid_to'])
save_csv('user_session_logs.csv', logs_data, ['log_id', 'user_id', 'session_id', 'started_at', 'watched_duration_sec'])
