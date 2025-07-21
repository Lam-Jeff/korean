import logging
import bs4  # type: ignore
import requests  # type: ignore

logging.basicConfig(level=logging.INFO)


def extract_text():
    logging.info("##### SCRAPPING HTML LINKS FOR KOREAN TEXTS #####")
    htmls = []
    with open("htmls.txt", "r") as file:
        lines = file.readlines()
        for i in range(0, len(lines)):
            htmls.append(lines[i].rstrip("\n"))

    htmls = list(set(htmls))
    htmls = [html for html in htmls if ".html" in html]
    if len(htmls) > 0:
        for html in htmls:
            response = requests.get(html)
            if response:
                soup = bs4.BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("span")
                for paragraph in paragraphs:
                    with open("data/korean_texts.txt", "a") as file:
                        if paragraph:
                            print(paragraph.text, file=file)
    else:
        logging.warning("No html links.")


extract_text()
