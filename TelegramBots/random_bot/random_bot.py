import telebot
from telebot import types
import sqlite3
import random
import datetime

# Инициализация бота
bot = telebot.TeleBot('YOUR_BOT_TOKEN_HERE')

# Имя файла базы данных
DB_NAME = 'random_bot.db'


def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу для истории действий пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        action_type TEXT NOT NULL,
        action_data TEXT,
        result TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу для пользовательских вариантов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_choices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()


def save_action(user_id, username, action_type, action_data, result):
    """Сохранить действие пользователя в базу данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO user_actions (user_id, username, action_type, action_data, result)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, action_type, action_data, result))

    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Получить статистику пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Получаем общее количество действий
    cursor.execute('SELECT COUNT(*) FROM user_actions WHERE user_id = ?', (user_id,))
    total_actions = cursor.fetchone()[0]

    # Получаем количество действий по типам
    cursor.execute('''
    SELECT action_type, COUNT(*) 
    FROM user_actions 
    WHERE user_id = ? 
    GROUP BY action_type
    ''', (user_id,))

    actions_by_type = cursor.fetchall()

    conn.close()

    return total_actions, actions_by_type


def save_user_choice(user_id, option1, option2):
    """Сохранить пользовательские варианты выбора"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Удаляем старые варианты пользователя
    cursor.execute('DELETE FROM user_choices WHERE user_id = ?', (user_id,))

    # Сохраняем новые варианты
    cursor.execute('''
    INSERT INTO user_choices (user_id, option1, option2)
    VALUES (?, ?, ?)
    ''', (user_id, option1, option2))

    conn.commit()
    conn.close()


def get_user_choice(user_id):
    """Получить сохраненные варианты пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT option1, option2 
    FROM user_choices 
    WHERE user_id = ? 
    ORDER BY id DESC LIMIT 1
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()

    return result


def create_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn_number = types.KeyboardButton('🎲 Случайное число')
    btn_coin = types.KeyboardButton('🪙 Монетка')
    btn_choice = types.KeyboardButton('🤔 Выбрать из 2-х')
    btn_stats = types.KeyboardButton('📊 Статистика')

    keyboard.add(btn_number, btn_coin, btn_choice, btn_stats)
    return keyboard


def create_choice_keyboard():
    """Создание клавиатуры для выбора"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn_default = types.KeyboardButton('🎯 "Да" или "Нет"')
    btn_custom = types.KeyboardButton('✏️ Свои варианты')
    btn_back = types.KeyboardButton('🔙 Назад')

    keyboard.add(btn_default, btn_custom, btn_back)
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = (
        "🎲 *Добро пожаловать в Random Bot!*\n\n"
        "Я помогу вам сделать случайный выбор:\n\n"
        "✨ *Доступные возможности:*\n"
        "• 🎲 Случайное число от 1 до 100\n"
        "• 🪙 Подбросить монетку (Орел/Решка)\n"
        "• 🤔 Выбрать из двух вариантов\n"
        "• 📊 Посмотреть статистику\n\n"
        "Используйте кнопки ниже или команды:\n"
        "/number - случайное число\n"
        "/coin - монетка\n"
        "/choice - выбор из двух\n"
        "/stats - статистика"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['number'])
def send_random_number(message):
    """Генерация случайного числа"""
    user = message.from_user
    random_num = random.randint(1, 100)

    result_text = f"🎲 *Ваше случайное число:* {random_num}"

    # Сохраняем действие в базу
    save_action(user.id, user.username, 'random_number', '1-100', str(random_num))

    bot.send_message(
        message.chat.id,
        result_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['coin'])
def flip_coin(message):
    """Подбрасывание монетки"""
    user = message.from_user
    result = random.choice(['Орел', 'Решка'])

    # Эмодзи для наглядности
    emoji = '🦅' if result == 'Орел' else '🪙'

    result_text = f"{emoji} *Монетка показывает:* {result}"

    # Сохраняем действие в базу
    save_action(user.id, user.username, 'coin_flip', 'Орел/Решка', result)

    bot.send_message(
        message.chat.id,
        result_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['choice'])
def choice_menu(message):
    """Меню выбора из двух вариантов"""
    bot.send_message(
        message.chat.id,
        "🤔 *Выберите тип выбора:*",
        parse_mode='Markdown',
        reply_markup=create_choice_keyboard()
    )


@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Показать статистику пользователя"""
    user = message.from_user
    total_actions, actions_by_type = get_user_stats(user.id)

    stats_text = f"📊 *Ваша статистика:*\n\n"
    stats_text += f"Всего действий: *{total_actions}*\n\n"

    if actions_by_type:
        stats_text += "*По типам:*\n"
        for action_type, count in actions_by_type:
            if action_type == 'random_number':
                stats_text += f"🎲 Случайных чисел: {count}\n"
            elif action_type == 'coin_flip':
                stats_text += f"🪙 Подбрасываний монетки: {count}\n"
            elif action_type == 'custom_choice':
                stats_text += f"🤔 Выборов из вариантов: {count}\n"
            elif action_type == 'default_choice':
                stats_text += f"🎯 Выборов 'Да/Нет': {count}\n"
    else:
        stats_text += "Вы еще не использовали бота. Попробуйте кнопки ниже!"

    bot.send_message(
        message.chat.id,
        stats_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработка текстовых сообщений и кнопок"""
    user = message.from_user
    text = message.text

    if text == '🎲 Случайное число':
        send_random_number(message)

    elif text == '🪙 Монетка':
        flip_coin(message)

    elif text == '🤔 Выбрать из 2-х':
        choice_menu(message)

    elif text == '📊 Статистика':
        show_stats(message)

    elif text == '🎯 "Да" или "Нет"':
        # Выбор из "Да" или "Нет"
        result = random.choice(['Да', 'Нет'])
        emoji = '✅' if result == 'Да' else '❌'

        result_text = f"{emoji} *Результат:* {result}"

        # Сохраняем действие в базу
        save_action(user.id, user.username, 'default_choice', 'Да/Нет', result)

        bot.send_message(
            message.chat.id,
            result_text,
            parse_mode='Markdown',
            reply_markup=create_choice_keyboard()
        )

    elif text == '✏️ Свои варианты':
        # Запрос пользовательских вариантов
        msg = bot.send_message(
            message.chat.id,
            "✏️ *Введите два варианта через запятую:*\n\n"
            "Например: *Пойти гулять, Остаться дома*",
            parse_mode='Markdown',
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_custom_options)

    elif text == '🔙 Назад':
        # Возврат в главное меню
        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=create_main_keyboard()
        )

    else:
        # Если сообщение не распознано
        bot.send_message(
            message.chat.id,
            "🤔 Не понял команду. Используйте кнопки или команды:\n"
            "/start - начать работу\n"
            "/number - случайное число\n"
            "/coin - монетка\n"
            "/choice - выбор из двух\n"
            "/stats - статистика",
            reply_markup=create_main_keyboard()
        )


def process_custom_options(message):
    """Обработка пользовательских вариантов"""
    user = message.from_user
    text = message.text.strip()

    # Разделяем варианты по запятой
    if ',' in text:
        options = [opt.strip() for opt in text.split(',')]

        if len(options) >= 2:
            option1, option2 = options[0], options[1]

            # Сохраняем варианты в базу
            save_user_choice(user.id, option1, option2)

            # Делаем случайный выбор
            result = random.choice([option1, option2])

            result_text = (
                f"🤔 *Варианты:*\n"
                f"1. {option1}\n"
                f"2. {option2}\n\n"
                f"🎯 *Выбор пал на:* {result}"
            )

            # Сохраняем действие в базу
            save_action(user.id, user.username, 'custom_choice', f'{option1}/{option2}', result)

            bot.send_message(
                message.chat.id,
                result_text,
                parse_mode='Markdown',
                reply_markup=create_choice_keyboard()
            )

        else:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ Нужно ввести *два варианта* через запятую.\n"
                "Попробуйте еще раз:",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(msg, process_custom_options)
    else:
        msg = bot.send_message(
            message.chat.id,
            "⚠️ Используйте запятую для разделения вариантов.\n"
            "Например: *Кино, Ресторан*\n"
            "Попробуйте еще раз:",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_custom_options)


if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()

    print("🎲 Random Bot запущен...")
    print(f"📁 База данных: {DB_NAME}")

    # Запускаем бота
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")