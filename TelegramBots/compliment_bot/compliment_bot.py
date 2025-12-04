import telebot
from telebot import types
import sqlite3
import random
import datetime

# Инициализация бота
bot = telebot.TeleBot('YOUR_BOT_TOKEN_HERE')

# Имя файла базы данных
DB_NAME = 'compliment_bot.db'

# База комплиментов
COMPLIMENTS = [
    "Ты сияешь ярче солнца! ☀️",
    "У тебя прекрасное чувство юмора! 😄",
    "Ты вдохновляешь окружающих! ✨",
    "С тобой всегда интересно! 🌟",
    "У тебя доброе сердце! 💖",
    "Ты невероятно талантлив(а)! 🎨",
    "Твоя улыбка заразительна! 😊",
    "Ты прекрасный собеседник! 💬",
    "У тебя отменный вкус! 👌",
    "Ты излучаешь позитивную энергию! ⚡",
    "Твоя мудрость впечатляет! 🧠",
    "Ты красиво мыслишь! 💭",
    "С тобой чувствуешь себя особенным! 💫",
    "Твоя доброта не знает границ! 🌈",
    "Ты превосходно справляешься с задачами! ✅",
    "У тебя чарующий голос! 🎵",
    "Ты отличный друг! 🤝",
    "Твоя креативность восхищает! 🎭",
    "Ты прекрасно выглядишь! 👗",
    "Твоя уверенность вдохновляет! 💪",
    "У тебя золотые руки! 👐",
    "Ты очень проницательный(ая)! 🔍",
    "Твоя энергия заряжает! 🔋",
    "Ты умнее, чем думаешь! 🧩",
    "С тобой можно свернуть горы! ⛰️",
    "Ты прекрасно справляешься с трудностями! 🛡️",
    "У тебя ангельское терпение! 😇",
    "Твои глаза полны добра! 👀",
    "Ты делаешь мир лучше! 🌍",
    "Твой смех - лучшее лекарство! 😂",
]


def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу для истории комплиментов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compliment_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        compliment TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_favorite BOOLEAN DEFAULT 0
    )
    ''')

    # Создаем таблицу для статистики
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        total_compliments INTEGER DEFAULT 0,
        favorite_compliments INTEGER DEFAULT 0,
        last_activity DATETIME
    )
    ''')

    # Создаем таблицу для настроек пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        preferred_gender TEXT DEFAULT 'neutral',
        language TEXT DEFAULT 'ru'
    )
    ''')

    conn.commit()
    conn.close()


def save_compliment(user_id, username, compliment_text, is_favorite=False):
    """Сохранить комплимент в базу данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Сохраняем комплимент в историю
    cursor.execute('''
    INSERT INTO compliment_history (user_id, username, compliment, is_favorite)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, compliment_text, 1 if is_favorite else 0))

    # Обновляем статистику пользователя
    cursor.execute('''
    INSERT OR REPLACE INTO user_stats (user_id, username, total_compliments, favorite_compliments, last_activity)
    VALUES (
        ?, 
        ?, 
        COALESCE((SELECT total_compliments FROM user_stats WHERE user_id = ?), 0) + 1,
        COALESCE((SELECT favorite_compliments FROM user_stats WHERE user_id = ?), 0) + ?,
        CURRENT_TIMESTAMP
    )
    ''', (user_id, username, user_id, user_id, 1 if is_favorite else 0))

    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Получить статистику пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT total_compliments, favorite_compliments, last_activity 
    FROM user_stats 
    WHERE user_id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        total, favorites, last_activity = result
        return {
            'total_compliments': total or 0,
            'favorite_compliments': favorites or 0,
            'last_activity': last_activity
        }
    return {
        'total_compliments': 0,
        'favorite_compliments': 0,
        'last_activity': None
    }


def get_compliment_history(user_id, limit=10):
    """Получить историю комплиментов пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT compliment, timestamp, is_favorite 
    FROM compliment_history 
    WHERE user_id = ? 
    ORDER BY timestamp DESC 
    LIMIT ?
    ''', (user_id, limit))

    history = cursor.fetchall()
    conn.close()
    return history


def get_favorite_compliments(user_id):
    """Получить любимые комплименты пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT compliment, timestamp 
    FROM compliment_history 
    WHERE user_id = ? AND is_favorite = 1 
    ORDER BY timestamp DESC
    ''', (user_id,))

    favorites = cursor.fetchall()
    conn.close()
    return favorites


def toggle_favorite(user_id, compliment_text):
    """Добавить/удалить комплимент из избранного"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Проверяем текущий статус
    cursor.execute('''
    SELECT is_favorite FROM compliment_history 
    WHERE user_id = ? AND compliment = ? 
    ORDER BY timestamp DESC LIMIT 1
    ''', (user_id, compliment_text))

    result = cursor.fetchone()

    if result:
        current_status = result[0]
        new_status = 0 if current_status else 1

        # Обновляем статус в истории
        cursor.execute('''
        UPDATE compliment_history 
        SET is_favorite = ? 
        WHERE id = (
            SELECT id FROM compliment_history 
            WHERE user_id = ? AND compliment = ? 
            ORDER BY timestamp DESC LIMIT 1
        )
        ''', (new_status, user_id, compliment_text))

        # Обновляем статистику
        if new_status:
            cursor.execute('''
            UPDATE user_stats 
            SET favorite_compliments = favorite_compliments + 1 
            WHERE user_id = ?
            ''', (user_id,))
        else:
            cursor.execute('''
            UPDATE user_stats 
            SET favorite_compliments = favorite_compliments - 1 
            WHERE user_id = ?
            ''', (user_id,))

        conn.commit()
        conn.close()
        return new_status == 1
    conn.close()
    return None


def get_random_compliment():
    """Получить случайный комплимент"""
    return random.choice(COMPLIMENTS)


def create_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn_compliment = types.KeyboardButton('💖 Скажи комплимент')
    btn_favorites = types.KeyboardButton('⭐ Любимые комплименты')
    btn_history = types.KeyboardButton('📜 История комплиментов')
    btn_stats = types.KeyboardButton('📊 Моя статистика')

    keyboard.add(btn_compliment, btn_favorites, btn_history, btn_stats)
    return keyboard


def create_compliment_keyboard(compliment_text):
    """Создание клавиатуры после получения комплимента"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    btn_favorite = types.InlineKeyboardButton(
        '⭐ В избранное',
        callback_data=f'fav_{compliment_text}'
    )
    btn_another = types.InlineKeyboardButton(
        '🎲 Ещё комплимент',
        callback_data='another'
    )

    keyboard.add(btn_favorite, btn_another)
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = (
        "💖 *Добро пожаловать в Бот-Комплимент!*\n\n"
        "Я здесь, чтобы поднять вам настроение и сказать приятные слова!\n\n"
        "✨ *Что я умею:*\n"
        "• 💖 Говорить комплименты\n"
        "• ⭐ Сохранять любимые комплименты\n"
        "• 📜 Показывать историю\n"
        "• 📊 Вести статистику\n\n"
        "Используйте кнопки ниже или команды:\n"
        "/compliment - получить комплимент\n"
        "/favorites - любимые комплименты\n"
        "/history - история\n"
        "/stats - статистика\n"
        "/clear - очистить историю"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['compliment'])
def send_compliment_command(message):
    """Отправка комплимента по команде"""
    send_compliment(message)


def send_compliment(message):
    """Отправка случайного комплимента"""
    user = message.from_user
    compliment = get_random_compliment()

    # Сохраняем комплимент в историю
    save_compliment(user.id, user.username, compliment)

    # Отправляем комплимент с инлайн-кнопками
    bot.send_message(
        message.chat.id,
        f"💖 *Для тебя:*\n\n{compliment}",
        parse_mode='Markdown',
        reply_markup=create_compliment_keyboard(compliment)
    )


@bot.message_handler(commands=['favorites'])
def show_favorites_command(message):
    """Показать избранные комплименты"""
    show_favorites(message)


def show_favorites(message):
    """Показать избранные комплименты пользователя"""
    user = message.from_user
    favorites = get_favorite_compliments(user.id)

    if favorites:
        favorites_text = "⭐ *Ваши любимые комплименты:*\n\n"
        for i, (compliment, timestamp) in enumerate(favorites, 1):
            date_str = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
            favorites_text += f"{i}. {compliment}\n   📅 {date_str}\n\n"

        # Добавляем кнопку очистки
        keyboard = types.InlineKeyboardMarkup()
        btn_clear = types.InlineKeyboardButton('🗑️ Очистить избранное', callback_data='clear_favorites')
        keyboard.add(btn_clear)

        bot.send_message(
            message.chat.id,
            favorites_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        bot.send_message(
            message.chat.id,
            "У вас пока нет любимых комплиментов.\n"
            "Нажимайте ⭐ на понравившихся комплиментах!",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(commands=['history'])
def show_history_command(message):
    """Показать историю комплиментов"""
    show_history(message)


def show_history(message):
    """Показать историю комплиментов пользователя"""
    user = message.from_user
    history = get_compliment_history(user.id, limit=15)

    if history:
        history_text = "📜 *Последние комплименты:*\n\n"
        for i, (compliment, timestamp, is_favorite) in enumerate(history, 1):
            date_str = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
            star = "⭐ " if is_favorite else ""
            history_text += f"{i}. {star}{compliment}\n   🕒 {date_str}\n\n"

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
            "История комплиментов пуста.\n"
            "Получите свой первый комплимент! 💖",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(commands=['stats'])
def show_stats_command(message):
    """Показать статистику"""
    show_stats(message)


def show_stats(message):
    """Показать статистику пользователя"""
    user = message.from_user
    stats = get_user_stats(user.id)

    if stats['last_activity']:
        last_active = datetime.datetime.strptime(stats['last_activity'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
    else:
        last_active = "никогда"

    stats_text = (
        f"📊 *Ваша статистика:*\n\n"
        f"💖 Всего комплиментов: *{stats['total_compliments']}*\n"
        f"⭐ Любимых комплиментов: *{stats['favorite_compliments']}*\n"
        f"📅 Последняя активность: {last_active}\n\n"
        f"Продолжайте радовать себя комплиментами! ✨"
    )

    bot.send_message(
        message.chat.id,
        stats_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['clear'])
def clear_history_prompt(message):
    """Запрос на очистку истории"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_history = types.InlineKeyboardButton('🗑️ Очистить историю', callback_data='clear_history')
    btn_favorites = types.InlineKeyboardButton('⭐ Очистить избранное', callback_data='clear_favorites')
    btn_all = types.InlineKeyboardButton('💥 Очистить всё', callback_data='clear_all')
    keyboard.add(btn_history, btn_favorites, btn_all)

    bot.send_message(
        message.chat.id,
        "Что вы хотите очистить?",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка callback-запросов от инлайн-кнопок"""
    user_id = call.from_user.id

    if call.data.startswith('fav_'):
        # Добавление/удаление из избранного
        compliment_text = call.data[4:]  # Убираем префикс 'fav_'
        result = toggle_favorite(user_id, compliment_text)

        if result is not None:
            if result:
                bot.answer_callback_query(call.id, "✅ Добавлено в избранное!")
            else:
                bot.answer_callback_query(call.id, "❌ Удалено из избранного")
        else:
            bot.answer_callback_query(call.id, "Комплимент не найден")

    elif call.data == 'another':
        # Запрос еще одного комплимента
        compliment = get_random_compliment()
        save_compliment(user_id, call.from_user.username, compliment)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"💖 *Для тебя:*\n\n{compliment}",
            parse_mode='Markdown',
            reply_markup=create_compliment_keyboard(compliment)
        )

    elif call.data == 'clear_history':
        # Очистка истории
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM compliment_history WHERE user_id = ?', (user_id,))
        cursor.execute('UPDATE user_stats SET total_compliments = 0, favorite_compliments = 0 WHERE user_id = ?',
                       (user_id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "✅ История очищена!")
        bot.send_message(
            call.message.chat.id,
            "История комплиментов успешно очищена!",
            reply_markup=create_main_keyboard()
        )

    elif call.data == 'clear_favorites':
        # Очистка избранного
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('UPDATE compliment_history SET is_favorite = 0 WHERE user_id = ?', (user_id,))
        cursor.execute('UPDATE user_stats SET favorite_compliments = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "✅ Избранное очищено!")
        bot.send_message(
            call.message.chat.id,
            "Избранные комплименты успешно очищены!",
            reply_markup=create_main_keyboard()
        )

    elif call.data == 'clear_all':
        # Полная очистка
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM compliment_history WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_stats WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "✅ Всё очищено!")
        bot.send_message(
            call.message.chat.id,
            "✅ Вся ваша история и статистика очищены!\nНачните с чистого листа!",
            reply_markup=create_main_keyboard()
        )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработка текстовых сообщений"""
    text = message.text

    if text == '💖 Скажи комплимент':
        send_compliment(message)

    elif text == '⭐ Любимые комплименты':
        show_favorites(message)

    elif text == '📜 История комплиментов':
        show_history(message)

    elif text == '📊 Моя статистика':
        show_stats(message)

    else:
        # Если сообщение не распознано
        bot.send_message(
            message.chat.id,
            "Используйте кнопки или команды:\n"
            "/start - начать работу\n"
            "/compliment - получить комплимент\n"
            "/favorites - любимые комплименты\n"
            "/history - история\n"
            "/stats - статистика\n"
            "/clear - очистить историю",
            reply_markup=create_main_keyboard()
        )


if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()

    print("💖 Бот-Комплимент запущен...")
    print(f"📁 База данных: {DB_NAME}")
    print(f"📊 Количество комплиментов: {len(COMPLIMENTS)}")

    # Запускаем бота
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")