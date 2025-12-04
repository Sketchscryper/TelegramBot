import telebot
from telebot import types
import sqlite3
import random
import datetime
import json

# Инициализация бота
bot = telebot.TeleBot('YOUR_BOT_TOKEN_HERE')

# Имя файла базы данных
DB_NAME = 'weather_bot.db'

# Список доступных городов с координатами
CITIES = {
    'Москва': {
        'lat': 55.7558,
        'lon': 37.6173,
        'timezone': 'Europe/Moscow'
    },
    'Санкт-Петербург': {
        'lat': 59.9343,
        'lon': 30.3351,
        'timezone': 'Europe/Moscow'
    },
    'Сочи': {
        'lat': 43.5855,
        'lon': 39.7231,
        'timezone': 'Europe/Moscow'
    },
    'Екатеринбург': {
        'lat': 56.8389,
        'lon': 60.6057,
        'timezone': 'Asia/Yekaterinburg'
    },
    'Новосибирск': {
        'lat': 55.0084,
        'lon': 82.9357,
        'timezone': 'Asia/Novosibirsk'
    },
    'Казань': {
        'lat': 55.8304,
        'lon': 49.0661,
        'timezone': 'Europe/Moscow'
    },
    'Нижний Новгород': {
        'lat': 56.2965,
        'lon': 43.9361,
        'timezone': 'Europe/Moscow'
    },
    'Краснодар': {
        'lat': 45.0355,
        'lon': 38.9753,
        'timezone': 'Europe/Moscow'
    },
    'Владивосток': {
        'lat': 43.1332,
        'lon': 131.9113,
        'timezone': 'Asia/Vladivostok'
    },
    'Калининград': {
        'lat': 54.7104,
        'lon': 20.4522,
        'timezone': 'Europe/Kaliningrad'
    }
}

# Типы погоды с эмодзи и описаниями
WEATHER_TYPES = [
    {
        'type': 'Ясно ☀️',
        'temp_range': (15, 30),
        'description': 'Прекрасный солнечный день! Идеально для прогулок.'
    },
    {
        'type': 'Переменная облачность ⛅',
        'temp_range': (10, 25),
        'description': 'Облака чередуются с солнцем. Не забудьте зонт на всякий случай.'
    },
    {
        'type': 'Пасмурно ☁️',
        'temp_range': (8, 20),
        'description': 'Сплошная облачность. Хороший день для домашних дел.'
    },
    {
        'type': 'Дождь 🌧️',
        'temp_range': (5, 18),
        'description': 'Идет дождь. Возьмите зонт и наденьте непромокаемую обувь.'
    },
    {
        'type': 'Гроза ⛈️',
        'temp_range': (12, 25),
        'description': 'Гроза с ливнем. Будьте осторожны на улице.'
    },
    {
        'type': 'Снег ❄️',
        'temp_range': (-15, 0),
        'description': 'Идет снег. Тепло одевайтесь и будьте аккуратны на дорогах.'
    },
    {
        'type': 'Туман 🌫️',
        'temp_range': (0, 15),
        'description': 'Туманная погода. Будьте внимательны за рулем.'
    },
    {
        'type': 'Ветрено 💨',
        'temp_range': (5, 20),
        'description': 'Сильный ветер. Закрепите легкие предметы на улице.'
    },
    {
        'type': 'Жарко 🔥',
        'temp_range': (30, 40),
        'description': 'Очень жарко. Пейте больше воды и избегайте прямых солнечных лучей.'
    },
    {
        'type': 'Морозно 🥶',
        'temp_range': (-30, -10),
        'description': 'Сильный мороз. Тепло одевайтесь и сократите время пребывания на улице.'
    }
]

# Рекомендации по одежде
CLOTHING_RECOMMENDATIONS = {
    'Ясно ☀️': ['👕 Футболка', '🩳 Шорты/легкие брюки', '🧢 Кепка/панама', '🕶️ Солнцезащитные очки'],
    'Переменная облачность ⛅': ['👕 Футболка/рубашка', '👖 Легкие брюки', '🧥 Легкая куртка на вечер'],
    'Пасмурно ☁️': ['👕 Рубашка/свитер', '👖 Брюки/джинсы', '🧥 Куртка/ветровка'],
    'Дождь 🌧️': ['🧥 Водонепроницаемая куртка', '👖 Непромокаемые брюки', '☂️ Зонт', '👟 Водостойкая обувь'],
    'Гроза ⛈️': ['🧥 Непромокаемая одежда', '☂️ Зонт', '👟 Водостойкая обувь', '⚠️ Избегайте открытых пространств'],
    'Снег ❄️': ['🧥 Теплая зимняя куртка', '🧤 Перчатки', '🧣 Шарф', '🎩 Теплая шапка', '👢 Зимняя обувь'],
    'Туман 🌫️': ['🧥 Куртка/ветровка', '👖 Брюки', '⚠️ Светоотражающие элементы для безопасности'],
    'Ветрено 💨': ['🧥 Ветровка/куртка', '👖 Брюки', '🧣 Шарф для защиты шеи'],
    'Жарко 🔥': ['👕 Легкая футболка/майка', '🩳 Шорты', '🧢 Кепка/панама', '🕶️ Солнцезащитные очки', '💧 Бутылка воды'],
    'Морозно 🥶': ['🧥 Теплая пуховая куртка', '🧣 Шарф', '🧤 Термоперчатки', '🎩 Теплая шапка', '👢 Утепленная обувь',
                  '👖 Термобелье']
}


def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу для избранных городов пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_favorites (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        favorite_city TEXT,
        favorite_city_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу для истории запросов погоды
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        city TEXT NOT NULL,
        weather_data TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу для статистики
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        total_requests INTEGER DEFAULT 0,
        favorite_city TEXT,
        last_request DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу для настроек пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        units TEXT DEFAULT 'celsius',
        notifications_enabled BOOLEAN DEFAULT 0,
        notification_time TEXT DEFAULT '08:00'
    )
    ''')

    conn.commit()
    conn.close()


def save_weather_request(user_id, username, city, weather_data):
    """Сохранить запрос погоды в историю"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Сохраняем запрос в историю
    cursor.execute('''
    INSERT INTO weather_history (user_id, username, city, weather_data)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, city, json.dumps(weather_data)))

    # Обновляем статистику пользователя
    cursor.execute('''
    INSERT OR REPLACE INTO user_stats (user_id, username, total_requests, favorite_city, last_request)
    VALUES (
        ?, 
        ?, 
        COALESCE((SELECT total_requests FROM user_stats WHERE user_id = ?), 0) + 1,
        COALESCE((SELECT favorite_city FROM user_stats WHERE user_id = ?), ?),
        CURRENT_TIMESTAMP
    )
    ''', (user_id, username, user_id, user_id, city))

    conn.commit()
    conn.close()


def set_favorite_city(user_id, username, city):
    """Установить избранный город пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    city_data = json.dumps(CITIES.get(city, {}))

    cursor.execute('''
    INSERT OR REPLACE INTO user_favorites (user_id, username, favorite_city, favorite_city_data, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, username, city, city_data))

    # Также обновляем в статистике
    cursor.execute('''
    UPDATE user_stats SET favorite_city = ? WHERE user_id = ?
    ''', (city, user_id))

    conn.commit()
    conn.close()


def get_favorite_city(user_id):
    """Получить избранный город пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT favorite_city FROM user_favorites WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def get_user_stats(user_id):
    """Получить статистику пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT total_requests, favorite_city, last_request, created_at 
    FROM user_stats 
    WHERE user_id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        total_requests, favorite_city, last_request, created_at = result
        return {
            'total_requests': total_requests or 0,
            'favorite_city': favorite_city or 'Не выбран',
            'last_request': last_request,
            'created_at': created_at
        }
    return {
        'total_requests': 0,
        'favorite_city': 'Не выбран',
        'last_request': None,
        'created_at': None
    }


def get_weather_history(user_id, limit=5):
    """Получить историю запросов погоды"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT city, weather_data, timestamp 
    FROM weather_history 
    WHERE user_id = ? 
    ORDER BY timestamp DESC 
    LIMIT ?
    ''', (user_id, limit))

    history = cursor.fetchall()
    conn.close()

    formatted_history = []
    for city, weather_json, timestamp in history:
        weather_data = json.loads(weather_json)
        formatted_history.append({
            'city': city,
            'weather': weather_data,
            'timestamp': timestamp
        })

    return formatted_history


def generate_weather(city):
    """Сгенерировать случайную погоду для города"""
    weather_type = random.choice(WEATHER_TYPES)
    temp_min, temp_max = weather_type['temp_range']
    temperature = random.randint(temp_min, temp_max)

    # Добавляем сезонные корректировки
    month = datetime.datetime.now().month
    if month in [12, 1, 2]:  # Зима
        temperature = max(temperature - 10, -35)
    elif month in [6, 7, 8]:  # Лето
        temperature = min(temperature + 5, 40)

    # Добавляем временные корректировки
    hour = datetime.datetime.now().hour
    if hour >= 22 or hour <= 6:  # Ночь
        temperature -= random.randint(3, 8)

    # Влажность и давление
    humidity = random.randint(30, 90)
    pressure = random.randint(720, 780)
    wind_speed = random.randint(0, 15)

    # Определяем направление ветра
    wind_directions = ['Северный', 'Северо-восточный', 'Восточный', 'Юго-восточный',
                       'Южный', 'Юго-западный', 'Западный', 'Северо-западный']
    wind_direction = random.choice(wind_directions)

    # Определяем ощущаемую температуру
    feels_like = temperature
    if wind_speed > 10:
        feels_like -= random.randint(2, 5)
    if humidity > 80:
        feels_like += random.randint(1, 3) if temperature > 20 else 0

    weather_data = {
        'city': city,
        'temperature': temperature,
        'feels_like': feels_like,
        'weather_type': weather_type['type'],
        'description': weather_type['description'],
        'humidity': humidity,
        'pressure': pressure,
        'wind_speed': wind_speed,
        'wind_direction': wind_direction,
        'clothing': CLOTHING_RECOMMENDATIONS.get(weather_type['type'].split(' ')[0], []),
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    return weather_data


def format_weather_message(weather_data):
    """Форматировать данные о погоде в читаемое сообщение"""
    city_info = CITIES.get(weather_data['city'], {})

    message = f"🌤️ *Погода в {weather_data['city']}*\n\n"
    message += f"📍 *Температура:* {weather_data['temperature']}°C\n"
    message += f"🌡️ *Ощущается как:* {weather_data['feels_like']}°C\n"
    message += f"🌦️ *Состояние:* {weather_data['weather_type']}\n"
    message += f"💧 *Влажность:* {weather_data['humidity']}%\n"
    message += f"📊 *Давление:* {weather_data['pressure']} мм рт.ст.\n"
    message += f"💨 *Ветер:* {weather_data['wind_speed']} м/с, {weather_data['wind_direction']}\n\n"

    message += f"📝 *{weather_data['description']}*\n\n"

    if weather_data['clothing']:
        message += "👕 *Рекомендации по одежде:*\n"
        for item in weather_data['clothing'][:5]:  # Показываем первые 5 рекомендаций
            message += f"• {item}\n"

    # Добавляем интересные факты
    facts = [
        f"\n🌅 *Восход солнца:* {random.randint(5, 8)}:{random.randint(0, 59):02d}",
        f"🌇 *Закат солнца:* {random.randint(18, 22)}:{random.randint(0, 59):02d}",
        f"📈 *УФ-индекс:* {random.randint(1, 10)}"
    ]

    if 'lat' in city_info:
        message += random.choice(facts)

    message += f"\n\n🕒 *Обновлено:* {weather_data['timestamp'][11:16]}"

    return message


def create_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    # Первые 4 популярных города
    btn_moscow = types.KeyboardButton('🏛️ Москва')
    btn_spb = types.KeyboardButton('🏰 Санкт-Петербург')
    btn_sochi = types.KeyboardButton('🏖️ Сочи')
    btn_ekb = types.KeyboardButton('⛰️ Екатеринбург')

    btn_favorites = types.KeyboardButton('⭐ Избранное')
    btn_all_cities = types.KeyboardButton('🌍 Все города')
    btn_stats = types.KeyboardButton('📊 Статистика')
    btn_history = types.KeyboardButton('📜 История')

    row1 = [btn_moscow, btn_spb]
    row2 = [btn_sochi, btn_ekb]
    row3 = [btn_favorites, btn_all_cities]
    row4 = [btn_stats, btn_history]

    keyboard.add(*row1)
    keyboard.add(*row2)
    keyboard.add(*row3)
    keyboard.add(*row4)

    return keyboard


def create_cities_keyboard():
    """Создание клавиатуры со всеми городами"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    # Создаем кнопки для всех городов
    buttons = []
    for city in CITIES.keys():
        # Добавляем эмодзи в зависимости от города
        if city == 'Москва':
            btn = types.KeyboardButton(f'🏛️ {city}')
        elif city == 'Санкт-Петербург':
            btn = types.KeyboardButton(f'🏰 {city}')
        elif city == 'Сочи':
            btn = types.KeyboardButton(f'🏖️ {city}')
        elif city == 'Владивосток':
            btn = types.KeyboardButton(f'🌊 {city}')
        elif city == 'Калининград':
            btn = types.KeyboardButton(f'🏰 {city}')
        else:
            btn = types.KeyboardButton(f'🏙️ {city}')
        buttons.append(btn)

    # Добавляем кнопку "Назад"
    btn_back = types.KeyboardButton('🔙 Назад')
    buttons.append(btn_back)

    # Добавляем кнопки группами по 2
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.add(buttons[i], buttons[i + 1])
        else:
            keyboard.add(buttons[i])

    return keyboard


def create_weather_keyboard(city_name):
    """Создание инлайн-клавиатуры для погоды"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    btn_refresh = types.InlineKeyboardButton('🔄 Обновить', callback_data=f'refresh_{city_name}')
    btn_favorite = types.InlineKeyboardButton('⭐ В избранное', callback_data=f'fav_{city_name}')
    btn_forecast = types.InlineKeyboardButton('📅 Прогноз на день', callback_data=f'forecast_{city_name}')
    btn_details = types.InlineKeyboardButton('📊 Подробности', callback_data=f'details_{city_name}')

    keyboard.add(btn_refresh, btn_favorite, btn_forecast, btn_details)
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = (
        "🌤️ *Добро пожаловать в Weather Bot!*\n\n"
        "Я помогу вам узнать погоду в разных городах России.\n\n"
        "✨ *Доступные возможности:*\n"
        "• 🌤️ Проверить погоду в любом городе\n"
        "• ⭐ Сохранить любимый город\n"
        "• 📊 Просмотреть статистику\n"
        "• 📜 Посмотреть историю запросов\n\n"
        "Используйте кнопки ниже или команды:\n"
        "/weather <город> - погода в городе\n"
        "/favorites - избранный город\n"
        "/stats - статистика\n"
        "/history - история запросов\n"
        "/cities - список всех городов"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['weather'])
def weather_command(message):
    """Команда для запроса погоды"""
    try:
        city = message.text.split(' ', 1)[1].strip()
        if city in CITIES:
            send_weather(message, city)
        else:
            bot.send_message(
                message.chat.id,
                f"Город '{city}' не найден в списке. Используйте /cities чтобы увидеть все доступные города.",
                reply_markup=create_main_keyboard()
            )
    except IndexError:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, укажите город. Например: /weather Москва",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(commands=['favorites'])
def favorites_command(message):
    """Показать избранный город"""
    user = message.from_user
    favorite = get_favorite_city(user.id)

    if favorite:
        bot.send_message(
            message.chat.id,
            f"⭐ Ваш избранный город: *{favorite}*\n\n"
            f"Нажмите на кнопку города, чтобы узнать погоду.",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "У вас пока нет избранного города.\n"
            "Нажмите ⭐ на погоде в любом городе, чтобы добавить его в избранное.",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Показать статистику"""
    show_stats(message)


@bot.message_handler(commands=['history'])
def history_command(message):
    """Показать историю запросов"""
    show_history(message)


@bot.message_handler(commands=['cities'])
def cities_command(message):
    """Показать список всех городов"""
    bot.send_message(
        message.chat.id,
        "🌍 *Доступные города:*\n\n" + "\n".join([f"• {city}" for city in CITIES.keys()]),
        parse_mode='Markdown',
        reply_markup=create_cities_keyboard()
    )


def send_weather(message, city_name):
    """Отправить погоду для указанного города"""
    user = message.from_user

    # Генерируем погоду
    weather_data = generate_weather(city_name)

    # Сохраняем запрос в историю
    save_weather_request(user.id, user.username, city_name, weather_data)

    # Форматируем сообщение
    weather_message = format_weather_message(weather_data)

    # Отправляем сообщение с инлайн-кнопками
    bot.send_message(
        message.chat.id,
        weather_message,
        parse_mode='Markdown',
        reply_markup=create_weather_keyboard(city_name)
    )


def show_stats(message):
    """Показать статистику пользователя"""
    user = message.from_user
    stats = get_user_stats(user.id)

    stats_text = f"📊 *Ваша статистика:*\n\n"
    stats_text += f"🌤️ Всего запросов погоды: *{stats['total_requests']}*\n"
    stats_text += f"⭐ Избранный город: *{stats['favorite_city']}*\n"

    if stats['last_request']:
        last_request = datetime.datetime.strptime(stats['last_request'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
        stats_text += f"🕒 Последний запрос: {last_request}\n"

    if stats['created_at']:
        created_at = datetime.datetime.strptime(stats['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
        stats_text += f"📅 Используете бота с: {created_at}\n"

    bot.send_message(
        message.chat.id,
        stats_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


def show_history(message):
    """Показать историю запросов погоды"""
    user = message.from_user
    history = get_weather_history(user.id, limit=5)

    if history:
        history_text = "📜 *Последние запросы погоды:*\n\n"
        for i, item in enumerate(history, 1):
            time_str = datetime.datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
            history_text += f"{i}. *{item['city']}* - {item['weather']['temperature']}°C\n"
            history_text += f"   {item['weather']['weather_type']} | {time_str}\n\n"

        # Добавляем кнопку очистки
        keyboard = types.InlineKeyboardMarkup()
        btn_clear = types.InlineKeyboardButton('🗑️ Очистить историю', callback_data='clear_history')
        keyboard.add(btn_clear)

        bot.send_message(
            message.chat.id,
            history_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        bot.send_message(
            message.chat.id,
            "История запросов погоды пуста.\n"
            "Сделайте свой первый запрос погоды! 🌤️",
            reply_markup=create_main_keyboard()
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка callback-запросов от инлайн-кнопок"""
    user = call.from_user

    if call.data.startswith('refresh_'):
        # Обновить погоду
        city_name = call.data[8:]
        weather_data = generate_weather(city_name)
        save_weather_request(user.id, user.username, city_name, weather_data)

        weather_message = format_weather_message(weather_data)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=weather_message,
            parse_mode='Markdown',
            reply_markup=create_weather_keyboard(city_name)
        )
        bot.answer_callback_query(call.id, "✅ Погода обновлена!")

    elif call.data.startswith('fav_'):
        # Добавить в избранное
        city_name = call.data[4:]
        set_favorite_city(user.id, user.username, city_name)
        bot.answer_callback_query(call.id, f"✅ {city_name} добавлен в избранное!")

    elif call.data.startswith('forecast_'):
        # Показать прогноз на день
        city_name = call.data[9:]

        forecast_text = f"📅 *Прогноз на день для {city_name}:*\n\n"

        times = ['Утро', 'День', 'Вечер', 'Ночь']
        for time in times:
            temp = random.randint(-5, 25)  # Случайная температура для времени суток
            condition = random.choice(WEATHER_TYPES)
            forecast_text += f"🌅 *{time}:* {temp}°C, {condition['type']}\n"

        forecast_text += "\n⚠️ *Примечание:* Это случайно сгенерированный прогноз!"

        bot.send_message(
            call.message.chat.id,
            forecast_text,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith('details_'):
        # Показать подробности
        city_name = call.data[8:]
        city_info = CITIES.get(city_name, {})

        details_text = f"📊 *Подробности о {city_name}:*\n\n"

        if city_info:
            details_text += f"📍 *Координаты:* {city_info['lat']:.4f}, {city_info['lon']:.4f}\n"
            details_text += f"🌐 *Часовой пояс:* {city_info['timezone']}\n"

        # Добавляем интересные факты
        facts = [
            f"Население: {random.randint(500000, 15000000):,} человек",
            f"Высота над уровнем моря: {random.randint(0, 500)} м",
            f"Среднегодовая температура: {random.randint(0, 10)}°C"
        ]

        details_text += f"📈 *Интересные факты:*\n"
        for fact in random.sample(facts, 2):
            details_text += f"• {fact}\n"

        bot.send_message(
            call.message.chat.id,
            details_text,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)

    elif call.data == 'clear_history':
        # Очистка истории
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM weather_history WHERE user_id = ?', (user.id,))
        cursor.execute('UPDATE user_stats SET total_requests = 0 WHERE user_id = ?', (user.id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "✅ История очищена!")
        bot.send_message(
            call.message.chat.id,
            "История запросов погоды успешно очищена!",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработка текстовых сообщений"""
    text = message.text
    user = message.from_user

    # Убираем эмодзи для сравнения
    clean_text = text
    for emoji in ['🏛️', '🏰', '🏖️', '⛰️', '🌊', '🏙️']:
        clean_text = clean_text.replace(emoji, '').strip()

    if text == '🏛️ Москва' or clean_text == 'Москва':
        send_weather(message, 'Москва')

    elif text == '🏰 Санкт-Петербург' or clean_text == 'Санкт-Петербург':
        send_weather(message, 'Санкт-Петербург')

    elif text == '🏖️ Сочи' or clean_text == 'Сочи':
        send_weather(message, 'Сочи')

    elif text == '⛰️ Екатеринбург' or clean_text == 'Екатеринбург':
        send_weather(message, 'Екатеринбург')

    elif text == '⭐ Избранное':
        favorite = get_favorite_city(user.id)
        if favorite:
            send_weather(message, favorite)
        else:
            bot.send_message(
                message.chat.id,
                "У вас пока нет избранного города.\n"
                "Нажмите ⭐ на погоде в любом городе, чтобы добавить его в избранное.",
                reply_markup=create_main_keyboard()
            )

    elif text == '🌍 Все города':
        bot.send_message(
            message.chat.id,
            "Выберите город из списка:",
            reply_markup=create_cities_keyboard()
        )

    elif text == '📊 Статистика':
        show_stats(message)

    elif text == '📜 История':
        show_history(message)

    elif text == '🔙 Назад':
        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=create_main_keyboard()
        )

    elif clean_text in CITIES:
        # Если текст соответствует любому городу из списка
        send_weather(message, clean_text)

    else:
        # Если сообщение не распознано
        bot.send_message(
            message.chat.id,
            "Используйте кнопки или команды:\n"
            "/start - начать работу\n"
            "/weather <город> - погода в городе\n"
            "/favorites - избранный город\n"
            "/stats - статистика\n"
            "/history - история запросов\n"
            "/cities - список всех городов",
            reply_markup=create_main_keyboard()
        )


if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()

    print("🌤️ Weather Bot запущен...")
    print(f"📁 База данных: {DB_NAME}")
    print(f"🏙️ Доступно городов: {len(CITIES)}")

    # Запускаем бота
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")