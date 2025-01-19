import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
if not os.path.isfile('.env'):
    raise FileNotFoundError("Файл .env не найден. Убедитесь, что файл .env присутствует в корневой директории проекта.")
load_dotenv()

# Получение токенов из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Проверка наличия токенов
if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
    raise ValueError("Необходимые токены отсутствуют. Убедитесь, что они указаны в файле .env")
