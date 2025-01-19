import os
import json

USER_DATA_FILE = 'user_data.json'

def save_user_data(user_id, city):
    data = {}
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
    
    data[str(user_id)] = {'city': city}

    with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def load_user_data(user_id):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get(str(user_id), None)
    return None
