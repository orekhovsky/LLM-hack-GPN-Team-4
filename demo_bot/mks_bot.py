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

init_firebase()
bot = telebot.TeleBot(config.token)

# Хранилище состояния опроса (временное, пока не перенесем в Firebase)
user_states = {}

# ------------------------ ОСНОВНЫЕ КОМАНДЫ ------------------------

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
    btn3 = types.KeyboardButton('Мои предпочтения 🍽')
    btn4 = types.KeyboardButton('Присоединиться к комнате 👋🏻')
    markup.add(btn1, btn2, btn3, btn4)
    
    text = ''' Как здорово снова встретиться с вами! Я — *Dorcia*, ваш помощник в выборе ресторанов. 🍽

                                    *Ваш вкус- наш выбор*
    '''
        
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

# ------------------------ ОПРОС ПОЛЬЗОВАТЕЛЯ ------------------------

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


# ======================= ОДИНОЧНЫЙ ПОИСК ==========================
@bot.message_handler(func=lambda message: message.text == 'Найти рестораны 🔍')
def handle_solo_search(message):
    """Новая функция: запуск одиночного поиска"""
    user_id = str(message.chat.id)
    user_states[user_id] = {'mode': 'solo', 'step': 'price'}
    ask_price_step(user_id)

def ask_price_step(user_id):
    """Запрос ценового диапазона"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('До 500 ₽', '500-1000 ₽', 'Свыше 1000 ₽')
    bot.send_message(user_id, "💸 Средний чек на человека:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id), {}).get('step') == 'price')
def process_solo_price(message):
    """Обработка цены для одиночного поиска"""
    user_id = str(message.chat.id)
    price_map = {
        'До 500 ₽': (0, 500),
        '500-1000 ₽': (501, 1000),
        'Свыше 1000 ₽': (1001, 5000)
    }
    
    if message.text not in price_map:
        bot.send_message(user_id, "❌ Выберите вариант из кнопок!")
        return ask_price_step(user_id)
    
    user_states[user_id]['price'] = price_map[message.text]
    user_states[user_id]['step'] = 'time'
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('<30 мин', '30-60 мин', '>1 часа')
    bot.send_message(user_id, "⏳ Время на обед:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id), {}).get('step') == 'time')
def process_solo_time(message):
    """Обработка времени для одиночного поиска"""
    user_id = str(message.chat.id)
    if message.text not in ['<30 мин', '30-60 мин', '>1 часа']:
        bot.send_message(user_id, "❌ Выберите вариант из кнопок!")
        return
    
    user_states[user_id]['time'] = message.text
    user_states[user_id]['step'] = 'cuisine'
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Итальянская', 'Японская', 'Кафе', 'Ресторан', 'Пиццерия', 'Другое')
    bot.send_message(user_id, "🍽 Предпочтения по кухне/типу:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(str(message.chat.id), {}).get('step') == 'cuisine')
def process_solo_cuisine(message):
    """Обработка кухни и вывод результатов"""
    user_id = str(message.chat.id)
    cuisine = message.text
    filters = user_states[user_id]
    
    # Фильтрация ресторанов
    filtered = [
        r for r in MOCK_RESTAURANTS 
        if filters['price'][0] <= r['avg_price'] <= filters['price'][1]
    ]
    
    if cuisine != 'Другое':
        filtered = [r for r in filtered if cuisine.lower() in r['name'].lower()]
    
    if not filtered:
        bot.send_message(user_id, "😞 По вашему запросу ничего не найдено")
        return
    
    # Формирование сообщения с результатами
    response = "🍴 Найденные рестораны:\n\n"
    for i, rest in enumerate(filtered[:5], 1):
        response += (
            f"{i}. {rest['name']}\n"
            f"   Средний чек: {rest['avg_price']} ₽\n"
            f"   Рейтинг: {rest['rating']} ★\n\n"
        )
    
    bot.send_message(user_id, response)


# ------------------------ ЛОГИКА КОМНАТ ---------------------------

@bot.message_handler(func=lambda message: message.text == 'Создать комнату 🏠')
def handle_create_room(message):
    """Создание комнаты"""
    user_id = str(message.chat.id)
    
    # Генерация уникального кода комнаты
    room_code = str(random.randint(1000, 9999))
    while get_room(room_code):
        room_code = str(random.randint(1000, 9999))
    
    # Создаем комнату в Firebase
    room_data = {
        'moderator': user_id,
        'members': {user_id: True},
        'status': 'waiting',
        'votes': {},
        'restaurants': [r['name'] for r in MOCK_RESTAURANTS],
        'created_at': datetime.datetime.now().isoformat()
    }
    
    create_room(room_data, room_code)
    update_user(user_id, {'current_room': room_code})
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать голосование", callback_data='start_voting'))
    
    bot.send_message(
        user_id, 
        f"✅ Комната *{room_code}* создана!\n\n"
        "Участники могут присоединиться с помощью кода.\n"
        "Нажмите кнопку ниже чтобы начать голосование.",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == 'Присоединиться к комнате 👋🏻')
def join_room_command(message):
    """Присоединение к комнате"""
    user_id = str(message.chat.id)
    bot.send_message(user_id, "Введите 4-значный код комнаты:")
    bot.register_next_step_handler(message, process_room_code)

def process_room_code(message):
    """Обработка кода комнаты"""
    user_id = str(message.chat.id)
    room_id = message.text.strip()

    if not room_id.isdigit() or len(room_id) != 4:
        return bot.send_message(user_id, "❌ Неверный формат кода!")

    try:
        room = get_room(room_id)
        if not room:
            return bot.send_message(user_id, "❌ Комната не найдена!")
        
        if user_id in room.get('members', {}):
            return bot.send_message(user_id, "ℹ️ Вы уже в этой комнате!")
        
        if room.get('status') != 'waiting':
            return bot.send_message(user_id, "❌ Голосование уже началось!")

        # Добавляем пользователя в комнату
        add_user_to_room(room_id, user_id)
        update_user(user_id, {'current_room': room_id})
        
        # Уведомляем модератора
        moderator_id = room['moderator']
        bot.send_message(
            moderator_id,
            f"✅ Пользователь @{message.from_user.username} присоединился к комнате!"
        )
        
        bot.send_message(user_id, f"✅ Вы присоединились к комнате {room_id}!")
    except Exception as e:
        print(f"Ошибка присоединения: {e}")
        bot.send_message(user_id, "❌ Ошибка при присоединении. Попробуйте позже.")

@bot.callback_query_handler(func=lambda call: call.data == 'start_voting')
def start_voting_handler(call):
    """Запуск голосования"""
    user_id = str(call.message.chat.id)
    user_data = get_user(user_id)
    room_id = user_data.get('current_room')
    
    if not room_id:
        return bot.send_message(user_id, "❌ Вы не в комнате!")
    
    room = get_room(room_id)
    if not room or room['moderator'] != user_id:
        return bot.send_message(user_id, "❌ Только модератор может начать голосование!")
    
    # Обновляем статус комнаты
    update_room(room_id, {'status': 'voting', 'votes': {}})
    
    # Рассылаем интерфейс голосования
    members = room.get('members', {}).keys()
    for member_id in members:
        try:
            send_voting_interface(member_id, room_id)
        except Exception as e:
            print(f"Ошибка отправки для {member_id}: {e}")

def send_voting_interface(user_id: str, room_id: str):
    """Отправка интерфейса голосования"""
    room = get_room(room_id)
    if not room:
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for rest in room.get('restaurants', []):
        markup.add(types.KeyboardButton(rest))
    markup.add(types.KeyboardButton("Завершить голосование ❌"))
    
    bot.send_message(
        user_id, 
        "🗳 *Голосование началось!*\nВыберите ресторан из списка:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text in MOCK_RESTAURANTS)
def vote_handler(message):
    """Обработка голосования"""
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    room_id = user_data.get('current_room')
    
    if not room_id:
        return bot.send_message(user_id, "❌ Вы не в комнате!")
    
    room = get_room(room_id)
    if not room or room['status'] != 'voting':
        return bot.send_message(user_id, "❌ Голосование не активно!")
    
    # Обновляем голоса в Firebase
    votes = room.get('votes', {})
    votes[user_id] = message.text
    update_room(room_id, {'votes': votes})
    
    bot.send_message(user_id, "✅ Ваш голос учтен!")

@bot.message_handler(func=lambda message: message.text == "Завершить голосование ❌")
def finish_voting_handler(message):
    """Завершение голосования"""
    user_id = str(message.chat.id)
    user_data = get_user(user_id)
    room_id = user_data.get('current_room')
    
    if not room_id:
        return bot.send_message(user_id, "❌ Вы не в комнате!")
    
    room = get_room(room_id)
    if not room or room['moderator'] != user_id:
        return bot.send_message(user_id, "❌ Только модератор может завершить голосование!")
    
    # Подсчет результатов
    votes = room.get('votes', {})
    results = defaultdict(int)
    for rest in votes.values():
        results[rest] += 1
    
    # Формируем текст результатов
    result_text = "📊 *Результаты голосования:*\n\n"
    for rest, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        result_text += f"🍽 *{rest}* — {count} голосов\n"
    
    # Рассылаем результаты
    members = room.get('members', {}).keys()
    for member_id in members:
        try:
            bot.send_message(
                member_id, 
                result_text + "\nКомната автоматически закрывается через 2 минуты.",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки для {member_id}: {e}")
    
    # Закрываем комнату через 2 минуты
    close_room_with_delay(room_id)

def close_room_with_delay(room_id: str):
    """Закрытие комнаты с задержкой"""
    import threading
    from time import sleep
    
    def closer():
        sleep(120)
        room = get_room(room_id)
        if not room:
            return
        
        # Удаляем комнату
        delete_room(room_id)
        
        # Удаляем привязку к комнате у пользователей
        members = room.get('members', {}).keys()
        for member_id in members:
            update_user(member_id, {'current_room': None})
        
        # Уведомляем участников
        for member_id in members:
            try:
                bot.send_message(member_id, "🚪 Комната автоматически закрыта!")
            except Exception as e:
                print(f"Ошибка уведомления {member_id}: {e}")
    
    thread = threading.Thread(target=closer)
    thread.start()
# ------------------------ ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ------------------------


@bot.message_handler(commands=['info'])
def info_command(message):
    '''Информация про функционал бота'''
    info_text = '''
    🔍 Основные функции бота:

    - Опрос предпочтений
    - Совместный выбор ресторана
    - Голосование в реальном времени

    Как работает бот?

    1. Для одного:  
    Если вы ищете место для себя, выберите опцию «Найти рестораны».
    Бот предложит вам список лучших заведений, соответствующих вашим предпочтениям. 
    Вы сможете увидеть оценку, средний чек, время в пути и выбрать идеальный ресторан для посещения.

    2. Для компании:  
    Если вы планируете поход в ресторан с друзьями или коллегами, доступны следующие варианты:
    
    - Создать новую комнату:  
        Эта опция позволит вам организовать собственное мероприятие. 
        Вы получите необходимые инструменты для приглашения гостей и координации встречи.
        
    - Присоединиться к комнате:  
        Если уже создана комната, к которой вы хотите присоединиться, введите её код, чтобы стать частью встречи.

    Изменение предпочтений:

    Вы всегда можете изменить свои вкусовые предпочтения, чтобы получать более подходящие предложения от бота. 
    Для этого перейдите в раздел «Мои предпочтения» и выберите пункт «Пройти заново».

    '''
    bot.send_message(message.chat.id, info_text)


@bot.message_handler(commands=['feedback'])
def feedback_command(message):
    '''Обратная связь'''
    feedback_text = '''
    Мы всегда рады услышать ваше мнение! 
    Если у вас есть идеи, пожелания или вы хотите выразить благодарность нашей команде, пожалуйста, оставьте свои комментарии ниже. 
    Мы ценим каждое мнение и стараемся сделать наш сервис лучше для вас! 😊
    '''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Отменить отправку ❌"))
    
    msg = bot.reply_to(
        message, 
        feedback_text, 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
    '''Обработка отзыва'''
    if message.text == "Отменить отправку ❌":
        bot.send_message(message.chat.id, "Отмена.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    if not message.text:
        bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте текст.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    try:
        # Пересылаем сообщение в чат разработчиков
        bot.send_message(
            config.DEVELOPER_CHAT_ID,
            f"📝 Новый отзыв от @{message.from_user.username} ({user_name}):\n\n{message.text}"
        )
        
        # Подтверждение пользователю
        bot.send_message(user_id, "✅ Спасибо! Ваш отзыв отправлен разработчикам.", reply_markup=types.ReplyKeyboardRemove())
        
    except Exception as e:
        print(f"Ошибка отправки отзыва: {e}")
        bot.send_message(user_id, "❌ Не удалось отправить отзыв. Попробуйте позже.", reply_markup=types.ReplyKeyboardRemove())    

@bot.message_handler(commands=['id'])
def get_chat_id(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"ID этого чата: `{chat_id}`", parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_command(message):
    """Справка по командам"""
    help_text = """
    📌 Доступные команды:
    /start - Начать работу
    /help - Справка
    /create_room - Создать комнату
    /join_room - Присоединиться к комнате
    /info - Описание функционала бота
    /feedback - Обратная связь / Пожелания / Благодарности команде авторов
    """
    bot.send_message(message.chat.id, help_text)

if __name__ == '__main__':
    print("✅ Бот запущен!")
    bot.polling(none_stop=True)