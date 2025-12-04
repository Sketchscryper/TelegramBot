import telebot
from telebot import types
import sqlite3
import os

# Инициализация бота
bot = telebot.TeleBot('YOUR_BOT_TOKEN_HERE')

# Имя файла базы данных
DB_NAME = 'counter_bot.db'


def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_counters (
        user_id INTEGER PRIMARY KEY,
        count INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()


def get_user_count(user_id):
    """Получить текущее значение счетчика пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT count FROM user_counters WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    else:
        # Если пользователя нет в базе, создаем запись
        set_user_count(user_id, 0)
        return 0


def set_user_count(user_id, count):
    """Установить значение счетчика пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT OR REPLACE INTO user_counters (user_id, count) 
    VALUES (?, ?)
    ''', (user_id, count))

    conn.commit()
    conn.close()


def increment_user_count(user_id):
    """Увеличить счетчик пользователя на 1"""
    current_count = get_user_count(user_id)
    new_count = current_count + 1
    set_user_count(user_id, new_count)
    return new_count


def reset_user_count(user_id):
    """Сбросить счетчик пользователя"""
    set_user_count(user_id, 0)
    return 0


def create_keyboard():
    """Создание клавиатуры с кнопками"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn_increment = types.KeyboardButton('➕ +1')
    btn_reset = types.KeyboardButton('🔄 Сбросить')
    btn_check = types.KeyboardButton('📊 Проверить счетчик')

    keyboard.add(btn_increment, btn_reset, btn_check)
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = (
        "👋 Привет! Я бот-счетчик.\n\n"
        "Доступные команды:\n"
        "• /start или /help - это сообщение\n"
        "• /count - показать текущий счетчик\n"
        "• /reset - сбросить счетчик\n\n"
        "Или используйте кнопки ниже:"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_keyboard()
    )


@bot.message_handler(commands=['count'])
def show_count(message):
    """Показать текущее значение счетчика"""
    user_id = message.from_user.id
    count = get_user_count(user_id)

    bot.send_message(
        message.chat.id,
        f"📊 Ваш текущий счетчик: {count}",
        reply_markup=create_keyboard()
    )


@bot.message_handler(commands=['reset'])
def reset_count(message):
    """Сбросить счетчик"""
    user_id = message.from_user.id
    reset_user_count(user_id)

    bot.send_message(
        message.chat.id,
        "✅ Счетчик сброшен на 0!",
        reply_markup=create_keyboard()
    )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработка текстовых сообщений и кнопок"""
    user_id = message.from_user.id
    text = message.text

    if text == '➕ +1':
        # Увеличиваем счетчик
        new_count = increment_user_count(user_id)
        response = f"✅ Счетчик увеличен!\n📊 Текущее значение: {new_count}"

    elif text == '🔄 Сбросить':
        # Сбрасываем счетчик
        reset_user_count(user_id)
        response = "✅ Счетчик сброшен на 0!"

    elif text == '📊 Проверить счетчик':
        # Показываем текущее значение
        count = get_user_count(user_id)
        response = f"📊 Ваш текущий счетчик: {count}"

    else:
        # Если сообщение не распознано
        response = (
            "🤔 Не понял команду. Используйте кнопки или команды:\n"
            "/start - начать работу\n"
            "/count - показать счетчик\n"
            "/reset - сбросить счетчик"
        )

    bot.send_message(
        message.chat.id,
        response,
        reply_markup=create_keyboard()
    )


if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()

    print("Бот запущен...")
    print("База данных:", DB_NAME)

    # Запускаем бота
    bot.polling(none_stop=True)