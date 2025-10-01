"""Configuration constants and settings for the bot."""

import os
from typing import Final

try:
    # Load variables from a .env file if present
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # If python-dotenv is not installed, fall back silently to environment only
    pass

# Bot configuration
BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "")

# Categories configuration (comma-separated in env/.env: e.g., "food, taxi, one two")
CATEGORIES: Final[list[str]] = [
    'йога',
    'велопокатушка',
    'музыка',
    'калимба',
    'гитара',
    'балалайка',
    'пение',
    'банджо',
    'пианино',
    'вистл',
    'блокфлейта',
    'скрипка',
    'гиджак',
    'мандолина',
    'бузуки',
    'бас',
    'уд',
    'занятие гитарой',
    'занятие скрипкой',
    'занятие виолончелью',
    'занятие пением',
    'занятие флейтой',
    'занятие арфой',
    'занятие басом',
    'занятие теорией музыки',
    'быт',
    'побрился',
    'помылся',
    'уборка',
    'ремонт',
    'утро',
    'утренние процедуры',
    'вечерние процедуры',
    'к выходу готов',
    'медицина',
    'болел',
    'программирование',
    'электроника',
    'config',
    'анализ данных',
    'английский',
    'занятие английским',
    'худ',
    'аниме',
    'манга',
    'фильм',
    'думал',
    'прогулка',
    'гамак',
    'работа',
    'занятие вождением',
    'вождение',
    'кожа',
    'шитьё',
    'велосипед',
    'мастерил',
    'моделирование',
    'знание',
    'tracker',
    'рисование',
    'токарка',
    'поездка в Ташкент',
    'поездка в Грузию',
    'пилатес',
    'бокс',
    'бег',
    'скалодром',
    'функциональный тренинг',
    'миофасциальный релиз',
    'подвесной тренинг',
    'мотопокатушка',
    'стретчинг',
    'бассейн',
    'лыжи',
    'ледовые коньки',
    'роликовые коньки',
    'батуты',
    'картинг',

    'гусли',
    'укулеле',

    'похороны отца',
    'уд155',
    'спал',

    'carving',
    'авиамоделизм',

    'приехал на работу',
    'приехал с работы',

    'сериал',
]

# Processing settings
AUTO_PROCESS_DELAY: Final[int] = 2  # seconds

# Logging configuration
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: Final[str] = "INFO"

