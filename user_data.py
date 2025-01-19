import os
import json
import logging

logger = logging.getLogger(__name__)

USER_DATA_FILE = 'user_data.json'

# Проверка существования и инициализация пустого файла
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump({}, file, indent=4, ensure_ascii=False)

def read_user_data():
    if os.path.exists(USER_DATA_FILE):
        if os.stat(USER_DATA_FILE).st_size == 0:  # Проверка на пустоту файла
            return {}
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Ошибка чтения файла данных пользователя: {e}")
    return {}

def save_user_data(user_id, city):
    data = read_user_data()
    data[str(user_id)] = {'city': city}

    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except IOError as e:
        logger.error(f"Ошибка записи в файл данных пользователя: {e}")

def load_user_data(user_id):
    data = read_user_data()
    return data.get(str(user_id), None)
