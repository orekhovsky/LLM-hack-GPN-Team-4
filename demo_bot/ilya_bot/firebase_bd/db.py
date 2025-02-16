import random
import firebase_admin
from firebase_admin import credentials, db

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

def create_room(moderator_id: str):
    room_code = str(random.randint(1000, 9999))  # Генерация 4-значного кода
    ref = db.reference(f'/rooms/{room_code}')
    ref.set({
        'moderator': moderator_id,
        'users': {moderator_id: True},  # Добавляем создателя в комнату
        'votes': {},
        'is_voting_active': False
    })
    return room_code

def get_room(room_code: str):
    ref = db.reference(f'/rooms/{room_code}')
    return ref.get()

def join_room(user_id: str, room_code: str):
    room = get_room(room_code)
    if room:
        ref = db.reference(f'/rooms/{room_code}/users')
        ref.update({user_id: True})
        return True
    return False

def start_voting(room_code: str):
    ref = db.reference(f'/rooms/{room_code}')
    ref.update({'is_voting_active': True, 'votes': {}})
    
def vote_for_restaurant(room_code: str, user_id: str, restaurant: str):
    ref = db.reference(f'/rooms/{room_code}/votes')
    ref.update({user_id: restaurant})

def get_votes(room_code: str):
    ref = db.reference(f'/rooms/{room_code}/votes')
    return ref.get() or {}

def close_voting(room_code: str):
    ref = db.reference(f'/rooms/{room_code}')
    ref.update({'is_voting_active': False})
