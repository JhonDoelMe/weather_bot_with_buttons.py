import json
import os

DATA_FILE = 'user_data.json'

def save_user_data(user_id, city):
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, 'r') as file:
                data = json.load(file)
        else:
            data = {}
        
        data[str(user_id)] = {'city': city}

        with open(DATA_FILE, 'w') as file:
            json.dump(data, file)
        print(f"Данные пользователя {user_id} сохранены успешно.")
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователя: {e}")

def load_user_data(user_id):
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, 'r') as file:
                data = json.load(file)
            return data.get(str(user_id))
        else:
            return None
    except json.JSONDecodeError:
        print("Ошибка при загрузке данных пользователя: файл поврежден или пуст.")
        return None
    except Exception as e:
        print(f"Ошибка при загрузке данных пользователя: {e}")
        return None
