import os
from pprint import pprint

import requests, time
from dotenv import load_dotenv
from telebot import TeleBot, types

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


def check_tokens():
    """Проверка переменных среды."""
    required_tokens = [
        'PRACTICUM_TOKEN',
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID',
    ]
    for token in required_tokens:
        if token not in os.environ:
            raise ValueError(f'для работы бота не хватает токена {token}')


def send_message(bot, message):
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )


def get_api_answer(timestamp):
    homework_statuses = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': f'{timestamp}'},
    )
    return homework_statuses.json()


def check_response(response):
    if response['homeworks'][0]:
        return response['homeworks'][0]
    return False


def parse_status(homework):
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[f'{homework["status"]}']

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    homework = check_response(get_api_answer(int(time.time()) - RETRY_PERIOD))
    if homework:
        send_message(bot, message=parse_status(homework))
    pass
    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
