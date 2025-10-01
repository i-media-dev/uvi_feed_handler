import os

from dotenv import load_dotenv

load_dotenv()

NAME_OF_SHOP = 'uvi'
"""Константа названия магазина."""

FEEDS_FOLDER = os.getenv('FEEDS_FOLDER', 'temp_feeds')
"""Константа стокового названия директорий."""

IMAGE_FOLDER = os.getenv('IMAGE_FOLDER', 'old_images')
"""Константа стокового названия директорий."""

NEW_IMAGE_FOLDER = os.getenv('NEW_IMAGE_FOLDER', 'new_images')
"""Константа стокового названия директорий."""

ENCODING = 'utf-8'
"""Кодировка по умолчанию."""
