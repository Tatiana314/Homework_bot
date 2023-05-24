"""Telegram-бот.
Бот-ассистент обращаеся к сервису API Практикум.Домашка
и узнает статус домашней работы."""


import sys
import time
import logging

import requests

from telegram import Bot, TelegramError
from configs.logs import log_configured
from configs.base import (
    PRACTICUM_TOKEN,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
    RETRY_PERIOD,
    ENDPOINT,
    HEADERS,
    HOMEWORK_VERDICTS,
)


logger = log_configured.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


MESSAGE = 'Отсутствует обязательная переменная окружения: {}'


def check_tokens():
    """Проверка загрузки переменных окружения."""
    if not PRACTICUM_TOKEN:
        logger.critical(MESSAGE.format('PRACTICUM_TOKEN'))
    if not TELEGRAM_TOKEN:
        logger.critical(MESSAGE.format('TELEGRAM_TOKEN'))
    if not TELEGRAM_CHAT_ID:
        logger.critical(MESSAGE.format('TELEGRAM_CHAT_ID'))
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def send_message(bot, message):
    """Отправляем сообщение в Telegram-чат"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError as error:
        logger.error(f'Бот не смог отправить сообщение {error}')
    else:
        logger.debug(f'Бот отправил сообщение: {message}')


MESSAGE_ERROR = (
    'Неожиданный ответ сервера {endpoint}. '
    'Статус ответа: {code}. '
    'Содержание ответа {content}.'
)


def get_api_answer(timestamp):
    """Запрос к сервису Яндекс-практикум"""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(
                MESSAGE_ERROR.format(
                    endpoint=ENDPOINT,
                    code=response.status_code,
                    content=response.content
                )
            )
    except requests.exceptions.RequestException as error:
        logger.exception(error)
    else:
        logger.debug('Получен ответ от сервиса Яндекс-практикум')
    return response.json()


def check_response(response):
    """Проверяем ответ API"""
    if type(response) != dict:
        logger.error('Тип данных, полученных от сервера, не является словарем')
        raise TypeError('Ожидается словарь')
    if response.get('homeworks') is None:
        logger.error('В словаре отсутствует ключ: homeworks')
        raise KeyError('Ожидается ключ homeworks')
    homeworks = response.get('homeworks')
    if type(homeworks) != list:
        logger.error('Тип данных homeworks не является списком')
        raise TypeError('Ожидается список')
    if response.get('current_date') is None:
        logger.error('В словаре отсутствует ключ: current_date')
        raise KeyError('Ожидается ключ current_date')
    current_date = response.get('current_date')
    if type(current_date) != int:
        logger.error('Тип данных current_date не является числом')
        raise TypeError('Ожидается число')
    return (homeworks, current_date)


def parse_status(homework):
    """Определяем статус домашней работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('В словаре нет ключа homework_name')
    homework_status = homework.get('status')
    logger.debug(f'Текущий статус работы {homework_status}')
    if homework_status is None:
        raise KeyError('В словаре нет ключа homework_status')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    logger.debug(f'Оценка работы {verdict}')
    if verdict is None:
        raise ValueError(f'Неизвестный статус {homework_status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот запущен')
    timestamp = int(time.time())
    message_cache = ''
    while True:
        try:
            message = 'Статус работ не изменился'
            response = get_api_answer(timestamp)
            if response:
                homeworks, timestamp = check_response(response)
                if homeworks:
                    for homework in homeworks:
                        message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != message_cache:
                send_message(bot, message)
                message_cache = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
