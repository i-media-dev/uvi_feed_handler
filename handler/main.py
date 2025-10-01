from handler.decorators import time_of_function, time_of_script
from handler.feeds_save import XMLSaver


@time_of_script
@time_of_function
def main():
    save_client = XMLSaver()
    save_client.save_xml()


if __name__ == '__main__':
    main()
