import telebot
from telebot import types
import random

# Моковые данные для ресторанов
restaurants = [
    {"name": "Ресторан 'Прованс'", "address": "ул. Пушкина, д. 15", "cuisine": "Французская", "price": "800 рублей", "rating": "5 ⭐"},
    {"name": "Кафе 'Сакура'", "address": "пр-т Мира, д. 25", "cuisine": "Японская", "price": "600 рублей", "rating": "4 ⭐"},
    {"name": "Пиццерия 'Маргарита'", "address": "ул. Горького, д. 20", "cuisine": "Итальянская", "price": "700 рублей", "rating": "5 ⭐"},
    {"name": "Ресторан 'Шашлычная'", "address": "ул. Советская, д. 35", "cuisine": "Кавказская", "price": "900 рублей", "rating": "5 ⭐"},
    {"name": "Кафе 'Уютный уголок'", "address": "ул. Кирова, д. 40", "cuisine": "Европейская", "price": "550 рублей", "rating": "3 ⭐"}
]

# Хранение данных пользователей и комнат
user_data = {}
rooms = {}

# Инициализация бота
bot = telebot.TeleBot('7636573482:AAGUi4I-kYnb4WHyyN4emv4hpf7K3QealYY')

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    user_data[user_id] = {"step": "preferences"}  # Начинаем с вопросов о предпочтениях

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Да", callback_data="spicy_yes"))
    keyboard.add(types.InlineKeyboardButton("Нет", callback_data="spicy_no"))

    bot.send_message(
        user_id,
        "Приветствую! Я — Dorcia, ваш помощник в выборе ресторанов. 🍽️\n"
        "Помогаю находить места, которые подойдут вам и вашим коллегам по вкусу.\n\n"
        "1. Вы предпочитаете острую кухню?",
        reply_markup=keyboard
    )

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.message.chat.id
    data = call.data

    if user_data[user_id]["step"] == "preferences":
        if data in ["spicy_yes", "spicy_no"]:
            user_data[user_id]["spicy"] = data == "spicy_yes"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("Да", callback_data="spices_yes"))
            keyboard.add(types.InlineKeyboardButton("Нет", callback_data="spices_no"))
            bot.edit_message_text(
                "2. Любите блюда со специями?",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
        elif data in ["spices_yes", "spices_no"]:
            user_data[user_id]["spices"] = data == "spices_yes"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("Создать комнату", callback_data="create_room"))
            keyboard.add(types.InlineKeyboardButton("Присоединиться к комнате", callback_data="join_room"))
            bot.edit_message_text(
                "Спасибо за ответы! Теперь давайте определимся, хотите ли вы создать новую комнату или присоединиться к уже существующей.",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
            user_data[user_id]["step"] = "room_choice"
    elif user_data[user_id]["step"] == "room_choice":
        if data == "create_room":
            room_code = str(random.randint(10000, 99999))
            rooms[room_code] = {"members": [user_id], "status": "waiting"}
            user_data[user_id]["room_code"] = room_code
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("Адрес 1", callback_data="address_1"))
            keyboard.add(types.InlineKeyboardButton("Адрес 2", callback_data="address_2"))
            bot.edit_message_text(
                "Для того чтобы подобрать рестораны поблизости, укажите, пожалуйста, ваш текущий адрес.",
                chat_id=user_id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
            user_data[user_id]["step"] = "address"
        elif data == "join_room":
            bot.edit_message_text(
                "Введите, пожалуйста, код комнаты, к которой хотите присоединиться.",
                chat_id=user_id,
                message_id=call.message.message_id
            )
            user_data[user_id]["step"] = "join_room"
    elif user_data[user_id]["step"] == "address":
        user_data[user_id]["address"] = data
        bot.edit_message_text(
            f"Комната создана успешно! Вот её уникальный код: {user_data[user_id]['room_code']}. Поделитесь этим кодом с коллегами, чтобы они могли присоединиться к вам.\nКак только все участники будут готовы, нажмите на кнопку *Готовы!*",
            chat_id=user_id,
            message_id=call.message.message_id
        )
        user_data[user_id]["step"] = "ready"
    elif user_data[user_id]["step"] == "ready":
        if data == "ready":
            bot.edit_message_text(
                "Подождите немного, подбираем для вас лучшие варианты...",
                chat_id=user_id,
                message_id=call.message.message_id
            )
            show_restaurants(user_id)

# Показ ресторанов
def show_restaurants(user_id):
    keyboard = types.InlineKeyboardMarkup()
    for i, restaurant in enumerate(restaurants):
        keyboard.add(types.InlineKeyboardButton(restaurant["name"], callback_data=f"restaurant_{i}"))
    bot.send_message(user_id, "Вот список ресторанов:", reply_markup=keyboard)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    if user_data[user_id]["step"] == "join_room":
        room_code = message.text
        if room_code in rooms:
            rooms[room_code]["members"].append(user_id)
            user_data[user_id]["room_code"] = room_code
            bot.send_message(user_id, "Вы успешно присоединились к комнате. Ожидайте остальных участников.")
        else:
            bot.send_message(user_id, "Комната не найдена. Пожалуйста, проверьте код комнаты.")

# Запуск бота
bot.polling()