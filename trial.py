import os

from dotenv import load_dotenv

load_dotenv()
from exceptions import WrongHomeworkStatus


# def delenie():
#     try:
#         a = 5 / 0
#     except Exception as e:
#         print(e)
#         raise WrongHomeworkStatus(f'delenint na nol')
#
#
# def main():
#     while True:
#         try:
#             delenie()
#         except Exception as error:
#             if isinstance(error, WrongHomeworkStatus):
#                 print('sobaken')
#             print(error)
#             break
#
#
# main()

# d = {'1': 'one'}
# if '2' not in d:
#     print('im sosige')

# required_tokens = [
#     'PRACTICUM_TOKEN',
#     'TELEGRAM_TOKEN',
#     'TELEGRAM_CHAT_ID',
# ]
# missing_tokens = []
#
#
# for token in required_tokens:
#     if token not in os.environ:
#         missing_tokens.append(token)
#
# print(missing_tokens)
connection_data = {
        'ENDPOINT': 'https://practicum.yandex.ru/api/user_api/homework_statuses/',
        'headers': 'header_1',
        'params': {'from_date': '10:55'}
    }

str_ = ('Начало отправки запроса к API-сервису {ENDPOINT}, '
        'данные заголовка {headers}, время {params}.').format(**connection_data)
print(str_)