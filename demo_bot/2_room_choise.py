import json
import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Загружаем токен
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, "tokens.json")

with open(TOKEN_PATH, "r") as file:
    config = json.load(file)

TOKEN = config["TOKEN"]

bot = telebot.TeleBot(TOKEN)

users = {}  # Данные о пользователях
rooms = {}  # Данные о комнатах {room_id: {"moderator": user_id, "members": []}}
user_rooms = {}  # Какую комнату выбрал пользователь {user_id: room_id}

# Клавиатура для выбора комнаты
def get_room_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for room_id in rooms.keys():
        markup.add(KeyboardButton(f"Комната {room_id}"))
    return markup if rooms else None

@bot.message_handler(commands=['create_room'])
def create_room(message):
    """Создание новой комнаты"""
    user_id = message.chat.id
    room_id = str(len(rooms) + 1)  # Уникальный ID комнаты

    rooms[room_id] = {"moderator": user_id, "members": [user_id]}
    user_rooms[user_id] = room_id  # Пользователь автоматически заходит в свою комнату

    bot.send_message(user_id, f"Ты создал комнату {room_id}. Теперь другие могут к ней присоединиться!")

@bot.message_handler(commands=['join_room'])
def join_room(message):
    """Выбор комнаты из списка"""
    user_id = message.chat.id
    if not rooms:
        bot.send_message(user_id, "Нет доступных комнат. Создай новую с помощью /create_room.")
        return

    bot.send_message(user_id, "Выбери комнату:", reply_markup=get_room_keyboard())

@bot.message_handler(func=lambda message: message.text.startswith("Комната"))
def enter_room(message):
    """Вход в выбранную комнату"""
    user_id = message.chat.id
    room_id = message.text.split()[-1]

    if room_id in rooms:
        rooms[room_id]["members"].append(user_id)
        user_rooms[user_id] = room_id
        bot.send_message(user_id, f"Ты присоединился к комнате {room_id}!")
    else:
        bot.send_message(user_id, "Такой комнаты не существует.")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    bot.send_message(message.chat.id, "Бот завершает работу.")
    os._exit(0)  # Остановка скрипта

bot.polling()
