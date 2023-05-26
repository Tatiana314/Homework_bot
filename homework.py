"""
Telegram-бот.
Бот-ассистент обращаеся к сервису API Практикум.Домашка
и узнает статус домашней работы.
"""


import sys
import time
import json
import logging


import requests
from telegram import Bot, TelegramError

from configs.base import (
    ENDPOINT,
    HEADERS,
    HOMEWORK_VERDICTS,
    PRACTICUM_TOKEN,
    RETRY_PERIOD,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    TIMEOUT
)
from configs.logs import log_configured


logger = log_configured.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler_stream = logging.StreamHandler(sys.stdout)
handler_file = logging.FileHandler('bot.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'
)
handler_stream.setFormatter(formatter)
handler_file.setFormatter(formatter)


MESSAGE_BOT = 'Бот отправил сообщение: {message}'
MESSAGE_BOT_ERROR = 'Бот не смог отправить сообщение {error}'
MESSAGE_DATA_ERROR = 'Ожидается словарь, получен {type_data}'
MESSAGE_DECODE_ERROR = (
    'Ошибка декодирования полученного ответа от сервиса {endpoint}'
)
MESSAGE_SERVER_ERROR = (
    'Ошибка при запросе к сервису {endpoint}. '
    '{headers}.'
    '{params}.'
    '{timeout}.'
)
MESSAGE_HTTP_ERROR = (
    'Неожиданный ответ сервера {endpoint}. '
    'Статус ответа: {code}. '
    '{headers}.'
    '{params}'
)
MESSAGE_ERROR = 'Сбой в работе программы: {error}'
MESSAGE_SERVER = 'Получен ответ от сервиса Яндекс-практикум'
MESSAGE_STATUS_JOB = 'Статус работы {status}'
MESSAGE_STATUS_JOB_ERROR = 'Неизвестный статус работы {status}'
MESSAGE_TOKENS = 'Отсутствует обязательная переменная окружения: {}'
KEY_ERROR = 'В словаре нет ключа "{key}"'
STATUS_HOMEWORK = 'Изменился статус проверки работы "{name}". {verdict}'
TYPE_KEY_ERROR = 'Тип данных homeworks не является списком, получен {type_key}'


def check_tokens():
    """Проверка загрузки переменных окружения."""
    case = (
        ('PRACTICUM_TOKEN ', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN ', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID ', TELEGRAM_CHAT_ID),
    )
    variable_error = ''
    for name, variable in case:
        if not variable:
            variable_error += name
    if variable_error:
        logger.critical(MESSAGE_TOKENS.format(variable_error))
        raise ValueError(MESSAGE_TOKENS.format(variable_error))


def send_message(bot, message):
    """Отправляем сообщение в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(MESSAGE_BOT.format(message=message))
    except TelegramError as error:
        logger.error(MESSAGE_BOT_ERROR.format(error=error), exc_info=True)
    else:
        return True


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
    except requests.exceptions.ConnectionError as error:
        raise error(
            MESSAGE_SERVER_ERROR.format(
                endpoint=ENDPOINT,
                headers=HEADERS,
                params=payload,
                timeout=TIMEOUT,
            )
        )
    except requests.exceptions.Timeout as error:
        raise error(
            MESSAGE_SERVER_ERROR.format(
                endpoint=ENDPOINT,
                headers=HEADERS,
                params=payload,
                timeout=TIMEOUT,
            )
        )
    except requests.exceptions.RequestException as error:
        raise error(
            MESSAGE_SERVER_ERROR.format(
                endpoint=ENDPOINT,
                headers=HEADERS,
                params=payload,
                timeout=TIMEOUT,
            )
        )
    else:
        logger.debug(MESSAGE_SERVER)
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(
            MESSAGE_HTTP_ERROR.format(
                endpoint=ENDPOINT,
                code=response.status_code,
                headers=HEADERS,
                params=payload,
            )
        )
    try:
        return response.json()
    except json.JSONDecodeError as error:
        raise error(MESSAGE_DECODE_ERROR.format(endpoint=ENDPOINT))


def check_response(response):
    """Проверяем ответ API."""
    if not isinstance(response, dict):
        raise TypeError(MESSAGE_DATA_ERROR.format(type_data={type(response)}))
    if 'homeworks' not in response:
        raise KeyError(KEY_ERROR.format(key='homeworks'))
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logger.error(TYPE_KEY_ERROR.format(type_key={type(homeworks)}))
        raise TypeError(TYPE_KEY_ERROR.format(type_key={type(homeworks)}))
    return homeworks


def parse_status(homework):
    """Определяем статус домашней работы."""
    name = homework.get('homework_name')
    if name is None:
        raise KeyError(KEY_ERROR.format(key='homeworks_name'))
    status = homework.get('status')
    logger.debug(MESSAGE_STATUS_JOB.format(status=status))
    if status is None:
        raise KeyError(KEY_ERROR.format(key='homeworks_status'))
    verdict = HOMEWORK_VERDICTS.get(status)
    logger.debug(f'Оценка работы {verdict}')
    if verdict is None:
        raise ValueError(MESSAGE_STATUS_JOB_ERROR.format(status=status))
    return STATUS_HOMEWORK.format(name=name, verdict=verdict)


def main():
    """Основная функция для запуска Бот-ассистента."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот запущен')
    timestamp = int(time.time())
    message_cache = ''
    while True:
        try:
            message = MESSAGE_STATUS_JOB.format(status='не изменился')
            response = get_api_answer(timestamp)
            homework = check_response(response)
            timestamp = response.get('current_date')
            if homework:
                message = parse_status(homework[0])
            send_message(bot, message)
        except Exception as error:
            message = MESSAGE_ERROR.format(error=error)
            logger.error(message)
            if message != message_cache:
                if send_message(bot, message):
                    message_cache = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
