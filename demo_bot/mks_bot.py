import telebot
from telebot import types
from firebase_bd import init_firebase, get_user, save_user
import config
from qstns import questions, cuisines
from firebase_admin import db
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
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Создать комнату 🏠", callback_data='create_room'),
        types.InlineKeyboardButton("Найти рестораны 🔍", callback_data='find_restaurants')
    )
    
    text = "Ваши предпочтения:\n" + "\n".join(
        [f"• {k}: {v} баллов" for k, v in user_data['cuisines'].items() if v > 0]
    )
    
    bot.send_message(user_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'start_quiz')
def start_quiz(call):
    user_id = str(call.message.chat.id)
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
    user_data = {
        'cuisines': state['cuisines'],
        'timestamp': datetime.datetime.now().isoformat()  # Локальное время
    }
    sorted_cuisines = sorted(state['cuisines'].items(), key=lambda x: x[1], reverse=True)
    
    result_text = "🍴 Результаты вашего опроса:\n\n"
    for cuisine, score in sorted_cuisines:
        if score > 0:
            result_text += f"▫️ {cuisine}: {score} баллов\n"
    
    result_text += "\nТеперь вы можете создать комнату для выбора ресторана!"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Создать комнату 🏠", callback_data='create_room'))
    
    bot.send_message(user_id, result_text, reply_markup=markup)
    save_user(user_id, user_data)

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