"""Настройка логирования."""

import logging as log_configured

log_configured.basicConfig(
    level=log_configured.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        log_configured.FileHandler('bot.log'),
    ],
)
