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

def update_user(user_id: str, updates: dict):
    ref = db.reference(f'/users/{user_id}')
    ref.update(updates)

def delete_user(user_id: str):
    ref = db.reference(f'/users/{user_id}')
    ref.delete()

def create_room(user_data: dict):
    ref = db.reference('/rooms')
    new_room_ref = ref.push()
    new_room_ref.set(user_data)
    return new_room_ref.key

def get_room(room_id: str):
    ref = db.reference(f'/rooms/{room_id}')
    return ref.get()