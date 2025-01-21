import logging
from main import main

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # Запуск бота
    try:
        logger.info("Запуск бота...")
        main()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")