import telebot
from telebot import types
import sqlite3
import random
import datetime

# Инициализация бота
bot = telebot.TeleBot('YOUR_TOKEN_BOT')

# Имя файла базы данных
DB_NAME = 'quiz_bot.db'

# База вопросов для викторины
QUESTIONS = [
    {
        'question': 'Солнце вращается вокруг Земли?',
        'answer': 'Нет',
        'explanation': 'На самом деле Земля вращается вокруг Солнца! 🌍☀️'
    },
    {
        'question': 'Акулы — это млекопитающие?',
        'answer': 'Нет',
        'explanation': 'Акулы — это рыбы, а не млекопитающие. 🦈'
    },
    {
        'question': 'Вода кипит при 100 градусах Цельсия?',
        'answer': 'Да',
        'explanation': 'Да, при нормальном атмосферном давлении вода кипит при 100°C. 💧'
    },
    {
        'question': 'Пингвины умеют летать?',
        'answer': 'Нет',
        'explanation': 'Пингвины не летают, но отлично плавают! 🐧'
    },
    {
        'question': 'Человек использует только 10% своего мозга?',
        'answer': 'Нет',
        'explanation': 'Это миф! Человек использует все области мозга, но не одновременно. 🧠'
    },
    {
        'question': 'Банан — это ягода?',
        'answer': 'Да',
        'explanation': 'С ботанической точки зрения банан — это ягода! 🍌'
    },
    {
        'question': 'Мед никогда не портится?',
        'answer': 'Да',
        'explanation': 'Мед может храниться веками благодаря своему составу. 🍯'
    },
    {
        'question': 'Змеи могут слышать?',
        'answer': 'Да',
        'explanation': 'Змеи слышат, но не через уши, а чувствуя вибрации. 🐍'
    },
    {
        'question': 'Венера — самая горячая планета Солнечной системы?',
        'answer': 'Да',
        'explanation': 'Да, из-за плотной атмосферы и парникового эффекта. ♀️'
    },
    {
        'question': 'Страус прячет голову в песок от страха?',
        'answer': 'Нет',
        'explanation': 'Это миф! Страусы опускают голову, чтобы искать пищу. 🐦'
    }
]

# Словарь для хранения текущих сессий пользователей
user_sessions = {}


def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу для статистики пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        total_games INTEGER DEFAULT 0,
        total_correct INTEGER DEFAULT 0,
        total_questions INTEGER DEFAULT 0,
        best_score INTEGER DEFAULT 0,
        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу для истории вопросов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        user_answer TEXT,
        correct_answer TEXT NOT NULL,
        is_correct BOOLEAN,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Создаем таблицу для вопросов викторины
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL UNIQUE,
        correct_answer TEXT NOT NULL,
        explanation TEXT,
        category TEXT DEFAULT 'general',
        difficulty INTEGER DEFAULT 1,
        times_shown INTEGER DEFAULT 0,
        times_correct INTEGER DEFAULT 0
    )
    ''')

    # Добавляем вопросы в базу, если их там нет
    for q in QUESTIONS:
        cursor.execute('''
        INSERT OR IGNORE INTO quiz_questions (question, correct_answer, explanation)
        VALUES (?, ?, ?)
        ''', (q['question'], q['answer'], q['explanation']))

    conn.commit()
    conn.close()


def get_user_stats(user_id):
    """Получить статистику пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT username, total_games, total_correct, total_questions, 
           best_score, last_activity
    FROM user_stats 
    WHERE user_id = ?
    ''', (user_id,))

    result = cursor.fetchone()

    if result:
        stats = {
            'username': result[0],
            'total_games': result[1] or 0,
            'total_correct': result[2] or 0,
            'total_questions': result[3] or 0,
            'best_score': result[4] or 0,
            'last_activity': result[5]
        }
    else:
        stats = {
            'username': None,
            'total_games': 0,
            'total_correct': 0,
            'total_questions': 0,
            'best_score': 0,
            'last_activity': None
        }

    conn.close()
    return stats


def update_user_stats(user_id, username, **kwargs):
    """Обновить статистику пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Получаем текущие данные
    cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
    current = cursor.fetchone()

    if current:
        # Обновляем существующую запись
        updates = []
        values = []

        for key, value in kwargs.items():
            if key == 'current_score':
                # Для текущего счета также проверяем лучший результат
                cursor.execute('SELECT best_score FROM user_stats WHERE user_id = ?', (user_id,))
                best_score = cursor.fetchone()[0] or 0
                if value > best_score:
                    updates.append('best_score = ?')
                    values.append(value)
            else:
                updates.append(f'{key} = ?')
                values.append(value)

        updates.append('last_activity = CURRENT_TIMESTAMP')

        if username:
            updates.append('username = ?')
            values.append(username)

        values.append(user_id)

        query = f'UPDATE user_stats SET {", ".join(updates)} WHERE user_id = ?'
        cursor.execute(query, values)
    else:
        # Создаем новую запись
        fields = ['user_id', 'username']
        placeholders = ['?', '?']
        values = [user_id, username]

        for key, value in kwargs.items():
            if key != 'current_score':  # current_score не сохраняем в базе, только в сессии
                fields.append(key)
                placeholders.append('?')
                values.append(value)

        fields.append('created_at')
        placeholders.append('CURRENT_TIMESTAMP')

        query = f'INSERT INTO user_stats ({", ".join(fields)}) VALUES ({", ".join(placeholders)})'
        cursor.execute(query, values)

    conn.commit()
    conn.close()


def save_question_history(user_id, question, user_answer, correct_answer, is_correct):
    """Сохранить историю вопроса"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO question_history (user_id, question, user_answer, correct_answer, is_correct)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, question, user_answer, correct_answer, is_correct))

    # Обновляем статистику вопроса
    cursor.execute('''
    UPDATE quiz_questions 
    SET times_shown = times_shown + 1,
        times_correct = times_correct + ?
    WHERE question = ?
    ''', (1 if is_correct else 0, question))

    conn.commit()
    conn.close()


def get_random_question():
    """Получить случайный вопрос"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id, question, correct_answer, explanation 
    FROM quiz_questions 
    ORDER BY RANDOM() 
    LIMIT 1
    ''')

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'id': result[0],
            'question': result[1],
            'correct_answer': result[2],
            'explanation': result[3]
        }
    return None


def get_question_history(user_id, limit=10):
    """Получить историю вопросов пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT question, user_answer, correct_answer, is_correct, timestamp 
    FROM question_history 
    WHERE user_id = ? 
    ORDER BY timestamp DESC 
    LIMIT ?
    ''', (user_id, limit))

    history = cursor.fetchall()
    conn.close()

    return history


def get_global_stats():
    """Получить глобальную статистику"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Общее количество игроков
    cursor.execute('SELECT COUNT(*) FROM user_stats')
    total_players = cursor.fetchone()[0]

    # Общее количество вопросов
    cursor.execute('SELECT COUNT(*) FROM quiz_questions')
    total_questions = cursor.fetchone()[0]

    # Общее количество ответов
    cursor.execute('SELECT COUNT(*) FROM question_history')
    total_answers = cursor.fetchone()[0]

    # Процент правильных ответов
    cursor.execute('SELECT COUNT(*) FROM question_history WHERE is_correct = 1')
    correct_answers = cursor.fetchone()[0]

    conn.close()

    if total_answers > 0:
        accuracy = (correct_answers / total_answers) * 100
    else:
        accuracy = 0

    return {
        'total_players': total_players,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'accuracy': round(accuracy, 1)
    }


def create_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn_start = types.KeyboardButton('🎮 Начать викторину')
    btn_stats = types.KeyboardButton('📊 Моя статистика')
    btn_global = types.KeyboardButton('🌍 Глобальная статистика')
    btn_history = types.KeyboardButton('📜 История ответов')
    btn_rules = types.KeyboardButton('📚 Правила')

    keyboard.add(btn_start, btn_stats, btn_global, btn_history, btn_rules)
    return keyboard


def create_quiz_keyboard():
    """Создание клавиатуры для викторины"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn_yes = types.KeyboardButton('✅ Да')
    btn_no = types.KeyboardButton('❌ Нет')
    btn_stop = types.KeyboardButton('⏹️ Закончить игру')
    btn_hint = types.KeyboardButton('💡 Подсказка')

    keyboard.add(btn_yes, btn_no, btn_stop, btn_hint)
    return keyboard


def create_session(user_id):
    """Создать новую сессию для пользователя"""
    user_sessions[user_id] = {
        'active': True,
        'score': 0,
        'question_count': 0,
        'current_question': None,
        'used_questions': []  # Чтобы не повторять вопросы в одной сессии
    }


def get_session(user_id):
    """Получить сессию пользователя"""
    return user_sessions.get(user_id)


def end_session(user_id):
    """Завершить сессию пользователя"""
    if user_id in user_sessions:
        del user_sessions[user_id]


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = (
        "🧠 *Добро пожаловать в Викторину Да/Нет!*\n\n"
        "Это игра, где нужно отвечать на вопросы только \"Да\" или \"Нет\".\n\n"
        "✨ *Что я умею:*\n"
        "• 🎮 Проводить викторину с интересными вопросами\n"
        "• 📊 Вести вашу личную статистику\n"
        "• 🌍 Показывать глобальную статистику\n"
        "• 📜 Сохранять историю ваших ответов\n\n"
        "Используйте кнопки ниже или команды:\n"
        "/quiz - начать викторину\n"
        "/stats - моя статистика\n"
        "/global - глобальная статистика\n"
        "/history - история ответов\n"
        "/rules - правила игры"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['rules'])
def show_rules(message):
    """Показать правила игры"""
    rules_text = (
        "📚 *Правила игры:*\n\n"
        "1. Я задаю вопрос, на который можно ответить только *Да* или *Нет*\n"
        "2. Вы выбираете один из двух вариантов ответа\n"
        "3. После ответа я покажу правильный ответ и объяснение\n"
        "4. Игра продолжается до тех пор, пока вы не решите остановиться\n\n"
        "📊 *Как считается счет:*\n"
        "• За каждый правильный ответ: +1 балл\n"
        "• За неправильный: 0 баллов\n"
        "• Лучший результат сохраняется\n\n"
        "💡 *Подсказки:*\n"
        "• Можно использовать кнопку \"Подсказка\" для сложных вопросов\n"
        "• Статистика сохраняется между играми\n"
        "• Вопросы не повторяются в одной игровой сессии"
    )

    bot.send_message(
        message.chat.id,
        rules_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


@bot.message_handler(commands=['quiz'])
def start_quiz_command(message):
    """Начать викторину по команде"""
    start_quiz(message)


@bot.message_handler(commands=['stats'])
def show_stats_command(message):
    """Показать статистику по команде"""
    show_stats(message)


@bot.message_handler(commands=['global'])
def show_global_stats_command(message):
    """Показать глобальную статистику"""
    show_global_stats(message)


@bot.message_handler(commands=['history'])
def show_history_command(message):
    """Показать историю по команде"""
    show_history(message)


def start_quiz(message):
    """Начать новую викторину"""
    user = message.from_user

    # Создаем новую сессию
    create_session(user.id)

    # Обновляем статистику
    stats = get_user_stats(user.id)
    update_user_stats(
        user.id,
        user.username,
        total_games=stats['total_games'] + 1
    )

    # Отправляем первый вопрос
    send_next_question(message.chat.id, user.id)


def send_next_question(chat_id, user_id):
    """Отправить следующий вопрос"""
    session = get_session(user_id)

    if not session or not session['active']:
        bot.send_message(
            chat_id,
            "Сначала начните викторину!",
            reply_markup=create_main_keyboard()
        )
        return

    # Получаем случайный вопрос, исключая уже заданные
    question_data = get_random_question()

    # Если вопрос уже был в этой сессии, ищем другой
    attempts = 0
    while question_data and question_data['question'] in session['used_questions'] and attempts < 10:
        question_data = get_random_question()
        attempts += 1

    if question_data:
        # Сохраняем текущий вопрос в сессии
        session['current_question'] = question_data
        session['used_questions'].append(question_data['question'])
        session['question_count'] += 1

        question_text = (
            f"❓ *Вопрос #{session['question_count']}*\n\n"
            f"{question_data['question']}\n\n"
            f"🏆 Текущий счет: *{session['score']}*"
        )

        bot.send_message(
            chat_id,
            question_text,
            parse_mode='Markdown',
            reply_markup=create_quiz_keyboard()
        )
    else:
        bot.send_message(
            chat_id,
            "К сожалению, вопросы закончились! 😅",
            reply_markup=create_main_keyboard()
        )
        end_session(user_id)


def show_stats(message):
    """Показать статистику пользователя"""
    user = message.from_user
    stats = get_user_stats(user.id)

    if stats['total_questions'] > 0:
        accuracy = (stats['total_correct'] / stats['total_questions']) * 100
    else:
        accuracy = 0

    stats_text = (
        f"📊 *Ваша статистика:*\n\n"
        f"🎮 Игр сыграно: *{stats['total_games']}*\n"
        f"❓ Всего вопросов: *{stats['total_questions']}*\n"
        f"✅ Правильных ответов: *{stats['total_correct']}*\n"
        f"🎯 Точность: *{accuracy:.1f}%*\n"
        f"🏆 Лучший результат: *{stats['best_score']}*\n\n"
    )

    # Добавляем текущую сессию, если она есть
    session = get_session(user.id)
    if session and session['active']:
        stats_text += f"🔥 Текущая игра: *{session['score']}* из {session['question_count'] - 1}\n\n"

    if stats['last_activity']:
        last_active = datetime.datetime.strptime(stats['last_activity'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
        stats_text += f"🕒 Последняя активность: {last_active}"

    bot.send_message(
        message.chat.id,
        stats_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


def show_global_stats(message):
    """Показать глобальную статистику"""
    stats = get_global_stats()

    stats_text = (
        f"🌍 *Глобальная статистика:*\n\n"
        f"👥 Игроков всего: *{stats['total_players']}*\n"
        f"❓ Вопросов в базе: *{stats['total_questions']}*\n"
        f"🎮 Ответов всего: *{stats['total_answers']}*\n"
        f"🎯 Общая точность: *{stats['accuracy']}%*\n\n"
        f"*Самые популярные категории:*\n"
        f"• Наука и природа 🔬\n"
        f"• Животные 🐾\n"
        f"• Мифы и факты 📚"
    )

    bot.send_message(
        message.chat.id,
        stats_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )


def show_history(message):
    """Показать историю ответов"""
    user = message.from_user
    history = get_question_history(user.id, limit=10)

    if history:
        history_text = "📜 *Последние ответы:*\n\n"

        for i, (question, user_answer, correct_answer, is_correct, timestamp) in enumerate(history, 1):
            time_str = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
            status = "✅" if is_correct else "❌"

            # Обрезаем длинные вопросы
            short_question = question[:50] + "..." if len(question) > 50 else question

            history_text += f"{i}. {status} {short_question}\n"
            history_text += f"   Ваш ответ: {user_answer} | Правильно: {correct_answer}\n"
            history_text += f"   {time_str}\n\n"

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
            "История ответов пуста.\n"
            "Сыграйте в викторину, чтобы начать собирать историю! 🎮",
            reply_markup=create_main_keyboard()
        )


def process_answer(message, question_data):
    """Обработать ответ пользователя"""
    user = message.from_user
    user_answer = message.text
    correct_answer = question_data['correct_answer']
    session = get_session(user.id)

    if not session:
        bot.send_message(
            message.chat.id,
            "Сначала начните викторину!",
            reply_markup=create_main_keyboard()
        )
        return

    # Проверяем ответ
    if user_answer in ['✅ Да', '❌ Нет']:
        # Извлекаем только "Да" или "Нет"
        answer_text = 'Да' if 'Да' in user_answer else 'Нет'
        is_correct = (answer_text == correct_answer)

        # Обновляем счет в сессии
        if is_correct:
            session['score'] += 1

        # Обновляем статистику в базе данных
        stats = get_user_stats(user.id)
        new_total_correct = stats['total_correct'] + (1 if is_correct else 0)

        update_user_stats(
            user.id,
            user.username,
            total_correct=new_total_correct,
            total_questions=stats['total_questions'] + 1,
            best_score=max(stats['best_score'], session['score'])
        )

        # Сохраняем в историю
        save_question_history(
            user.id,
            question_data['question'],
            answer_text,
            correct_answer,
            is_correct
        )

        # Формируем ответ
        result_text = (
            f"{'✅ *Правильно!*' if is_correct else '❌ *Неправильно!*'}\n\n"
            f"*Вопрос:* {question_data['question']}\n"
            f"*Ваш ответ:* {answer_text}\n"
            f"*Правильный ответ:* {correct_answer}\n\n"
            f"💡 *Объяснение:* {question_data['explanation']}\n\n"
            f"🏆 Текущий счет: *{session['score']}* из {session['question_count']}"
        )

        bot.send_message(
            message.chat.id,
            result_text,
            parse_mode='Markdown'
        )

        # Задержка перед следующим вопросом
        bot.send_chat_action(message.chat.id, 'typing')
        import time
        time.sleep(2)

        # Отправляем следующий вопрос
        send_next_question(message.chat.id, user.id)
    else:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, используйте кнопки 'Да' или 'Нет' для ответа.",
            reply_markup=create_quiz_keyboard()
        )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработка текстовых сообщений"""
    text = message.text
    user = message.from_user

    if text == '🎮 Начать викторину':
        start_quiz(message)

    elif text == '📊 Моя статистика':
        show_stats(message)

    elif text == '🌍 Глобальная статистика':
        show_global_stats(message)

    elif text == '📜 История ответов':
        show_history(message)

    elif text == '📚 Правила':
        show_rules(message)

    elif text in ['✅ Да', '❌ Нет']:
        # Проверяем, есть ли активная сессия и текущий вопрос
        session = get_session(user.id)
        if session and session['active'] and session['current_question']:
            process_answer(message, session['current_question'])
        else:
            bot.send_message(
                message.chat.id,
                "Сначала начните викторину!",
                reply_markup=create_main_keyboard()
            )

    elif text == '⏹️ Закончить игру':
        session = get_session(user.id)

        if session and session['active']:
            end_text = (
                f"🏁 *Игра завершена!*\n\n"
                f"🎯 Правильных ответов: *{session['score']}* из {session['question_count'] - 1}\n"
            )

            if session['question_count'] > 1:
                accuracy = (session['score'] / (session['question_count'] - 1)) * 100
                end_text += f"📊 Точность: *{accuracy:.1f}%*\n\n"

            # Проверяем, побил ли пользователь свой рекорд
            stats = get_user_stats(user.id)
            if session['score'] > stats['best_score']:
                end_text += f"🎉 *Новый рекорд!* Поздравляем! 🏆\n\n"

            end_text += f"Хотите сыграть еще раз?"

            # Завершаем сессию
            end_session(user.id)

            keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            btn_again = types.KeyboardButton('🔄 Играть снова')
            btn_menu = types.KeyboardButton('📋 Главное меню')
            keyboard.add(btn_again, btn_menu)

            bot.send_message(
                message.chat.id,
                end_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                message.chat.id,
                "У вас нет активной игры.",
                reply_markup=create_main_keyboard()
            )

    elif text == '💡 Подсказка':
        # Показываем подсказку для текущего вопроса
        session = get_session(user.id)
        if session and session['active'] and session['current_question']:
            bot.send_message(
                message.chat.id,
                f"💡 *Подсказка:*\n{session['current_question']['explanation']}\n\n"
                f"Теперь попробуйте ответить!",
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id,
                "Сначала начните викторину и получите вопрос!",
                reply_markup=create_main_keyboard()
            )

    elif text == '🔄 Играть снова':
        start_quiz(message)

    elif text == '📋 Главное меню':
        # Завершаем активную сессию при возврате в меню
        if user.id in user_sessions:
            end_session(user.id)

        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=create_main_keyboard()
        )

    else:
        bot.send_message(
            message.chat.id,
            "Используйте кнопки или команды:\n"
            "/quiz - начать викторину\n"
            "/stats - моя статистика\n"
            "/global - глобальная статистика\n"
            "/history - история ответов\n"
            "/rules - правила игры",
            reply_markup=create_main_keyboard()
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка callback-запросов"""
    if call.data == 'clear_history':
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM question_history WHERE user_id = ?', (call.from_user.id,))
        cursor.execute('UPDATE user_stats SET total_questions = 0, total_correct = 0, best_score = 0 WHERE user_id = ?',
                       (call.from_user.id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "✅ История очищена!")
        bot.send_message(
            call.message.chat.id,
            "История ответов успешно очищена!",
            reply_markup=create_main_keyboard()
        )


if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()

    print("🧠 Викторина Да/Нет запущена...")
    print(f"📁 База данных: {DB_NAME}")
    print(f"❓ Вопросов в базе: {len(QUESTIONS)}")

    # Запускаем бота
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")