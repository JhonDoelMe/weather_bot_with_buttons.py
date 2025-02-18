Instructions in English:

Clone the Repository: Clone the repository or download the code files to your local machine.

bash
git clone https://github.com/yourusername/weather-bot.git
cd weather-bot
Create a Virtual Environment: Create a virtual environment to manage dependencies.

bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install Required Packages: Install the necessary packages listed in the requirements.txt file.

bash
pip install -r requirements.txt
Create a .env File: Create a .env file in the root directory of the project and add the following environment variables:

plaintext
TELEGRAM_TOKEN=your_telegram_token
WEATHER_API_KEY=your_openweathermap_api_key
Replace your_telegram_token and your_openweathermap_api_key with your actual tokens.

Run the Bot: Run the bot using the following command:

bash
python weather_bot.py
The bot should now be running and ready to respond to weather queries.

Інструкція українською мовою:

Клонування репозиторію: Клонуйте репозиторій або завантажте файли коду на свій локальний комп'ютер.

bash
git clone https://github.com/yourusername/weather-bot.git
cd weather-bot
Створення віртуального середовища: Створіть віртуальне середовище для управління залежностями.

bash
python -m venv venv
source venv/bin/activate  # Для Windows використовуйте `venv\Scripts\activate`
Встановлення необхідних пакетів: Встановіть необхідні пакети, перелічені у файлі requirements.txt.

bash
pip install -r requirements.txt
Створення файлу .env: Створіть файл .env у кореневій директорії проєкту і додайте наступні змінні середовища:

plaintext
TELEGRAM_TOKEN=your_telegram_token
WEATHER_API_KEY=your_openweathermap_api_key
Замініть your_telegram_token і your_openweathermap_api_key на ваші реальні токени.

Запуск бота: Запустіть бота за допомогою наступної команди:

bash
python weather_bot.py
Тепер бот має працювати і бути готовим відповідати на запити про погоду.
