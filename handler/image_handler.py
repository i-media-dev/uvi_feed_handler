from io import BytesIO
import logging
from pathlib import Path

from PIL import Image, ImageFilter
import requests

from handler.constants import (
    FEEDS_FOLDER,
    FRAME_FOLDER,
    IMAGE_FOLDER,
    NEW_IMAGE_FOLDER,
    NAME_OF_FRAME
)
from handler.decorators import time_of_function
from handler.feeds import FEEDS
from handler.mixins import FileMixin
from handler.logging_config import setup_logging

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
        feeds_list: list[str] = FEEDS
    ) -> None:
        self.frame_folder = frame_folder
        self.feeds_folder = feeds_folder
        self.image_folder = image_folder
        self.new_image_folder = new_image_folder
        self.feeds_list = feeds_list

    def _get_image_filename(self, index: int, offer_id: str, url: str) -> str:
        """Защищенный метод, создает имя файла с изображением."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image_format = image.format.lower() if image.format else None
            return f'{offer_id}_{index}.{image_format}'
        except Exception as e:
            print(f'Ошибка при обработке изображения {url}: {e}')
            logging.error(f'Ошибка при обработке изображения {url}: {e}')
            return ''

    def _save_image(self, url: str, folder_path: Path, image_filename: str):
        """Защищенный метод, сохраняет изображение по указанному пути."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            with Image.open(BytesIO(response.content)) as img:
                file_path = folder_path / image_filename
                img.load()
                img.save(file_path)
        except requests.RequestException as e:
            logging.error(f'Ошибка при загрузке {url}: {e}')
        except Exception as e:
            logging.error(f'Ошибка при обработке изображения {url}: {e}')

    @time_of_function
    def get_images(self):
        """Метод получения и сохранения изображений из xml-файла."""
        for file_name in self._get_filenames_list(self.feeds_folder):
            tree = self._get_tree(file_name, self.feeds_folder)
            root = tree.getroot()
            for offer in root.findall('.//offer'):
                offer_id = offer.get('id')
                offer_images = [
                    img.text for img in offer.findall(
                        'picture'
                    ) if (
                        '1.jpg' in img.text or '2.jpg' in img.text
                    ) and 'Technical' not in img.text
                ]
                if not offer_images:
                    logging.warning(f'Offer {offer_id} не имеет изображений')
                    continue
                for index, offer_image in enumerate(offer_images):
                    image_filename = self._get_image_filename(
                        index,
                        offer_id,
                        offer_image
                    )
                    folder_path = self._make_dir(self.image_folder)
                    self._save_image(offer_image, folder_path, image_filename)

    def add_frame(self):
        images_names_list = self._get_filenames_list(self.image_folder, 'jpeg')
        file_path = self._make_dir(self.image_folder)
        frame_path = self._make_dir(self.frame_folder)
        new_file_path = self._make_dir(self.new_image_folder)

        for image_name in images_names_list:

            with Image.open(file_path / image_name) as image:
                image.load()
                image_width, image_height = image.size
            with Image.open(frame_path / NAME_OF_FRAME) as frame:
                frame_resized = frame.resize((image_width, image_height))

            canvas_margin = 20

            canvas_width = image_width - 2 * canvas_margin
            canvas_height = image_height - 2 * canvas_margin

            image_margin = 200

            new_image_width = image_width - 2 * image_margin
            new_image_height = image_height - 2 * image_margin

            resized_image = image.resize((new_image_width, new_image_height))

            canvas = Image.new(
                'RGB',
                (canvas_width, canvas_height),
                (255, 255, 255)
            )

            x_position = (canvas_width - new_image_width) // 2
            y_position = (canvas_height - new_image_height) // 2
            canvas.paste(resized_image, (x_position, y_position))

            final_image = Image.new(
                'RGBA',
                (image_width, image_height),
                (0, 0, 0, 0)
            )

            canvas_x = (image_width - canvas_width) // 2
            canvas_y = (image_height - canvas_height) // 2

            final_image.paste(canvas, (canvas_x, canvas_y))
            final_image.paste(frame_resized, (0, 0), frame_resized)
            final_image.save(
                new_file_path / f'{image_name.split('.')[0]}.png',
                'PNG'
            )
