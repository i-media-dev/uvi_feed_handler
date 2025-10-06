from handler.decorators import time_of_function, time_of_script
from handler.feeds_save import XMLSaver
from handler.image_handler import XMLImage
from handler.feeds_handler import XMLHandler


@time_of_script
@time_of_function
def main():
    # save_client = XMLSaver()
    image_client = XMLImage()
    # handler_client = XMLHandler()
    # save_client.save_xml()
    image_client.get_images()
    # image_client.add_frame()
    # handler_client.image_replacement()


if __name__ == '__main__':
    main()
