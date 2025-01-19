import json

def load_user_data(user_id):
    try:
        with open('user_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get(str(user_id), {})
    except FileNotFoundError:
        return {}

def save_user_data(user_id, city, notified=False):
    try:
        with open('user_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
    
    data[str(user_id)] = {'city': city, 'notified': notified}
    
    with open('user_data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
