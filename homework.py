import logging
import os
import sys
import time
from http import HTTPStatus
import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import (
    NoTokenEnv, WrongHomeworkStatus, ApiIsNotReachable, CantSendMessage, NoHomeworkInResponse
)

load_dotenv()

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
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
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия переменных среды."""
    required_tokens = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    ]
    missing_tokens = []
    for token in required_tokens:
        if not token:
            missing_tokens.append(token)
    if missing_tokens:
        logger.critical(
            f'для работы бота не хватает токена(ов): {missing_tokens}'
        )
        return False
    return True


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug(f'Удачная отправка сообщения "{message}"')
    except Exception as e:
        raise CantSendMessage(f'Не переслано сообщение {message}. Ошибка: {e}')


def get_api_answer(timestamp):
    """Получить ответ от api-сервиса."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': f'{timestamp}'},
        )
    except Exception:
        logger.error(
            f'API не доступен, статус запроса {homework_statuses.status_code}'
        )
        raise requests.RequestException(
            f'API не доступен, статус запроса {homework_statuses.status_code}'
        )
    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error(
            f'Неправильный код запроса: {homework_statuses.status_code}'
        )
        raise ApiIsNotReachable(
            f'API не доступен, статус запроса {homework_statuses.status_code}'
        )
    return homework_statuses.json()


def check_response(api_response):
    """Проверяет, содержит ли ответ от API нужные данные."""
    if not isinstance(api_response, dict):
        raise TypeError('Неверная структура данных в ответе от api-сервиса.')
    if 'homeworks' not in api_response:
        raise NoHomeworkInResponse(
            'Ответ от api-сервиса не содержит списка домашних работ.')
    if not isinstance(api_response['homeworks'], list):
        raise TypeError('Неверная структура данных в ответе от api-сервиса.')
    if not api_response['homeworks']:
        logger.debug('Нет новых домашних работ с прошлого запроса.')
        # raise NoHomeworkInResponse('Нет новых домашних работ с прошлого запроса.')


def parse_status(homework):
    """Составляет сообщение на основе статуса домашней работы."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[f'{homework["status"]}']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as e:
        logger.error(e)
        raise WrongHomeworkStatus('Неожиданный статус домашней работы.')


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        raise NoTokenEnv('Не хватает переменных окружения.')
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    prev_status = None
    prev_message = None
    while True:
        try:
            api_response = get_api_answer(timestamp)
            check_response(api_response)
            # if prev_status == api_response['homeworks'][0]['status']:
            #     logger.debug('статус домашней работы не изменился.')
            #     continue
            # prev_status = api_response['homeworks'][0]['status']
            timestamp = api_response['current_date']
            send_message(bot, parse_status(api_response['homeworks'][0]))
        except Exception as error:
            logger.error(error, exc_info=True)
            message = f'Сбой в работе программы: {error}.'
            if (
                prev_message != message and not isinstance(error, CantSendMessage)
                and send_message(message)
            ):
                prev_message = message
            if prev_message == message:
                logger.debug('Статус проверки не изменился.')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
