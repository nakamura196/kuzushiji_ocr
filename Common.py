import os
import requests
import json
class Common:
    @staticmethod
    def getJson(url, path):
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            df = requests.get(url).json()
            with open(path, 'w') as outfile:
                json.dump(df, outfile, ensure_ascii=False,
                indent=4, sort_keys=True, separators=(',', ': '))

        with open(path, 'r') as f:
            manifest = json.load(f)

        return manifest