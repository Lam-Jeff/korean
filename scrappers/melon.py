import os
import json
from dotenv import load_dotenv

load_dotenv()

directory = f"{os.getenv('PATH_TO_PROJECT')}/korean/data/melon"


for root, _, files in os.walk(directory):
    for filename in files:  # loop through files in the current directory
        path = os.path.join(root, filename)
        with (
            open(path, "r", encoding="utf-8") as file,
            open("data/lyrics.txt", "a") as lyrics_file,
        ):
            data = json.load(file)
            lines = data["lyrics"]["lines"]
            for line in lines:
                print(line, file=lyrics_file)
