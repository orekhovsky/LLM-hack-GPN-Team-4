import telebot
from telebot import types
from firebase_bd import init_firebase, get_user, save_user, create_room, get_room, join_room, start_voting, vote_for_restaurant, get_votes, close_voting

import config
from qstns import questions, cuisines
import datetime

# Инициализация Firebase
init_firebase()
bot = telebot.TeleBot(config.token)

# Рестораны для голосования (можно заменить API-подбором)
RESTAURANTS = ["La Piazza", "Sakura Sushi", "Texas BBQ"]

# Хранилище текущих состояний комнат
user_rooms = {}

# Хранилище состояния опроса
user_states = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text='Можем начинать', callback_data='start_quiz')
    markup.add(btn)
    
    if user_data and 'cuisines' in user_data and user_data['cuisines']:
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
    # Изменено: Исправлен тип клавиатуры и callback_data
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("Создать комнату 🏠")
    btn2 = types.KeyboardButton('Найти рестораны 🔍')
    btn3 = types.KeyboardButton('Мои предпочтения 🍽')
    btn4 = types.KeyboardButton('Присоединиться к комнате 👋🏻')
    markup.add(btn1, btn2, btn3, btn4)
    
    text = "Главное меню:"
    bot.send_message(user_id, text, reply_markup=markup)

# Добавлено: Обработчик для кнопки "Мои предпочтения"
@bot.message_handler(func=lambda message: message.text == 'Мои предпочтения 🍽')
def show_preferences(message):
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
        markup.add(types.InlineKeyboardButton("Перейти в меню", callback_data='main_menu'),
                 types.InlineKeyboardButton("Обновить предпочтения", callback_data='restart_quiz'))
        
        bot.send_message(user_id, result_text, reply_markup=markup)
    else:
        bot.send_message(user_id, "Вы еще не проходили опрос!")

@bot.callback_query_handler(func=lambda call: call.data == 'start_quiz')
def start_quiz(call):
    user_id = str(call.message.chat.id)
    # Изменено: Очистка предыдущих данных при повторном прохождении
    user_states[user_id] = {
        'current_question': 0,
        'cuisines': {k: 0 for k in cuisines},
        'follow_up': None
    }
    ask_question(user_id, 0)

def ask_question(user_id, question_num):
    state = user_states[user_id]
    
    if question_num >= len(questions):
        return show_results(user_id)
    
    if state['follow_up']:
        q_data = state['follow_up']
        state['follow_up'] = None
    else:
        q_data = questions[question_num]
    
    markup = types.InlineKeyboardMarkup()
    for key, value in q_data['options'].items():
        btn_text = list(value.keys())[0]
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'answer_{question_num}_{key}'))
    
    bot.send_message(user_id, q_data['question'], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
def handle_answer(call):
    user_id = str(call.message.chat.id)
    data = call.data.split('_')
    q_num = int(data[1])
    answer = data[2]
    state = user_states[user_id]
    
    # Обновление баллов
    selected = list(questions[q_num]['options'][answer].values())[0]
    for cuisine in selected:
        state['cuisines'][cuisine] += 1
    
    # Обработка уточняющих вопросов
    if 'follow_up' in questions[q_num] and answer in questions[q_num]['follow_up']:
        state['follow_up'] = questions[q_num]['follow_up'][answer]
        ask_question(user_id, q_num)
    else:
        state['current_question'] += 1
        ask_question(user_id, state['current_question'])

def show_results(user_id):
    state = user_states[user_id]
    # Изменено: Добавлено обновление данных вместо создания новых
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
        types.InlineKeyboardButton("В главное меню", callback_data='main_menu'),
        types.InlineKeyboardButton("Пройти заново", callback_data='restart_quiz')
    )
    
    bot.send_message(user_id, result_text, reply_markup=markup)
    save_user(user_id, user_data) 

@bot.callback_query_handler(func=lambda call: call.data in ['main_menu', 'restart_quiz'])
def handle_menu_actions(call):
    user_id = str(call.message.chat.id)
    if call.data == 'main_menu':
        user_data = get_user(user_id)
        show_main_menu(user_id, user_data)
    elif call.data == 'restart_quiz':
        # Очистка предыдущих результатов и запуск опроса
        user_states[user_id] = {
            'current_question': 0,
            'cuisines': {k: 0 for k in cuisines},
            'follow_up': None
        }
        ask_question(user_id, 0)
@bot.message_handler(func=lambda message: message.text == "Создать комнату 🏠")
def create_room_handler(message):
    user_id = str(message.chat.id)
    room_code = create_room(user_id)
    user_rooms[user_id] = room_code

    markup = types.InlineKeyboardMarkup()
    btn_start = types.InlineKeyboardButton("Начать голосование", callback_data=f"start_voting_{room_code}")
    markup.add(btn_start)

    bot.send_message(user_id, f"✅ Ваша комната создана! Код комнаты: *{room_code}*.\nОтправьте его друзьям, чтобы они присоединились.", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Присоединиться к комнате 👋🏻")
def join_room_handler(message):
    msg = bot.send_message(message.chat.id, "Введите 4-значный код комнаты:")
    bot.register_next_step_handler(msg, process_join_room)

def process_join_room(message):
    user_id = str(message.chat.id)
    room_code = message.text.strip()

    if join_room(user_id, room_code):
        user_rooms[user_id] = room_code
        bot.send_message(user_id, f"🎉 Вы успешно присоединились к комнате *{room_code}*! Ждите начала голосования.", parse_mode="Markdown")
    else:
        bot.send_message(user_id, "❌ Ошибка! Проверьте код и попробуйте снова.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("start_voting_"))
def start_voting_handler(call):
    user_id = str(call.message.chat.id)
    room_code = call.data.split("_")[2]

    if user_id in user_rooms and user_rooms[user_id] == room_code:
        start_voting(room_code)

        markup = types.InlineKeyboardMarkup()
        for restaurant in RESTAURANTS:
            markup.add(types.InlineKeyboardButton(restaurant, callback_data=f"vote_{room_code}_{restaurant}"))

        bot.send_message(call.message.chat.id, "🍽 Голосование началось! Выберите ресторан:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "❌ Только создатель комнаты может запустить голосование.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def vote_handler(call):
    user_id = str(call.message.chat.id)
    _, room_code, restaurant = call.data.split("_")

    vote_for_restaurant(room_code, user_id, restaurant)
    bot.send_message(user_id, f"✅ Вы проголосовали за *{restaurant}*.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "Завершить голосование")
def end_voting_handler(message):
    user_id = str(message.chat.id)
    room_code = user_rooms.get(user_id)

    if not room_code:
        bot.send_message(user_id, "❌ Вы не являетесь модератором комнаты.")
        return

    votes = get_votes(room_code)
    close_voting(room_code)

    results = {}
    for choice in votes.values():
        results[choice] = results.get(choice, 0) + 1

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    result_text = "📊 *Результаты голосования:*\n\n"
    for place, (restaurant, count) in enumerate(sorted_results, 1):
        result_text += f"{place}. {restaurant} - {count} голос(ов)\n"

    winner = sorted_results[0][0] if sorted_results else "Нет голосов"
    result_text += f"\n🏆 *Выбран ресторан:* {winner}!"

    bot.send_message(user_id, result_text, parse_mode="Markdown")
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

if __name__ == '__main__':
    print("Бот успешно запущен!")
    bot.polling(none_stop=True)