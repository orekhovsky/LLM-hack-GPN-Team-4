import telebot
from telebot import types
import config
from qstns import questions, cuisines
from firebase_bd import init_firebase, get_user, save_user, update_user, create_room

bot = telebot.TeleBot(config.token)
# init_firebase()

# Хранилище состояния пользователей
user_states = {}

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

bot.polling()