import json
import os
import logging

logger = logging.getLogger(__name__)

DATA_FILE = 'user_data.json'

def save_user_data(user_id, city=None, subscriptions=None):
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            data = {}
        
        user_data = data.get(str(user_id), {})
        if city:
            user_data['city'] = city
        if subscriptions:
            user_data['subscriptions'] = subscriptions

        data[str(user_id)] = user_data

        with open(DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info(f"Данные пользователя {user_id} сохранены успешно.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных пользователя: {e}")

def load_user_data(user_id):
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data.get(str(user_id))
        else:
            return None
    except json.JSONDecodeError:
        logger.error("Ошибка при загрузке данных пользователя: файл поврежден или пуст.")
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных пользователя: {e}")
        return None

def subscribe_user(user_id, subscription_type):
    user_data = load_user_data(user_id)
    if not user_data:
        user_data = {}
    if 'subscriptions' not in user_data:
        user_data['subscriptions'] = {}
    user_data['subscriptions'][subscription_type] = True
    save_user_data(user_id, subscriptions=user_data['subscriptions'])

def unsubscribe_user(user_id, subscription_type):
    user_data = load_user_data(user_id)
    if user_data and 'subscriptions' in user_data:
        user_data['subscriptions'].pop(subscription_type, None)
        save_user_data(user_id, subscriptions=user_data['subscriptions'])