import telebot #0.0.5
import sqlite3


bot = telebot.TeleBot('7636573482:AAGUi4I-kYnb4WHyyN4emv4hpf7K3QealYY')

@bot.message_handler(commands=['start'])
def start(message):
    pass






#polling
bot.polling()