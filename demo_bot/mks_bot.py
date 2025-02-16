import telebot
from telebot import types
from firebase_bd import init_firebase, get_user, save_user
import config
from qstns import questions, cuisines
import datetime

# Инициализация Firebase
init_firebase()
bot = telebot.TeleBot(config.token)

# Хранилище состояния опроса
user_states = {}

@bot.message_handler(commands=['start'])
def welcome(message):
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