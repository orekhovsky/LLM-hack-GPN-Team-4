# db.py
import firebase_admin
from firebase_admin import credentials, db
import random

def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase-key.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://gpncamp-default-rtdb.firebaseio.com/'
            })
            print("Firebase initialized successfully!")
    except Exception as e:
        print(f"Firebase init error: {e}")
        raise

def get_user(user_id: str):
    ref = db.reference(f'/users/{user_id}')
    return ref.get()

def save_user(user_id: str, data: dict):
    ref = db.reference(f'/users/{user_id}')
    ref.set(data)
    return user_id

def update_user(user_id: str, updates: dict):
    ref = db.reference(f'/users/{user_id}')
    ref.update(updates)

def delete_user(user_id: str):
    ref = db.reference(f'/users/{user_id}')
    ref.delete()

def get_room(room_id: str):
    ref = db.reference(f'/rooms/{room_id}')
    return ref.get()

def update_room(room_id: str, updates: dict):
    ref = db.reference(f'/rooms/{room_id}')
    ref.update(updates)

def delete_room(room_id: str):
    ref = db.reference(f'/rooms/{room_id}')
    ref.delete()

def add_user_to_room(room_id: str, user_id: str):
    ref = db.reference(f'/rooms/{room_id}/members')
    ref.update({user_id: True})

def remove_user_from_room(room_id: str, user_id: str):
    ref = db.reference(f'/rooms/{room_id}/users')
    users = ref.get() or []
    if user_id in users:
        users.remove(user_id)
        ref.set(users)

def generate_room_code():
    """Генерация 4-значного кода комнаты"""
    return str(random.randint(1000, 9999))

def create_room(room_data: dict):
    """Создание комнаты с 4-значным кодом"""
    ref = db.reference('/rooms')
    
    # Генерация уникального 4-значного кода
    while True:
        room_code = generate_room_code()
        if not ref.child(room_code).get():  # Проверяем, что код уникален
            break
    
    room_code = generate_room_code()
    room_data["members"] = [room_data["moderator"]]  # Добавляем модератора в участники
    ref.child(room_code).set(room_data)
    return room_code

def update_room_votes(room_id: str, rest: str, user_id: str):
    ref = db.reference(f'/rooms/{room_id}')
    room = ref.get() or {}
    
    # Обновляем голоса
    votes = room.get('votes', {})
    votes[rest] = votes.get(rest, 0) + 1
    
    # Обновляем список проголосовавших
    voted = room.get('voted', [])
    if user_id not in voted:
        voted.append(user_id)
    
    ref.update({
        'votes': votes,
        'voted': voted
    })
