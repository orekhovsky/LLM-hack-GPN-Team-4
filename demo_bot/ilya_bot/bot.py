import telebot
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from storage import get_rooms, save_rooms, get_users, save_users
import config

bot = telebot.TeleBot(config.token)

# 🔥 Три ресторана для голосования
RESTAURANTS = ["🍣 Sushi Bar", "🍕 Pizza Place", "🥩 Steak House"]

# 📌 Главное меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Создать комнату"), KeyboardButton("Присоединиться к комнате"))
    return markup

# 📌 Меню модератора
def moderator_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Начать голосование"))
    return markup

# 📌 Меню голосования
def voting_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for rest in RESTAURANTS:
        markup.add(KeyboardButton(rest))
    return markup

# 📌 Меню завершения голосования
def finish_voting_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Завершить голосование"))
    return markup

# 📌 Меню закрытия комнаты
def close_room_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Закрыть комнату"))
    return markup

# 🔥 Обработчик команды /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.send_message(message.chat.id, "👋 Привет! Давай выберем ресторан!", reply_markup=main_menu())

# 🔥 Создание комнаты
@bot.message_handler(func=lambda msg: msg.text == "Создать комнату")
def create_room_handler(message):
    rooms = get_rooms()
    users = get_users()
    
    room_code = str(random.randint(1000, 9999))
    rooms[room_code] = {"moderator": message.chat.id, "guests": [], "votes": {}}
    users[str(message.chat.id)] = {"room": room_code, "role": "moderator"}
    
    save_rooms(rooms)
    save_users(users)

    bot.send_message(message.chat.id, f"✅ Комната создана! Код: {room_code}\nОжидаем гостей...", reply_markup=moderator_menu())

# 🔥 Присоединение к комнате
@bot.message_handler(func=lambda msg: msg.text == "Присоединиться к комнате")
def join_room_handler(message):
    bot.send_message(message.chat.id, "🔢 Введите код комнаты:")

    @bot.message_handler(func=lambda msg: msg.text.isdigit())
    def process_room_code(message):
        rooms = get_rooms()
        users = get_users()
        room_code = message.text

        if room_code not in rooms:
            bot.send_message(message.chat.id, "❌ Такой комнаты нет! Введите код снова.")
            return

        rooms[room_code]["guests"].append(message.chat.id)
        users[str(message.chat.id)] = {"room": room_code, "role": "guest"}

        save_rooms(rooms)
        save_users(users)

        bot.send_message(message.chat.id, "✅ Вы присоединились к комнате! Ожидайте начала голосования.")

# 🔥 Начало голосования (только для модератора)
@bot.message_handler(func=lambda msg: msg.text == "Начать голосование")
def start_voting_handler(message):
    users = get_users()
    user = users.get(str(message.chat.id))

    if user and user["role"] == "moderator":
        room_code = user["room"]
        bot.send_message(message.chat.id, "🎉 Голосование началось!", reply_markup=finish_voting_menu())

        rooms = get_rooms()
        participants = rooms[room_code]["guests"] + [rooms[room_code]["moderator"]]
        
        for participant in participants:
            bot.send_message(participant, "🍽 Выберите ресторан:", reply_markup=voting_menu())

# 🔥 Голосование
@bot.message_handler(func=lambda msg: msg.text in RESTAURANTS)
def vote_handler(message):
    users = get_users()
    user = users.get(str(message.chat.id))

    if user:
        room_code = user["room"]
        rooms = get_rooms()

        if room_code in rooms:
            rooms[room_code]["votes"][message.chat.id] = message.text
            save_rooms(rooms)

            # Удаляем кнопки у проголосовавшего
            bot.send_message(message.chat.id, "✅ Ваш голос сохранён. Ожидайте результатов!", reply_markup=ReplyKeyboardRemove())

            # Если это модератор, показать кнопку завершения голосования
            if user["role"] == "moderator":
                bot.send_message(message.chat.id, "📝 Вы можете завершить голосование.", reply_markup=finish_voting_menu())

# 🔥 Завершение голосования (только для модератора)
@bot.message_handler(func=lambda msg: msg.text == "Завершить голосование")
def finish_voting_handler(message):
    users = get_users()
    user = users.get(str(message.chat.id))

    if user and user["role"] == "moderator":
        room_code = user["room"]
        rooms = get_rooms()

        results = {rest: 0 for rest in RESTAURANTS}
        for vote in rooms[room_code]["votes"].values():
            results[vote] += 1

        results_text = "\n".join([f"{r}: {c} голосов" for r, c in results.items()])

        # Отправляем результаты всем участникам
        participants = rooms[room_code]["guests"] + [rooms[room_code]["moderator"]]
        for participant in participants:
            bot.send_message(participant, f"📊 Итоги голосования:\n{results_text}")

        bot.send_message(message.chat.id, "🔚 Вы можете закрыть комнату.", reply_markup=close_room_menu())

# 🔥 Закрытие комнаты
@bot.message_handler(func=lambda msg: msg.text == "Закрыть комнату")
def close_room_handler(message):
    users = get_users()
    user = users.get(str(message.chat.id))

    if user and user["role"] == "moderator":
        room_code = user["room"]
        rooms = get_rooms()

        # Удаляем комнату
        del rooms[room_code]
        save_rooms(rooms)

        # Удаляем всех пользователей из этой комнаты
        users = {uid: info for uid, info in users.items() if info["room"] != room_code}
        save_users(users)

        bot.send_message(message.chat.id, "🚪 Комната закрыта!", reply_markup=main_menu())

# 🔥 Запуск бота
if __name__ == '__main__':
    print("✅ Бот запущен!")
    bot.polling(none_stop=True)
