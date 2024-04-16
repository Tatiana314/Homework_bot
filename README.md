# Homework_bot

Telegram-бот разработан как ассистент для взаимодействия с API сервиса Практикум.Домашка. Основная задача - опрашивать API сервиса для проверки статуса отправленного на ревью домашнего задания студентом. Благодаря данному боту студенты могут оставаться в курсе статуса своих домашних заданий без необходимости постоянно проверять его самостоятельно. Это повышает эффективность и удобство взаимодействия с обучающим сервисом.

Функциональность бота:
1. Регулярный опрос API: бот взаимодействует с API Практикум.Домашка каждые 10 минут, проверяя текущий статус отправленной домашней работы.
2. Уведомления об изменениях статуса: при обновлении статуса домашнего задания, бот анализирует ответ API и отправляет вам уведомление в Telegram, информируя о мгновенных изменениях или обновлениях.
3. Логирование и уведомления: ведётся лог работы бота, и в случае возникновения важных проблем вам отправляется сообщение в Telegram, чтобы вы были в курсе всех ключевых событий.

## Технологии
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue?logo=python)](https://www.python.org/)
[![python-telegram-bot](https://img.shields.io/badge/-python--telegram--bot-464646?logo=Python)](https://docs.python-telegram-bot.org/en/stable/index.html)
[![Requests](https://img.shields.io/badge/-Requests:_HTTP_for_Humans™-464646?logo=Python)](https://pypi.org/project/requests/)
[![logging](https://img.shields.io/badge/-logging-464646?logo=python)](https://docs.python.org/3/library/logging.html)

## Запуск проекта
Клонировать репозиторий:
```
git clone https://github.com/Tatiana314/Homework_bot.git && cd Homework_bot
```
Создать и активировать виртуальное окружение:
```
python -m venv venv
Linux/macOS: source env/bin/activate
windows: source env/scripts/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Создать файл .env:
```
touch .env
```
PRACTICUM_TOKEN - доступ к API сервиса Практикум.Домашка: https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a
TELEGRAM_TOKEN - выдается @BotFather при создании бота
TELEGRAM_CHAT_ID - выдается @userinfobot
Заполнить файл данными:
```
PRACTICUM_TOKEN='token'
TELEGRAM_TOKEN='token'
TELEGRAM_CHAT_ID=<id чата в телеграмм>
```
Запуск приложения:
```
python homework.py
```

## Автор
[Мусатова Татьяна](https://github.com/Tatiana314)
