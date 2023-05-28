"""
Telegram-бот.
Бот-ассистент обращаеся к сервису API Практикум.Домашка
и узнает статус домашней работы.
"""


import logging
import os
import sys
import time


import requests
from dotenv import load_dotenv
from telegram import Bot, TelegramError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
ANS_KEY_ERROR = 'Ответ API не содержит ключа "{key}"'
BOT_ADVANCE = 'Бот отправил сообщение: {message}'
CASES_TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
BOT_ERROR = 'Бот не смог отправить сообщение {error}'
DATA_ERROR = 'Ожидается словарь, получен {type_data}'
DENIAL_OF_SERVICE = (
    'Получен ответ от сервиса {url}.'
    'HEADERS: {headers}.'
    'params: {params}.'
    'timeout: {timeout}.\n'
    'Ошибка: {key_refusal} {error}.'
)
HOMEWORK_VERDICTS: dict[str: str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
JOB_KEY_ERROR = 'Словарь "homeworks" не содержит ключа "{key}"'
MESSAGE_ERROR = 'Сбой в работе программы: {error}'
RESPONSE_ERROR = (
    'Неожиданный ответ сервера {url}. '
    'Статус ответа: {code}. '
    'HEADERS: {headers}.'
    'params: {params}.'
    'timeout: {timeout}'
)
RATING_JOB = 'Оценка работы {verdict}'
RETRY_PERIOD = 600
SERVER_ADVANCE = 'Получен ответ от сервиса Яндекс-практикум'
SERVER_ERROR = (
    'Ошибка при запросе к сервису: url {url}. '
    'HEADERS: {headers}.'
    'params: {params}.'
    'timeout: {timeout}.\n'
    'Ошибка: {error}'
)
STATUS_JOB = 'Статус работы {status}'
STATUS_JOB_ERROR = 'Неизвестный статус работы {status}'
START_BOT = 'Бот запущен'
STATUS_HOMEWORK = 'Изменился статус проверки работы "{name}". {verdict}'
TIMEOUT = 30
TOKENS_ERROR = 'Отсутствует обязательная переменная окружения: {}'
TYPE_KEY_ERROR = 'Тип данных homeworks не является списком, получен {type_key}'


def check_tokens():
    """Проверка загрузки переменных окружения."""
    variable_error = ''
    for name in CASES_TOKENS:
        if not globals()[name]:
            variable_error += f'{name} '
    if variable_error:
        logging.critical(TOKENS_ERROR.format(variable_error), exc_info=True)
        raise ValueError(TOKENS_ERROR.format(variable_error))


def send_message(bot, message):
    """Отправляем сообщение в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(BOT_ADVANCE.format(message=message))
        return True
    except TelegramError as error:
        logging.error(BOT_ERROR.format(error=error), exc_info=True)
        return False


def get_api_answer(timestamp):
    """Запрос к сервису Яндекс-практикум."""
    request_params = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp},
        timeout=(TIMEOUT, TIMEOUT)
    )
    try:
        response = requests.get(**request_params)
    except requests.exceptions.RequestException as error:
        raise OSError(
            SERVER_ERROR.format(error=error, **request_params)
        )
    else:
        logging.debug(SERVER_ADVANCE)
    if response.status_code != 200:
        raise ValueError(
            RESPONSE_ERROR.format(code=response.status_code, **request_params)
        )
    response_json = response.json()
    for key_refusal in ('error', 'code'):
        if key_refusal in response_json:
            raise ValueError(
                DENIAL_OF_SERVICE.format(
                    key_refusal=key_refusal,
                    error=response_json.get(key_refusal),
                    **request_params
                )
            )
    return response_json


def check_response(response):
    """Проверяем ответ API."""
    if not isinstance(response, dict):
        raise TypeError(DATA_ERROR.format(type_data={type(response)}))
    if 'homeworks' not in response:
        raise KeyError(ANS_KEY_ERROR.format(key='homeworks'))
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logging.error(TYPE_KEY_ERROR.format(type_key={type(homeworks)}))
        raise TypeError(TYPE_KEY_ERROR.format(type_key={type(homeworks)}))
    return homeworks


def parse_status(homework):
    """Определяем статус домашней работы."""
    name = homework.get('homework_name')
    if name is None:
        raise KeyError(JOB_KEY_ERROR.format(key='homeworks_name'))
    status = homework.get('status')
    logging.debug(STATUS_JOB.format(status=status))
    if status is None:
        raise KeyError(JOB_KEY_ERROR.format(key='homeworks_status'))
    verdict = HOMEWORK_VERDICTS.get(status)
    logging.debug(RATING_JOB.format(verdict={verdict}))
    if verdict is None:
        raise ValueError(STATUS_JOB_ERROR.format(status=status))
    return STATUS_HOMEWORK.format(name=name, verdict=verdict)


def main():
    """Основная функция для запуска Бот-ассистента."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    logging.debug(START_BOT)
    timestamp = int(time.time())
    message_cache = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                if send_message(bot, parse_status(homeworks[0])):
                    timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = MESSAGE_ERROR.format(error=error)
            logging.error(message)
            if message != message_cache and send_message(bot, message):
                message_cache = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s - %(filename)s - '
            '%(funcName)s - %(lineno)d - '
            '%(levelname)s - %(message)s'
        ),
        handlers=[
            logging.FileHandler(__file__ + '.log'),
            logging.StreamHandler(sys.stdout),
        ],
    )
    main()
