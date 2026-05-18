import telebot

try:
    from bkz3.settings import TG_BOT_TOKEN
except ImportError:
    TG_BOT_TOKEN = None

if TG_BOT_TOKEN:
    base_bot = telebot.TeleBot(TG_BOT_TOKEN)
    welcome_bot = telebot.TeleBot(TG_BOT_TOKEN)
