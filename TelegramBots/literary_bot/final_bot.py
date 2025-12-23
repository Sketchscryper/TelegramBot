# final_bot.py
import os
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Базы данных
WRITERS = ["Хемингуэй", "Толстой", "Достоевский", "Оруэлл", "Кафка", "Маркес"]
POETS = ["Шекспир", "Пушкин", "Есенин", "Ахматова", "Цветаева", "Бродский"]
BOOKS = ["Три товарища", "Мастер и Маргарита", "1984", "Преступление и наказание", "Война и мир"]
MONOLOGUES = ["Быть или не быть", "Слово о полку Игореве", "Песнь о вещем Олеге", "Мцыри"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "📚 *Литературный бот*\n\n"
        "Я могу подсказать:\n"
        "• Писатель - случайного писателя\n"
        "• Поэт - случайного поэта\n"
        "• Книга - случайную книгу\n"
        "• Монолог - случайный монолог\n\n"
        "Просто отправь мне одно из этих слов!"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "Доступные команды:\n"
        "/start - начать общение\n"
        "/help - показать эту справку\n\n"
        "Просто отправьте одно из слов:\n"
        "Писатель, Поэт, Книга, Монолог"
    )
    await update.message.reply_text(help_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text.strip().lower()

    # Словарь соответствий
    response_map = {
        "писатель": lambda: f"📝 Писатель: *{random.choice(WRITERS)}*",
        "поэт": lambda: f"✍️ Поэт: *{random.choice(POETS)}*",
        "книга": lambda: f"📖 Книга: *{random.choice(BOOKS)}*",
        "монолог": lambda: f"🎭 Монолог: *{random.choice(MONOLOGUES)}*"
    }

    if user_message in response_map:
        response = response_map[user_message]()
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "Я не понимаю эту команду. 😕\n"
            "Попробуйте: Писатель, Поэт, Книга или Монолог\n"
            "Или введите /help для справки."
        )


def main():
    """Основная функция запуска бота"""
    if not TOKEN:
        print("Ошибка: Токен бота не найден!")
        print("Создайте файл .env с TELEGRAM_BOT_TOKEN=ваш_токен")
        return

    # Создаем приложение
    app = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print("✅ Бот запущен и готов к работе!")
    print("📱 Перейдите в Telegram и начните общение с вашим ботом")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()