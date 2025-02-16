import telebot
from telebot import types
from firebase_bd import *
import firebase_admin
from firebase_admin import firestore
import config
from qstns import questions, cuisines, MOCK_RESTAURANTS
import datetime
import random
import string
from collections import defaultdict

# Инициализация Firebase
init_firebase()
bot = telebot.TeleBot(config.token)

# Хранилище состояния опроса (временное, пока не перенесем в Firebase)
user_states = {}

def get_room_keyboard():
    """Генерация клавиатуры со списком комнат"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    rooms_ref = db.reference('/rooms')
    all_rooms = rooms_ref.get() or {}
    
    for room_id in all_rooms.keys():
        markup.add(types.KeyboardButton(f"Комната {room_id}"))
    return markup if all_rooms else None

@bot.message_handler(commands=['start'])
def welcome(message):
    """Обработчик команды /start"""
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text='Можем начинать', callback_data='start_quiz')
    markup.add(btn)
    
    if user_data:
        show_main_menu(user_id, user_data)
    else:
        bot.send_message(
            user_id,
            "Приветствую! Я — Dorcia, ваш помощник в выборе ресторанов. 🍽\n"
            "Чтобы я мог предложить подходящие варианты, расскажите мне о ваших кулинарных предпочтениях.\n"
            "Ответьте, пожалуйста, на несколько коротких вопросов.",
            reply_markup=markup
        )

def show_main_menu(user_id, user_data):
    """Отображение главного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('Создать комнату 🏠')
    btn2 = types.KeyboardButton('Найти рестораны 🔍')
    btn3 = types.KeyboardButton('Мои предпочтения �')
    btn4 = types.KeyboardButton('Присоединиться к комнате 👋🏻')
    markup.add(btn1, btn2, btn3, btn4)
    
    text = (
        "Уточните, пожалуйста, ищите ли вы место для себя или планируете поход в ресторан с компанией?\n\n"
        "1. Для одного: Нажмите *«Найти рестораны»* – эта опция подберет список лучших заведений, подходящих под ваши "
        "критерии. Вы сможете ознакомиться с оценкой, рейтингами, средним чеком и выбрать идеальное место для своего визита.\n\n"
        "2. Для компании: Если вы хотите провести время в кругу друзей или коллег, у нас есть два варианта:\n"
        "- *«Создать новую комнату»*: Выберите эту опцию, чтобы организовать свою собственную встречу. Мы предоставим вам все "
        "необходимые инструменты для приглашения гостей и координации мероприятия.\n"
        "- *«Присоединиться к комнате»*: Уже существует комната, в которую вы бы хотели вступить? Введите код комнаты, чтобы стать "
        "частью встречи.\n\n"
        "Не забудьте, что вы всегда можете изменить свои предпочтения в еде для подбора релевантных ресторанов. Для этого "
        "перейдите по кнопке *«Мои предпочтения»* и нажмите *«Пройти заново»*."
    )
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == 'Мои предпочтения 🍽')
def show_preferences(message):
    """Отображение текущих предпочтений пользователя"""
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    
    if user_data:
        sorted_cuisines = sorted(user_data['cuisines'].items(), 
                               key=lambda x: x[1], 
                               reverse=True)
        
        result_text = "🍴 Ваши текущие предпочтения:\n\n"
        for cuisine, score in sorted_cuisines:
            if score > 0:
                result_text += f"▫️ {cuisine}: {score} баллов\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("В главное меню", callback_data='main_menu'),
            types.InlineKeyboardButton("Обновить", callback_data='restart_quiz')
        )
        
        bot.send_message(user_id, result_text, reply_markup=markup)
    else:
        bot.send_message(user_id, "Вы еще не проходили опрос!")

@bot.callback_query_handler(func=lambda call: call.data == 'start_quiz')
def start_quiz(call):
    """Запуск опроса"""
    user_id = str(call.message.chat.id)
    user_states[user_id] = {
        'current_question': 0,
        'cuisines': {k: 0 for k in cuisines},
        'follow_up': None,
        'current_message_id': None
    }
    ask_question(user_id, 0)

def ask_question(user_id, question_num):
    """Задаем вопрос пользователю"""
    state = user_states[user_id]
    
    if question_num >= len(questions):
        try:
            bot.delete_message(user_id, state['current_message_id'])
        except Exception as e:
            print(f"Ошибка удаления сообщения: {e}")
        return show_results(user_id)
    
    q_data = questions[question_num]
    markup = types.InlineKeyboardMarkup()
    
    for key, value in q_data['options'].items():
        btn_text = list(value.keys())[0]
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'answer_{question_num}_{key}'))
    
    if state['current_message_id']:
        try:
            msg = bot.edit_message_text(
                chat_id=user_id,
                message_id=state['current_message_id'],
                text=q_data['question'],
                reply_markup=markup
            )
        except:
            msg = bot.send_message(user_id, q_data['question'], reply_markup=markup)
            state['current_message_id'] = msg.message_id
    else:
        msg = bot.send_message(user_id, q_data['question'], reply_markup=markup)
        state['current_message_id'] = msg.message_id
    
    user_states[user_id] = state

@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
def handle_answer(call):
    """Обработка ответов на вопросы"""
    user_id = str(call.message.chat.id)
    data = call.data.split('_')
    q_num = int(data[1])
    answer = data[2]
    state = user_states[user_id]
    
    # Обновление баллов
    selected = list(questions[q_num]['options'][answer].values())[0]
    for cuisine in selected:
        state['cuisines'][cuisine] += 1
    
    # Переход к следующему вопросу
    state['current_question'] += 1
    ask_question(user_id, state['current_question'])

def show_results(user_id):
    """Показ результатов опроса"""
    state = user_states[user_id]
    user_data = {
        'cuisines': state['cuisines'],
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    sorted_cuisines = sorted(user_data['cuisines'].items(), 
                           key=lambda x: x[1], 
                           reverse=True)
    
    result_text = "🍴 Новые результаты опроса:\n\n"
    for cuisine, score in sorted_cuisines:
        if score > 0:
            result_text += f"▫️ {cuisine}: {score} баллов\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("В меню", callback_data='main_menu'),
        types.InlineKeyboardButton("Заново", callback_data='restart_quiz')
    )
    
    bot.send_message(user_id, result_text, reply_markup=markup)
    save_user(user_id, user_data)

@bot.callback_query_handler(func=lambda call: call.data in ['main_menu', 'restart_quiz'])
def handle_menu_actions(call):
    """Обработка действий в меню"""
    user_id = str(call.message.chat.id)
    if call.data == 'main_menu':
        user_data = get_user(user_id)
        show_main_menu(user_id, user_data)
    elif call.data == 'restart_quiz':
        user_states[user_id] = {
            'current_question': 0,
            'cuisines': {k: 0 for k in cuisines},
            'follow_up': None,
            'current_message_id': None
        }
        ask_question(user_id, 0)


@bot.message_handler(func=lambda message: message.text == 'Создать комнату 🏠')
def handle_create_room(message):
    """Обработчик кнопки 'Создать комнату'"""
    create_room_command(message)

@bot.message_handler(commands=['create_room'])
def create_room_command(message):
    """Создание новой комнаты"""
    user_id = str(message.chat.id)
    room_data = {
        "moderator": user_id,
        "members": [user_id],
        "status": "waiting",
        "params": {},
        "votes": {},
        "restaurants": []
    }
    
    room_id = create_room(room_data)
    update_user(user_id, {"current_room": room_id})
    
    bot.send_message(user_id, f"✅ Комната {room_id} создана! Код для участников: *{room_id}*", 
                    parse_mode="Markdown")
    ask_additional_params(user_id, room_id)

@bot.message_handler(func=lambda message: message.text == 'Присоединиться к комнате 👋🏻')
def join_room_command(message):
    """Присоединение к комнате по 4-значному коду"""
    user_id = str(message.chat.id)
    bot.send_message(user_id, "Введите 4-значный код комнаты:")
    bot.register_next_step_handler(message, process_room_code)

def process_room_code(message):
    """Обработка введенного кода комнаты"""
    user_id = str(message.chat.id)
    room_code = message.text.strip()
    
    try:
        # Проверка формата кода
        if not room_code.isdigit() or len(room_code) != 4:
            bot.send_message(user_id, "❌ Неверный формат кода! Код должен состоять из 4 цифр.")
            return
        
        # Проверка существования комнаты
        room = get_room(room_code)
        if not room:
            bot.send_message(user_id, "❌ Комната не найдена!")
            return
        
        # Проверка, что пользователь уже не в комнате
        if user_id in room.get('members', []):
            bot.send_message(user_id, "ℹ️ Вы уже в этой комнате!")
            return
        
        # Добавляем пользователя в комнату
        add_user_to_room(room_code, user_id)
        update_user(user_id, {"current_room": room_code})
        
        bot.send_message(user_id, f"✅ Вы присоединились к комнате с кодом {room_code}!")
    except Exception as e:
        bot.send_message(user_id, "❌ Произошла ошибка при присоединении к комнате. Попробуйте позже.")
        print(f"Ошибка: {e}")


def ask_additional_params(user_id: str, room_id: str):
    """Запрос дополнительных параметров"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('До 500 ₽', '500-1000 ₽', 'Свыше 1000 ₽')
    msg = bot.send_message(user_id, "💸 Средний чек на человека:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: process_price_step(m, room_id))

def process_price_step(message, room_id: str):
    """Обработка выбора ценового диапазона"""
    user_id = str(message.chat.id)
    price = message.text.strip()
    
    # Проверка ввода
    if price not in ['До 500 ₽', '500-1000 ₽', 'Свыше 1000 ₽']:
        bot.send_message(user_id, "❌ Пожалуйста, выберите один из предложенных вариантов.")
        return ask_additional_params(user_id, room_id)  # Повторный запрос
    
    try:
        update_room(room_id, {f'params/{user_id}/price': price})
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('<30 мин', '30-60 мин', '>1 часа')
        msg = bot.send_message(user_id, "⏳ Время на обед:", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda m: process_time_step(m, room_id))
    except Exception as e:
        bot.send_message(user_id, "❌ Произошла ошибка при сохранении данных. Попробуйте позже.")
        print(f"Ошибка: {e}")

def process_time_step(message, room_id: str):
    """Обработка выбора времени и запуск голосования"""
    user_id = str(message.chat.id)
    time = message.text.strip()
    
    # Проверка ввода
    if time not in ['<30 мин', '30-60 мин', '>1 часа']:
        bot.send_message(user_id, "❌ Пожалуйста, выберите один из предложенных вариантов.")
        return ask_additional_params(user_id, room_id)  # Повторный запрос
    
    try:
        # Сохраняем время на обед
        update_room(room_id, {f'params/{user_id}/time': time})
        bot.send_message(user_id, "✅ Настройки сохранены!")
        
        # Отправляем кнопку "Готовы!"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Готовы!", callback_data=f"start_voting_{room_id}"))
        bot.send_message(user_id, "Нажмите *Готовы!*, чтобы начать голосование.", reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(user_id, "❌ Произошла ошибка при сохранении данных. Попробуйте позже.")
        print(f"Ошибка: {e}")

@bot.message_handler(func=lambda message: message.text.startswith("Комната"))
def enter_room(message):
    """Вход в комнату"""
    user_id = str(message.chat.id)
    room_id = message.text.split()[-1]
    room = get_room(room_id)
    
    if not room:
        bot.send_message(user_id, "❌ Комната не найдена!")
        return
    
    if user_id not in room.get('members', []):
        add_user_to_room(room_id, user_id)
        update_user(user_id, {"current_room": room_id})
        bot.send_message(user_id, f"✅ Вы в комнате {room_id}!")
    else:
        bot.send_message(user_id, "ℹ️ Вы уже в этой комнате!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_voting_'))
def start_voting(call):
    room_id = call.data.split('_')[-1]
    user_id = str(call.from_user.id)
    room = get_room(room_id)
    
    # Проверка, что модератор в списке участников
    if user_id not in room.get('members', []):
        bot.answer_callback_query(call.id, "❌ Вы не в этой комнате!")
        return
    
    # Запуск голосования
    update_room(room_id, {'status': 'voting'})
    for uid in room.get('members', []):
        try:
            send_voting_interface(uid, room_id)
        except Exception as e:
            print(f"Ошибка отправки для {uid}: {e}")

def send_voting_interface(user_id: str, room_id: str, offset=0):
    """Отправка интерфейса голосования"""
    room = get_room(room_id)
    if not room:
        return
    
    markup = types.InlineKeyboardMarkup()
    restaurants = room.get('restaurants', [])
    votes = room.get('votes', {})
    
    # Выводим топ-5 ресторанов (с учетом offset)
    for rest in restaurants[offset:offset+5]:
        vote_count = votes.get(rest, 0)
        markup.add(types.InlineKeyboardButton(
            f"{rest} ({vote_count})", 
            callback_data=f"vote_{room_id}_{rest}"
        ))
    
    # Если есть еще рестораны, добавляем кнопку "Пополнить список ➕"
    if len(restaurants) > offset + 5:
        markup.add(types.InlineKeyboardButton(
            "Пополнить список ➕", 
            callback_data=f"more_rest_{room_id}_{offset+5}"
        ))
    
    try:
        bot.send_message(user_id, "🏆 Голосование за рестораны:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote(call):
    """Обработка голосования"""
    _, room_id, rest = call.data.split('_', 2)
    user_id = str(call.from_user.id)
    room = get_room(room_id)
    
    if not room or user_id in room.get('voted', []):
        bot.answer_callback_query(call.id, "❌ Вы уже голосовали!")
        return
    
    # Обновляем голоса в Firebase
    new_votes = room.get('votes', {})
    new_votes[rest] = new_votes.get(rest, 0) + 1
    update_room(room_id, {
        'votes': new_votes,
        'voted': firestore.ArrayUnion([user_id])
    })
    
    # Обновляем интерфейс голосования для всех участников
    for uid in room.get('members', []):
        send_voting_interface(uid, room_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('more_rest_'))
def add_more_restaurants(call):
    """Добавление следующих ресторанов в список"""
    data = call.data.split('_')
    room_id = data[2]
    offset = int(data[3])  # Смещение для отображения следующих ресторанов
    
    # Отправляем обновленный интерфейс голосования
    send_voting_interface(call.from_user.id, room_id, offset)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Справка по командам"""
    help_text = """
📌 Доступные команды:
/start - Начать работу
/help - Справка
/create_room - Создать комнату

🔍 Основные функции:
- Опрос предпочтений
- Совместный выбор ресторана
- Голосование в режиме реального времени
"""
    bot.send_message(message.chat.id, help_text)

if __name__ == '__main__':
    print("✅ Бот запущен!")
    bot.polling(none_stop=True)