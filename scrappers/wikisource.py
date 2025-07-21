# https://github.com/storidient/KoCoNovel/tree/main
import logging
import pandas as pd
import requests
import bs4

logging.basicConfig(level=logging.INFO)
logging.info("##### SCRAPPING WIKISOURCE #####")

URL = "https://ko.wikisource.org/wiki/"


def extract_novels():
    csv_file = pd.read_csv("./data/list_novels.csv")
    for _, row in csv_file.iterrows():
        logging.info(f"Scrapping wikisource for: {row['Korean Title']}")
        link = URL + row["Korean Title"].replace(" ", "_")
        try:
            response = requests.get(link)
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            main = soup.find("div", {"id": "mw-content-text"})
            paragraphs = main.find_all("p")
            for p in paragraphs:
                with open(
                    f"./data/novels/{row['Translated Title']}.txt",
                    "a",
                    encoding="utf-8",
                ) as f:
                    print(p, file=f)
        except Exception as e:
            logging.exception(str(e))


extract_novels()
