import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from requests import RequestException
from telebot import TeleBot
from telebot.apihelper import ApiException

from exceptions import (ApiIsNotReachable, CantSendMessage,
                        NoHomeworkInResponse, NoTokenEnv, WrongHomeworkStatus)

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
    '%(asctime)s - %(levelname)s - %(module)s - '
    '%(filename)s:%(lineno)d - %(funcName)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия переменных среды."""
    required_tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    missing_tokens = []
    for token_name, token in required_tokens.items():
        if not token:
            missing_tokens.append(token_name)
    if missing_tokens:
        logger.critical(
            f'для работы бота не хватает токена(ов): {missing_tokens}'
        )
        return missing_tokens
    return False


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    try:
        logger.debug(f'Начало отправки сообщения "{message}"')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug(f'Удачная отправка сообщения "{message}"')
    except (ApiException, RequestException) as e:
        raise CantSendMessage(f'Не переслано сообщение {message}. Ошибка: {e}')
    return True


def get_api_answer(connection_data):
    """Получить ответ от api-сервиса."""
    try:
        logger.debug(
            'Начало отправки запроса к API-сервису {ENDPOINT}, '
            'данные заголовка {HEADERS}, с параметрами {PARAMS}.'.format(
                **connection_data
            ))
        homework_statuses = requests.get(
            connection_data['ENDPOINT'],
            headers=connection_data['HEADERS'],
            params=connection_data['PARAMS'],
        )
    except RequestException:
        raise ApiIsNotReachable
    if homework_statuses.status_code != HTTPStatus.OK:
        raise ApiIsNotReachable
    return homework_statuses.json()


def check_response(api_response):
    """Проверяет, содержит ли ответ от API нужные данные."""
    if not isinstance(api_response, dict):
        raise TypeError(
            f'ответ от api-сервиса содержит {type(api_response)} вместо dict'
        )
    if 'homeworks' not in api_response:
        raise NoHomeworkInResponse(
            'Словарь, полученный от api-сервиса не содержит ключа, '
            'дающего доступ к списку домашних работ.'
        )
    homeworks_lst = api_response['homeworks']
    if not isinstance(homeworks_lst, list):
        raise TypeError(
            f'Неверная структура данных в ответе от api-сервиса,'
            f'ожидался list вместо {type(homeworks_lst)}.'
        )
    if not homeworks_lst:
        logger.debug('Нет новых домашних работ с прошлого запроса.')
    return homeworks_lst


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
    if check_tokens():
        raise NoTokenEnv('Не хватает переменных окружения.')
    bot = TeleBot(token=TELEGRAM_TOKEN)
    prev_message = None
    timestamp = int(time.time())
    connection_data = {
        'ENDPOINT': 'https://practicum.yandex.ru/api/'
                    'user_api/homework_statuses/',
        'HEADERS': HEADERS,
        'PARAMS': {'from_date': f'{timestamp}'}
    }
    while True:
        try:
            api_response = get_api_answer(connection_data)
            homeworks_lst = check_response(api_response)
            if homeworks_lst:
                if send_message(
                        bot, parse_status(homeworks_lst[0])):
                    timestamp = api_response.get('current_date', timestamp)
                    connection_data['PARAMS'] = {'from_date': f'{timestamp}'}
                    prev_message = None
        except Exception as error:
            logger.error(error, exc_info=True)
            message = f'Сбой в работе программы: {error}.'
            if (
                    prev_message != message and not isinstance(error,
                                                               CantSendMessage
                                                               )
                    and send_message(message)
            ):
                prev_message = message
            else:
                logger.debug('Статус проверки не изменился.')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
