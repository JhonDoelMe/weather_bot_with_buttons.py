import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Проверка наличия файла .env
if not os.path.isfile('.env'):
    logger.error("Файл .env не найден. Убедитесь, что файл .env присутствует в корневой директории проекта.")
    raise FileNotFoundError("Файл .env не найден. Создайте файл .env и добавьте необходимые переменные окружения.")

# Загрузка переменных окружения
load_dotenv()
logger.info("Файл .env успешно загружен.")

# Получение токенов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")
UKRAINE_ALARM_API_KEY = os.getenv("UKRAINE_ALARM_API_KEY")

# Проверка наличия всех токенов
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN отсутствует. Убедитесь, что он указан в файле .env")
if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY отсутствует. Убедитесь, что он указан в файле .env")
if not CURRENCY_API_KEY:
    raise ValueError("CURRENCY_API_KEY отсутствует. Убедитесь, что он указан в файле .env")
if not UKRAINE_ALARM_API_KEY:
    raise ValueError("UKRAINE_ALARM_API_KEY отсутствует. Убедитесь, что он указан в файле .env")