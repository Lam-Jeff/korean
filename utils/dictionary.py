from dotenv import load_dotenv
import os
import logging
import requests
import bs4
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
load_dotenv()

KOREAN_DICT_API_KEY = os.getenv("KOREAN_DICT_API_KEY")
KOREAN_DICT_MAIN_URL = "https://krdict.korean.go.kr/api/search"  # 50_000 tokens/day


def search_word_in_dictionary(word, API_KEY, url):
    params = {
        "key": API_KEY,
        "q": word,
        "translated": "y",
        "trans_lang": "1",
        "part": "word",
    }
    try:
        request_url = (
            url
            + f"?key={params['key']}&q={params['q']}&translated={params['translated']}&trans_lang={params['trans_lang']}&part={params['part']}"
        )
        session = requests.Session()

        retries = Retry(
            total=3,  # 🔁 Nombre total de tentatives
            backoff_factor=1,  # ⏳ Temps d’attente croissant (1s, 2s, 4s, etc.)
            status_forcelist=[502, 503, 504],  # Réessayer pour ces codes HTTP
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        response = session.get(request_url)
        soup = bs4.BeautifulSoup(response.text, "xml")
        trans_dfn_soup = soup.find("trans_dfn")
        definition_soup = soup.find("definition")
        pos_soup = soup.find("pos")
        target_code_soup = soup.find("target_code")
        trans_word_soup = soup.find("trans_word")

        if trans_dfn_soup is not None:
            definition = trans_dfn_soup.get_text()
        elif definition_soup is not None:
            definition = definition_soup.get_text()
        else:
            definition = ""

        if pos_soup is not None:
            pos = soup.find("pos").get_text()
        else:
            pos = ""

        if target_code_soup is not None:
            target_code = soup.find("target_code").get_text()
        else:
            target_code = ""

        if trans_word_soup is not None:
            trans_word = soup.find("trans_word").get_text()
        else:
            trans_word = ""

        data = {
            "word": word,
            "definition": definition,
            "pos": pos,
            "target_code": target_code,
            "trans_word": trans_word,
        }

        return data
    except Exception as e:
        logging.exception(str(e))
    return None


def search_example(word, API_KEY, url):
    params = {
        "key": API_KEY,
        "q": word,
        "part": "exam",
    }
    try:
        request_url = (
            url + f"?key={params['key']}&q={params['q']}&part={params['part']}"
        )
        session = requests.Session()

        retries = Retry(
            total=3,  # 🔁 Nombre total de tentatives
            backoff_factor=1,  # ⏳ Temps d’attente croissant (1s, 2s, 4s, etc.)
            status_forcelist=[502, 503, 504],  # Réessayer pour ces codes HTTP
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        response = session.get(request_url)
        soup = bs4.BeautifulSoup(response.text, "xml")
        example_soup = soup.find("example")

        if example_soup is not None:
            example = example_soup.get_text()
        else:
            example = "..."
        return example
    except Exception as e:
        logging.exception(str(e))
    return None
