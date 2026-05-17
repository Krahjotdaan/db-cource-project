import random
import csv
from faker import Faker
from datetime import datetime, timedelta

Faker.seed(42)
fake = Faker('ru_RU')
random.seed(42)

# Конфигурация
NUM_USERS = 5000
NUM_TYPES = 15
NUM_TRAINERS = 30
NUM_WORKOUTS = 70
NUM_SESSIONS = 8000
NUM_LOGS = 100000

# 95% пользователей имеют хотя бы одну подписку
PERCENT_USERS_WITH_SUBSCRIPTION = 95

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
    duration = random.randint(600, 3600)
    sessions_data.append((i, workout_id, trainer_id, f"Урок {i}", duration, f"http://video.host/v/{i}"))

# Словарь для быстрого доступа к длительности сессии
session_duration_dict = {s[0]: s[4] for s in sessions_data}

# 4. Генерация Users и Subscriptions
sub_id = 1
users_info = []  # (user_id, reg_date, список периодов подписок)

print("Генерация пользователей и подписок...")

for i in range(1, NUM_USERS + 1):
    name = fake.name()
    email = fake.email()
    phone = fake.phone_number()
    reg_date = fake.date_between(start_date='-1y', end_date='-1d')
    
    users_data.append((i, name, email, phone, reg_date))
    
    # Определяем, будет ли пользователь иметь подписки (95%)
    has_subscription = random.random() < (PERCENT_USERS_WITH_SUBSCRIPTION / 100)
    
    subscription_periods = []
    
    if has_subscription:
        # Количество подписок у пользователя (от 1 до 6)
        num_subs = random.randint(1, 6)
        current_start = reg_date + timedelta(days=random.randint(1, 10))
        
        for _ in range(num_subs):
            valid_from = current_start
            valid_to = valid_from + timedelta(days=30)
            
            subscriptions_data.append((sub_id, i, valid_from.strftime('%Y-%m-%d'), valid_to.strftime('%Y-%m-%d')))
            subscription_periods.append((valid_from, valid_to))
            sub_id += 1
            
            # Перерыв между подписками от 0 до 21 дня
            gap = random.randint(0, 21)
            current_start = valid_to + timedelta(days=gap + 1)
    
    users_info.append((i, reg_date, subscription_periods))

users_with_subs = len([u for u in users_info if u[2]])
users_without_subs = NUM_USERS - users_with_subs
print(f"  - Пользователей с подписками: {users_with_subs} ({(users_with_subs/NUM_USERS)*100:.1f}%)")
print(f"  - Пользователей без подписок: {users_without_subs} ({(users_without_subs/NUM_USERS)*100:.1f}%)")
print(f"  - Всего подписок: {len(subscriptions_data)}")

# 5. Генерация Logs (только в период действия подписки и после регистрации)
print("Генерация логов просмотров...")

today = datetime.now()
one_year_ago = today - timedelta(days=365)

# Собираем всех пользователей с подписками и их активные периоды
active_users = []
for user_id, reg_date, periods in users_info:
    if periods:  # только пользователи с подписками
        for valid_from, valid_to in periods:
            active_users.append((user_id, reg_date, valid_from, valid_to))

log_id = 0
generated_logs = 0

# Генерируем логи, равномерно распределяя по активным периодам
while generated_logs < NUM_LOGS:
    # Выбираем случайный активный период
    user_id, reg_date, valid_from, valid_to = random.choice(active_users)
    
    # Генерируем дату в пределах периода подписки
    # Но не раньше даты регистрации (хотя valid_from уже гарантирует это)
    start_date = max(valid_from, reg_date)
    if start_date > valid_to:
        continue
    
    # Случайная дата в периоде подписки
    days_range = (valid_to - start_date).days
    if days_range <= 0:
        continue
    
    random_days = random.randint(0, days_range)
    started_at = datetime.combine(start_date + timedelta(days=random_days), 
                                   datetime.min.time()) + timedelta(seconds=random.randint(0, 86399))
    
    # Выбираем случайную сессию
    session_id = random.randint(1, NUM_SESSIONS)
    session_duration = session_duration_dict[session_id]
    
    # Генерация watched_duration с реалистичным распределением
    roll = random.random()
    if roll > 0.4:  # 60% - почти полный просмотр
        watched = int(session_duration * random.uniform(0.9, 1.0))
    elif roll > 0.1:  # 30% - бросают на середине
        watched = int(session_duration * random.uniform(0.3, 0.8))
    else:  # 10% - сразу закрывают
        watched = int(session_duration * random.uniform(0.01, 0.2))
    
    # 5% пересматривают фрагмент (может быть >100%)
    if random.random() > 0.95:
        watched = int(watched * random.uniform(1.01, 1.1))
    
    logs_data.append((log_id, user_id, session_id, started_at.strftime('%Y-%m-%d %H:%M:%S'), watched))
    generated_logs += 1
    log_id += 1
    
print(f"  - Готово! Сгенерировано {generated_logs} логов")

# 6. Сохранение CSV
def save_csv(filename, data, header):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)
    print(f"Файл {filename} сохранен ({len(data)} строк)")

save_csv('users.csv', users_data, ['user_id', 'user_name', 'email', 'phone_number', 'registration_dttm'])
save_csv('workout_type.csv', types_data, ['type_id', 'type_name'])
save_csv('trainers.csv', trainers_data, ['trainer_id', 'trainer_name']) 
save_csv('workouts.csv', workouts_data, ['workout_id', 'type_id', 'workout_name'])
save_csv('workout_sessions.csv', sessions_data, ['session_id', 'workout_id', 'trainer_id', 'session_name', 'duration_sec', 'video_link'])
save_csv('subscriptions.csv', subscriptions_data, ['subscription_id', 'user_id', 'valid_from', 'valid_to'])
save_csv('user_session_logs.csv', logs_data, ['log_id', 'user_id', 'session_id', 'started_at', 'watched_duration_sec'])

print("\n=== Генерация завершена ===")
print(f"Пользователей: {len(users_data)}")
print(f"  - С подписками: {users_with_subs}")
print(f"  - Без подписок: {users_without_subs}")
print(f"Подписок: {len(subscriptions_data)}")
print(f"Логов просмотров: {len(logs_data)}")
print("\nПроверка целостности:")
if logs_data:
    # Проверяем, что все логи принадлежат пользователям с подписками
    users_with_subs_ids = [u[0] for u in users_info if u[2]]
    all_logs_valid = all(l[1] in users_with_subs_ids for l in logs_data)
    print(f"  - Логи только у пользователей с подписками: {all_logs_valid}")
    
    # Дополнительная проверка: уникальность пользователей в логах
    unique_users_in_logs = len(set(l[1] for l in logs_data))
    print(f"  - Уникальных пользователей в логах: {unique_users_in_logs}")
else:
    print(f"  - Логи только у пользователей с подписками: N/A (логи не сгенерированы)")
    print(f"  - Проверьте, что есть активные периоды подписок для генерации логов")