import json
import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, "tokens.json")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
USERS_PATH = os.path.join(SESSIONS_DIR, "users.json")

# Загружаем токен
with open(TOKEN_PATH, "r") as file:
    config = json.load(file)
TOKEN = config["TOKEN"]

# Создаем папку sessions, если её нет
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# Загружаем данные пользователей из файла
def load_users():
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "r") as file:
            return json.load(file)
    return {}

# Сохраняем данные пользователей
def save_users():
    with open(USERS_PATH, "w") as file:
        json.dump(users, file, indent=4)

users = load_users()

bot = telebot.TeleBot(TOKEN)

# Кнопки для выбора кухни
cuisine_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cuisines = ["Восточная", "Европейская", "Русская", "Скандинавская", "Индийская"]
for cuisine in cuisines:
    cuisine_keyboard.add(KeyboardButton(cuisine))

# Кнопки для выбора среднего чека
price_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
price_ranges = ["до 500р", "500-1000", "1000-1500", "1500-2000", "2000+"]
for price in price_ranges:
    price_keyboard.add(KeyboardButton(price))

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    if user_id not in users:
        users[user_id] = {}  # Создаем пустой профиль пользователя
        save_users()
    bot.send_message(user_id, "Привет! Давай выберем твою любимую кухню:", reply_markup=cuisine_keyboard)

@bot.message_handler(func=lambda message: str(message.chat.id) in users and "cuisine" not in users[str(message.chat.id)])
def save_cuisine(message):
    user_id = str(message.chat.id)
    if message.text in cuisines:
        users[user_id]["cuisine"] = message.text
        save_users()
        bot.send_message(user_id, "Отлично! Теперь выбери желаемый средний чек:", reply_markup=price_keyboard)
    else:
        bot.send_message(user_id, "Выбери вариант из списка.")

@bot.message_handler(func=lambda message: str(message.chat.id) in users and "cuisine" in users[str(message.chat.id)] and "price_range" not in users[str(message.chat.id)])
def save_price(message):
    user_id = str(message.chat.id)
    if message.text in price_ranges:
        users[user_id]["price_range"] = message.text
        save_users()
        bot.send_message(user_id, "Ты зарегистрирован! Твои предпочтения сохранены.")
    else:
        bot.send_message(user_id, "Выбери вариант из списка.")

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
