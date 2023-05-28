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
BOT_ERROR = 'Бот не смог отправить сообщение {error}'
DATA_ERROR = 'Ожидается словарь, получен {type_data}'
DECODE_ERROR = (
    'Получен ответ от сервиса {endpoint}.'
    'HEADERS: {headers}.'
    'params: {params}.'
    'timeout: {timeout}.\n'
    'Ошибка: {error} {code}.'
)
HOMEWORK_VERDICTS: dict[str: str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
HTTP_ERROR = (
    'Неожиданный ответ сервера {endpoint}. '
    'Статус ответа: {code}. '
    'HEADERS: {headers}.'
    'params: {params}.'
    'timeout: {timeout}'
)
JOB_KEY_ERROR = 'Словарь "homeworks" не содержит ключа "{key}"'
MESSAGE_ERROR = 'Сбой в работе программы: {error}'
RETRY_PERIOD = 600
SERVER_ADVANCE = 'Получен ответ от сервиса Яндекс-практикум'
SERVER_ERROR = (
    'Ошибка при запросе к сервису {endpoint}. '
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


class ServiceException(Exception):
    """Ошибки в работе сервиса."""

    pass


def check_tokens():
    """Проверка загрузки переменных окружения."""
    variable_error = ''
    for name in ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'):
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
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload,
            timeout=(TIMEOUT, TIMEOUT)
        )
    except requests.exceptions.RequestException as error:
        raise ServiceException(
            SERVER_ERROR.format(
                endpoint=ENDPOINT,
                headers=HEADERS,
                params=payload,
                timeout=(TIMEOUT, TIMEOUT),
                error=error
            )
        )
    else:
        logging.debug(SERVER_ADVANCE)
    if response.status_code != 200:
        raise ValueError(
            HTTP_ERROR.format(
                endpoint=ENDPOINT,
                code=response.status_code,
                headers=HEADERS,
                params=payload,
                timeout=(TIMEOUT, TIMEOUT)
            )
        )
    response_json = response.json()
    if 'error' in response_json or 'code' in response_json:
        raise ValueError(
            DECODE_ERROR.format(
                endpoint=ENDPOINT,
                headers=HEADERS,
                params=payload,
                timeout=(TIMEOUT, TIMEOUT),
                error=response_json.get('error'),
                code=response_json.get('code')
            )
        )
    return response.json()


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
    logging.debug(f'Оценка работы {verdict}')
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
            timestamp = response.get('current_date', timestamp)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
        except Exception as error:
            message = MESSAGE_ERROR.format(error=error)
            logging.error(message)
            if message != message_cache and send_message(bot, message):
                message_cache = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(__file__ + '.log'),
            logging.StreamHandler(sys.stdout),
        ],
    )
    main()
