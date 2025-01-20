import json
import os

DATA_FILE = 'user_data.json'

def save_user_data(user_id, city):
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as file:
                data = json.load(file)
        else:
            data = {}
        
        data[user_id] = {'city': city}

        with open(DATA_FILE, 'w') as file:
            json.dump(data, file)
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователя: {e}")

def load_user_data(user_id):
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as file:
                data = json.load(file)
            return data.get(str(user_id))
        else:
            return None
    except Exception as e:
        print(f"Ошибка при загрузке данных пользователя: {e}")
        return None
