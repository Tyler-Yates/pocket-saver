import json
import os.path
import re
import time
import webbrowser
from typing import Dict

import requests
import unicodedata
from selenium import webdriver

from pocketsaver.constants import POCKET_API_URL, REDIRECT_URI


class PocketSaver:
    def __init__(self, pocket_key: str, save_path: str):
        self.pocket_key = pocket_key
        self.save_path = save_path

        self._access_token = None

        self.title_to_url = dict()

        self._pocket_auth()

    def _pocket_auth(self):
        print("Attempting authentication...")
        response = requests.post(f"{POCKET_API_URL}/oauth/request", headers={"X-Accept": "application/json"}, params={"consumer_key": self.pocket_key, "redirect_uri": REDIRECT_URI})
        response.raise_for_status()

        json_data = json.loads(response.text)
        oauth_token = json_data["code"]

        print("Opening browser for user acceptance...")
        webbrowser.open_new_tab(f"https://getpocket.com/auth/authorize?request_token={oauth_token}&redirect_uri={REDIRECT_URI}")

        for i in range(100):
            time.sleep(5)
            try:
                auth_response = requests.post(f"https://getpocket.com/v3/oauth/authorize", headers={"X-Accept": "application/json"}, params={"consumer_key": self.pocket_key, "code": oauth_token})
                print("Success!")
                auth_response.raise_for_status()
                auth_json = json.loads(auth_response.text)
                self._access_token = auth_json["access_token"]
                return
            except Exception:
                print(f"Auth failed. Waiting some time to try again...")

    def save_pocket(self):
        response = requests.get(f"{POCKET_API_URL}/get",
                                params={"consumer_key": self.pocket_key, "access_token": self._access_token})
        response.raise_for_status()
        json_data = response.json()
        saves: Dict = json_data["list"]
        for save in saves.values():
            item_id = save["item_id"]
            resolved_title = save["resolved_title"]
            resolved_url = save["resolved_url"]

            name = self._slugify(f"{item_id}_{resolved_title}")
            name = name[:100] if len(name) > 100 else name
            print(f"Processing {name} - {resolved_url}")
            self.title_to_url[name] = resolved_url
            self._save_webpage_to_disk(resolved_url, name)

        with open(os.path.join(self.save_path, "pocket_saves.json"), 'w') as fp:
            json.dump(self.title_to_url, fp)

    def _save_webpage_to_disk(self, url: str, name: str):
        save_path = os.path.join(self.save_path, f"{name}.mhtml")

        if os.path.exists(save_path):
            print(f"File {save_path} already exists. Skipping.")
            return

        driver = webdriver.Chrome()
        driver.get(url)

        # Execute Chrome dev tool command to obtain the mhtml file
        res = driver.execute_cdp_cmd('Page.captureSnapshot', {})

        # Write the file locally
        with open(save_path, 'w', newline='') as f:
            f.write(res['data'])

        print(f"Saved webpage to {save_path}")
        driver.quit()

    @staticmethod
    def _slugify(value: str, allow_unicode=False):
        """
        Taken from https://github.com/django/django/blob/master/django/utils/text.py
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')
