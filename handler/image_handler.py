import logging
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from handler.constants import (FEEDS_FOLDER, FRAME_FOLDER, IMAGE_FOLDER,
                               NAME_OF_FRAME, NEW_IMAGE_FOLDER,
                               NUMBER_PIXELS_CANVAS, NUMBER_PIXELS_IMAGE,
                               RGB_COLOR_SETTINGS, RGBA_COLOR_SETTINGS)
from handler.decorators import time_of_function
from handler.exceptions import DirectoryCreationError, EmptyFeedsListError
from handler.feeds import FEEDS
from handler.logging_config import setup_logging
from handler.mixins import FileMixin

setup_logging()


class XMLImage(FileMixin):
    """
    Класс, предоставляющий интерфейс
    для работы с изображениями.
    """

    def __init__(
        self,
        feeds_folder: str = FEEDS_FOLDER,
        frame_folder: str = FRAME_FOLDER,
        image_folder: str = IMAGE_FOLDER,
        new_image_folder: str = NEW_IMAGE_FOLDER,
        feeds_list: list[str] = FEEDS,
        number_pixels_canvas: int = NUMBER_PIXELS_CANVAS,
        number_pixels_image: int = NUMBER_PIXELS_IMAGE
    ) -> None:
        self.frame_folder = frame_folder
        self.feeds_folder = feeds_folder
        self.image_folder = image_folder
        self.new_image_folder = new_image_folder
        self.feeds_list = feeds_list
        self.number_pixels_canvas = number_pixels_canvas
        self.number_pixels_image = number_pixels_image
        self._existing_image_offers = set()
        self._existing_framed_offers = set()

    def _get_image_data(self, url: str) -> tuple:
        """
        Защищенный метод, загружает данные изображения
        и возвращает (image_data, image_format).
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image_format = image.format.lower() if image.format else None
            return response.content, image_format
        except Exception as e:
            logging.error(f'Ошибка при загрузке изображения {url}: {e}')
            return None, None

    def _get_image_filename(
        self,
        index: int,
        offer_id: str,
        image_data: bytes,
        image_format: str
    ) -> str:
        """Защищенный метод, создает имя файла с изображением."""
        if not image_data or not image_format:
            return ''
        return f'{offer_id}_{index}.{image_format}'

    def _build_offers_set(self, folder: str, format_str: str, target_set: set):
        """Защищенный метод, строит множество всех существующих офферов."""
        try:
            for file_name in self._get_filenames_list(folder, format_str):
                offer_id = file_name.split('_')[0]
                if offer_id:
                    target_set.add(offer_id)

            logging.info(
                f'Построен кэш для {len(target_set)} офферов'
            )
        except EmptyFeedsListError:
            raise
        except DirectoryCreationError:
            raise
        except Exception as e:
            logging.error(
                'Неожиданная ошибка при сборе множества '
                f'скачанных изображений: {e}'
            )
            raise

    def _save_image(
        self,
        image_data: bytes,
        folder_path: Path,
        image_filename: str
    ):
        """Защищенный метод, сохраняет изображение по указанному пути."""
        try:
            with Image.open(BytesIO(image_data)) as img:
                file_path = folder_path / image_filename
                img.load()
                img.save(file_path)
        except Exception as e:
            logging.error(f'Ошибка при сохранении {image_filename}: {e}')

    @time_of_function
    def get_images(self):
        """Метод получения и сохранения изображений из xml-файла."""
        total_offers_processed = 0
        offers_with_images = 0
        images_downloaded = 0
        offers_skipped_existing = 0

        try:
            self._build_offers_set(
                self.image_folder,
                'jpeg',
                self._existing_image_offers
            )
        except (DirectoryCreationError, EmptyFeedsListError):
            logging.warning(
                'Директория с изображениями отсутствует. Первый запуск'
            )
        try:
            for file_name in self._get_filenames_list(self.feeds_folder):
                tree = self._get_tree(file_name, self.feeds_folder)
                root = tree.getroot()
                for offer in root.findall('.//offer'):
                    offer_id = offer.get('id')
                    total_offers_processed += 1

                    if offer_id in self._existing_image_offers:
                        offers_skipped_existing += 1
                        continue

                    offer_images = [
                        img.text for img in offer.findall(
                            'picture'
                        ) if (
                            '1.jpg' in img.text or '2.jpg' in img.text
                        ) and 'Technical' not in img.text
                    ]
                    if not offer_images:
                        continue

                    offers_with_images += 1

                    for index, offer_image in enumerate(offer_images):
                        image_data, image_format = self._get_image_data(
                            offer_image
                        )
                        image_filename = self._get_image_filename(
                            index,
                            offer_id,
                            image_data,
                            image_format
                        )
                        folder_path = self._make_dir(self.image_folder)
                        self._save_image(
                            image_data, folder_path, image_filename)
                        images_downloaded += 1
            logging.info(
                f'\nВсего обработано офферов - {total_offers_processed}\n'
                'Всего офферов с подходящими '
                f'изображениями - {offers_with_images}\n'
                f'Всего изображений скачано {images_downloaded}\n'
                'Пропущено офферов с уже скачанными '
                f'изображениями - {offers_skipped_existing}'
            )
        except Exception as e:
            logging.error(f'Неожиданная ошибка при получении изображений: {e}')

    @time_of_function
    def add_frame(self):
        """Метод форматирует изображения и добавляет рамку."""
        images_names_list = self._get_filenames_list(self.image_folder, 'jpeg')
        file_path = self._make_dir(self.image_folder)
        frame_path = self._make_dir(self.frame_folder)
        new_file_path = self._make_dir(self.new_image_folder)
        total_framed_images = 0
        total_failed_images = 0
        skipped_images = 0

        try:
            self._build_offers_set(
                self.new_image_folder,
                'png',
                self._existing_framed_offers
            )
        except (DirectoryCreationError, EmptyFeedsListError):
            logging.warning(
                'Директория с форматированными изображениями отсутствует. '
                'Первый запуск'
            )
        try:
            for image_name in images_names_list:
                if image_name.split('_')[0] in self._existing_framed_offers:
                    skipped_images += 1
                    continue

                with Image.open(file_path / image_name) as image:
                    image.load()
                    image_width, image_height = image.size
                with Image.open(frame_path / NAME_OF_FRAME) as frame:
                    frame_resized = frame.resize((image_width, image_height))

                canvas_width = image_width - self.number_pixels_canvas
                canvas_height = image_height - self.number_pixels_canvas

                new_image_width = image_width - self.number_pixels_image
                new_image_height = image_height - self.number_pixels_image

                resized_image = image.resize(
                    (new_image_width, new_image_height))

                canvas = Image.new(
                    'RGB',
                    (canvas_width, canvas_height),
                    RGB_COLOR_SETTINGS
                )

                x_position = (canvas_width - new_image_width) // 2
                y_position = (canvas_height - new_image_height) // 2
                canvas.paste(resized_image, (x_position, y_position))

                final_image = Image.new(
                    'RGBA',
                    (image_width, image_height),
                    RGBA_COLOR_SETTINGS
                )

                canvas_x = (image_width - canvas_width) // 2
                canvas_y = (image_height - canvas_height) // 2

                final_image.paste(canvas, (canvas_x, canvas_y))
                final_image.paste(frame_resized, (0, 0), frame_resized)
                final_image.save(
                    new_file_path / f'{image_name.split('.')[0]}.png',
                    'PNG'
                )
                total_framed_images += 1
            logging.info(
                '\n Количество изображений, к которым добавлена '
                f'рамка - {total_framed_images}\n'
                f'Количество уже обрамленных изображений - {skipped_images}\n'
                'Количество изображений обрамленных '
                f'неудачно - {total_failed_images}'

            )
        except Exception as e:
            total_failed_images += 1
            logging.error(f'Неожиданная ошибка наложения рамки: {e}')
