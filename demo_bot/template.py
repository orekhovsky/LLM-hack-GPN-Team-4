import telebot
from telebot import types
import random
from qstns import *

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

def ask_question(user_id):
    step = user_data[user_id]["step"]
    if step < len(questions):
        question_data = questions[step]
        keyboard = types.InlineKeyboardMarkup()
        for key, value in question_data["options"].items():
            for option, _ in value.items():
                keyboard.add(types.InlineKeyboardButton(option, callback_data=f"answer_{key}"))
        bot.send_message(user_id, question_data["question"], reply_markup=keyboard)
    else:
        show_results(user_id)

# Функция для вывода результатов
def show_results(user_id):
    cuisines = user_data[user_id]["cuisines"]
    sorted_cuisines = sorted(cuisines.items(), key=lambda x: x[1], reverse=True)
    result_message = "Результаты опроса:\n"
    for cuisine, score in sorted_cuisines:
        if score > 0:
            result_message += f"{cuisine}: {score} баллов\n"
    bot.send_message(user_id, result_message)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    user_data[user_id] = {"step": 0, "cuisines": cuisines.copy()}
    ask_question(user_id)  # Начинаем с вопросов о предпочтениях

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Да", callback_data="spicy_yes"))
    keyboard.add(types.InlineKeyboardButton("Нет", callback_data="spicy_no"))

    bot.send_message(
        user_id,
        "Приветствую! Я — Dorcia, ваш помощник в выборе ресторанов. Помогаю находить места, которые подойдут вам и вашим коллегам по вкусу. 🍽️\n"
        "Чтобы я мог предложить подходящие варианты, расскажите мне о ваших кулинарных предпочтениях. 🍽️\n"
        "Ответьте, пожалуйста, на несколько коротких вопросов."
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

# ----------------------------------------------------------
'''
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='Можем начинать', callback_data='start_quiz')
    markup.add(btn1)
    bot.send_message(
        message.chat.id,
        "Приветствую! Я — Dorcia, ваш помощник в выборе ресторанов. Помогаю находить места, которые подойдут вам и вашим коллегам по вкусу. 🍽\n"
        "Чтобы я мог предложить подходящие варианты, расскажите мне о ваших кулинарных предпочтениях. \n"
        "Ответьте, пожалуйста, на несколько коротких вопросов.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith(('start_quiz', 'answer', 'followup')))
def handle_query(call):
    user_id = call.message.chat.id
    data = call.data
    
    if data == 'start_quiz':
        # Инициализация состояния пользователя
        user_states[user_id] = {
            'current_question': 0,
            'cuisines': {k: 0 for k in cuisines},
            'follow_up': None
        }
        ask_question(user_id)
    elif data.startswith('answer_'):
        handle_answer(user_id, data)
    elif data.startswith('followup_'):
        handle_followup(user_id, data)

def ask_question(user_id, question_num=0):
    state = user_states[user_id]
    
    if question_num >= len(questions):
        return show_results(user_id)
    
    if state['follow_up'] is not None:
        q_data = state['follow_up']
        state['follow_up'] = None
    else:
        q_data = questions[question_num]
    
    markup = types.InlineKeyboardMarkup()
    for key in q_data['options']:
        btn_text = list(q_data['options'][key].keys())[0]
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'answer_{question_num}_{key}'))
    
    bot.send_message(user_id, q_data['question'], reply_markup=markup)

def handle_answer(user_id, data):
    state = user_states[user_id]
    _, q_num, answer = data.split('_')
    q_num = int(q_num)
    q_data = questions[q_num]
    
    # Обновляем баллы
    selected = list(q_data['options'][answer].values())[0]
    for cuisine in selected:
        state['cuisines'][cuisine] += 1
    
    # Проверяем уточняющий вопрос
    if 'follow_up' in q_data and answer in q_data['follow_up']:
        state['follow_up'] = q_data['follow_up'][answer]
        ask_question(user_id, q_num)
    else:
        state['current_question'] += 1
        ask_question(user_id, state['current_question'])

def handle_followup(user_id, data):
    state = user_states[user_id]
    _, answer = data.split('_')
    q_data = state['follow_up']
    
    # Обновляем баллы
    selected = list(q_data['options'][answer].values())[0]
    for cuisine in selected:
        state['cuisines'][cuisine] += 0.5
    
    state['current_question'] += 1
    ask_question(user_id, state['current_question'])

def show_results(user_id):
    state = user_states[user_id]
    sorted_cuisines = sorted(state['cuisines'].items(), key=lambda x: x[1], reverse=True)
    
    result_text = "🍴 Результаты вашего опроса:\n\n"
    for cuisine, score in sorted_cuisines:
        if score > 0:
            result_text += f"▫️ {cuisine}: {score} баллов\n"
    
    result_text += "\nТеперь вы можете создать комнату для выбора ресторана!"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Создать комнату 🏠", callback_data='create_room'))
    
    bot.send_message(user_id, result_text, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📌 Доступные команды:
/start - Начать работу с ботом
/help - Получить справку

🔍 Возможности:
- Пройти опрос о кулинарных предпочтениях
- Создать комнату для совместного выбора
- Найти рестораны по вашим предпочтениям
- Управлять своими настройками
"""
    bot.send_message(message.chat.id, help_text)

'''