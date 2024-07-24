import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import NoTokenEnv, WrongHomeworkStatus

load_dotenv()

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
# RETRY_PERIOD = 600
RETRY_PERIOD = 30
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия переменных среды."""
    required_tokens = [
        'PRACTICUM_TOKEN',
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID',
    ]
    for token in required_tokens:
        if token not in os.environ:
            logger.critical(f'для работы бота не хватает токена {token}')
            raise NoTokenEnv(f'для работы бота не хватает токена {token}')


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )
    logger.debug(f'Удачная отправка сообщения "{message}"')


def get_api_answer(timestamp):
    """Получить ответ от api-сервиса."""
    homework_statuses = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': f'{timestamp}'},
    )
    return homework_statuses.json()


def check_response(api_response):
    """Проверяет, содержит ли ответ от API сервиса нужный словарь."""
    if api_response['homeworks']:
        return True
    logger.debug('Нет новых домашних работ с прошлого запроса.')
    return False


def parse_status(homework):
    """Составляет сообщение на основе статуса домашней работы."""
    homework_name = homework['homework_name']
    try:
        verdict = HOMEWORK_VERDICTS[f'{homework["status"]}']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except WrongHomeworkStatus:
        logger.error('Неожиданный статус домашней работы.')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = 0
    prev_status = None
    prev_message = None
    while True:
        try:
            time.sleep(RETRY_PERIOD)
            api_response = get_api_answer(timestamp)
            if not check_response(api_response):
                continue
            if prev_status == api_response['homeworks'][0]['status']:
                logger.debug('статус домашней работы не изменился.')
            prev_status = api_response['homeworks'][0]['status']
            timestamp = api_response['current_date']
            send_message(bot, parse_status(api_response['homeworks'][0]))
        except Exception as error:
            logger.error(error, exc_info=True)
            message = f'Сбой в работе программы: {error}.'
            if prev_message is None or prev_message != message:
                prev_message = message
                send_message(bot, message)
                continue
            if prev_message == message:
                logger.debug('Статус проверки не изменился.')


if __name__ == '__main__':
    main()
