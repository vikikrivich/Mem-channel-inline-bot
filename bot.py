import telebot
from utils.settings import settings
from handlers import BotHandlers


def main():
    settings.load_from_dotenv()
    bot = telebot.TeleBot(settings.BOT_TOKEN)
    handlers = BotHandlers(bot)

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        handlers.send_welcome(message)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        handlers.callback_inline(call)

    bot.polling()


if __name__ == '__main__':
    main()