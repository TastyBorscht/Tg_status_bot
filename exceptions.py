import requests


class NoTokenEnv(Exception):
    pass


class WrongHomeworkStatus(Exception):
    pass


class ApiIsNotReachable(requests.RequestException):
    pass


class CantSendMessage(Exception):
    pass


class NoHomeworkName(Exception):
    pass


class NoHomeworkInResponse(Exception):
    pass
