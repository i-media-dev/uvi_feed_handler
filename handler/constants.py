import os

from dotenv import load_dotenv

load_dotenv()

NAME_OF_SHOP = 'uvi'
"""Константа названия магазина."""

NAME_OF_FRAME = 'uvi.png'

FRAME_FOLDER = os.getenv('FRAME_FOLDER', 'frame')
"""Константа стокового названия директории c рамкой"""

FEEDS_FOLDER = os.getenv('FEEDS_FOLDER', 'temp_feeds')
"""Константа стокового названия директории с фидами."""

IMAGE_FOLDER = os.getenv('IMAGE_FOLDER', 'old_images')
"""Константа стокового названия директории с изображениями."""

NEW_IMAGE_FOLDER = os.getenv('NEW_IMAGE_FOLDER', 'new_images')
"""Константа стокового названия директории измененных изображений."""

ENCODING = 'utf-8'
"""Кодировка по умолчанию."""
