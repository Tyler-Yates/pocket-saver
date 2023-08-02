import json

from pocketsaver.constants import KEY_PROPERTY, SAVE_PATH_PROPERTY
from pocketsaver.pocket_saver import PocketSaver


def main():
    with open("config.json", mode="r") as config_file:
        json_data = json.load(config_file)
        pockey_key = json_data[KEY_PROPERTY]
        save_path = json_data[SAVE_PATH_PROPERTY]

    pocket_saver = PocketSaver(pocket_key=pockey_key, save_path=save_path)
    pocket_saver.save_pocket()


if __name__ == '__main__':
    main()
