import json
import os

ROOMS_FILE = "rooms.json"
USERS_FILE = "users.json"

def load_data(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_rooms():
    return load_data(ROOMS_FILE)

def save_rooms(rooms):
    save_data(ROOMS_FILE, rooms)

def get_users():
    return load_data(USERS_FILE)

def save_users(users):
    save_data(USERS_FILE, users)
