import requests
from bs4 import BeautifulSoup
import logging
from googletrans import Translator


def translate_word_wiktionary(word: str) -> list[str]:
    url = f"https://en.wiktionary.org/wiki/{word}"

    response = requests.get(url)
    if response.status_code != 200:
        logging.warning("Failed to fetch page.")
        return None
    soup = BeautifulSoup(response.text, "html.parser")

    page_content = soup.find("div", {"class": "mw-content-ltr mw-parser-output"})

    if not page_content:
        logging.warning("Could not find page content.")
        return None

    # headword_line = page_content.find("span", {"class": "headword-line"})
    translations = []
    ol = page_content.find("ol")
    for li in ol.find_all("li"):
        dl_tag = li.find("dl")
        if dl_tag:
            dl_tag.extract()
        translations.append(li.text)
    return translations


# The MIT License (MIT)

# Copyright (c) 2015 SuHun Han

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.


# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
async def translate_word_googletrans(word: str, src: str, dest: str) -> str:
    async with Translator() as translator:
        result = await translator.translate(word, src=src, dest=dest)
    return result.text


def translate_word_Glosbe(word: str, src: str, dest: str) -> str:
    url = f"https://glosbe.com/{src}/{dest}/{word}"
    response = requests.get(url)
    if response.status_code != 200:
        logging.warning("Failed to fetch page.")
        return None
    soup = BeautifulSoup(response.text, "html.parser")

    page_content = soup.find("section", {"class": "bg-white px-1"})

    if not page_content:
        logging.warning("Could not find page content.")
        return None

    translations = []
    ul_translation = page_content.find("ul", {"class": "pr-1"})

    for li in ul_translation.find_all("li"):
        h3 = li.find("h3")
        translations.append(h3.text)
    return translations


def translate_word_Daum(word: str) -> list[str]:
    url = f"https://dic.daum.net/search.do?q={word}"
    response = requests.get(url)
    if response.status_code != 200:
        logging.warning("Failed to fetch page.")
        return None
    soup = BeautifulSoup(response.text, "html.parser")

    page_content = soup.find("div", {"class": "search_cont"})

    if not page_content:
        logging.warning("Could not find page content.")
        return None

    translations = []
    table_translation = page_content.find_all("div", {"class": "card_word"})[1]
    translation = table_translation.find("div", {"class": "search_type kuke_type"})

    for li in translation.find_all("li"):
        text_span = li.find("span", {"class": "txt_search"})
        translations.append(text_span.text)
    return translations


def translate_word_wordreference(word: str) -> list[str]:
    url = f"https://www.wordreference.com/koen/{word}"
    response = requests.get(url)
    if response.status_code != 200:
        logging.warning("Failed to fetch page.")
        return None
    soup = BeautifulSoup(response.text, "html.parser")

    page_content = soup.find("td", {"id": "centercolumn"})

    if not page_content:
        logging.warning("Could not find page content.")
        return None

    translations = []
    table_translation = page_content.find("table", {"class": "WRD"})

    for td in table_translation.find_all("td", {"class": "FrWrd"})[1:]:
        translations.append(td.text)
    return translations
