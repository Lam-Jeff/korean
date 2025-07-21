import bs4
import requests
from seleniumwire import webdriver
import aiohttp
import asyncio
import random
import os
from dotenv import load_dotenv
import logging
import pandas as pd
from datetime import datetime
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)

MAIN_URL = "https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrtText.do?menuNo=200019&pageUnit=96"
DOMAIN = "https://gongu.copyright.or.kr"
CUSTOM_URL = "https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrtText.do"
USER_AGENT = os.getenv("USER_AGENT")


async def extract_data(text):
    links_list = []
    html = bs4.BeautifulSoup(text, "html.parser")
    articles_feed = html.find("div", {"class": "bbsList style2 wrt"})
    articles = articles_feed.find_all("li")
    for article_ in articles:
        original_text_button = article_.find("div", {"class": "col-md-2"})
        if original_text_button is not None:
            link = DOMAIN + article_.find("a")["href"]
            links_list.append(link)
    return links_list


def extract_html(data, retries=3):
    logging.info("Saving xhtml file...")
    seleniumwire_options = {"disable_encoding": True}
    aborted = 0
    new_htmls = 0
    requested = 0
    try:
        html_logs = []
        with open("html_logs", "r") as file:
            lines = file.readlines()
        for i in range(0, len(lines)):
            html_logs.append(lines[i].rstrip("\n"))
    except Exception as e:
        logging.exception(str(e))
        html_logs = []
    driver = webdriver.Chrome(seleniumwire_options=seleniumwire_options)
    driver.implicitly_wait(10)
    for array in data:
        if array is not None and len(array) > 0:
            for link in array:
                for attempt in range(retries):
                    try:
                        driver.get(link)
                        for request in driver.requests:
                            requested += 1
                            if request.response and ".html" in request.url:
                                with (
                                    open("htmls.txt", "a") as htmls,
                                    open("html_logs.txt", "a") as logs,
                                ):
                                    if request.url not in html_logs:
                                        new_htmls += 1
                                        print(request.url, file=htmls)
                                        print(request.url, file=logs)
                                        html_logs.append(request.url)
                            else:
                                logging.info(
                                    f"{request.url} aborted: not an html url or could not get response."
                                )
                                aborted += 1
                                request.abort()
                    except Exception as e:
                        logging.exception(str(e))
    driver.quit()
    return aborted, new_htmls, requested


def update_logs(total_pages, aborted, new_htmls, requested, start_time):
    now = datetime.now()
    date_time_str = now.strftime("%Y%m%d")
    CSV_FILE_PATH = date_time_str + "_logs.csv"
    duration = time.time() - start_time

    data = {
        "Date": date_time_str,
        "Total_Pages": total_pages,
        "Aborted_Number": aborted,
        "New_Htmls_Number": new_htmls,
        "Requested_Number": requested,
        "Estimated_Duration": duration,
    }
    df = pd.DataFrame(data)
    df.to_csv(CSV_FILE_PATH, index=False)
    logging.info(f"NEW LOGS: {date_time_str}")


async def fetch(session, page, retries=3):
    await asyncio.sleep(random.uniform(3, 7))
    for attempt in range(retries):
        try:
            params = {
                "menuNo": "200019",
                "pageUnit": "96",
                "sorteSe": "date",
                "pageIndex": page,
            }
            async with session.get(CUSTOM_URL, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    links = await extract_data(text)
                    return links
                elif response.status == 503:
                    wait_time = random.uniform(2, 7)
                    logging.warning(
                        f"Rate limited on page {page}. Retrying in {wait_time:.2f}s..."
                    )
                    await asyncio.sleep(wait_time)
                elif attempt == retries - 1:
                    await asyncio.sleep(30)
        except Exception as e:
            logging.exception(str(e))
    logging.warning(
        f"Extracting data from page {page} failed after {retries} attempts."
    )
    return None


async def scrape():
    logging.info("##### SCRAPPING GONGU #####")
    start_time = time.time()
    tasks = []
    all_data = []
    retries = 3

    try:
        response = requests.get(MAIN_URL)

        html = bs4.BeautifulSoup(response.text, "html.parser")
        pages = html.find("div", {"class": "btnrSet"})
        for tag_a_ in pages.select("a"):
            tag_a_.extract()
        total_pages_ = [int(i) for i in pages.get_text().split() if i.isdigit()][1]
        async with aiohttp.ClientSession(headers={"user-agent": USER_AGENT}) as session:
            for page in range(1, total_pages_):
                tasks.append(fetch(session, page, retries))
            articles = await asyncio.gather(*tasks)

        all_data.extend(articles)
        with open("pages.txt", "w") as f:
            print(all_data, file=f)
        aborted_, new_htmls_, requested_ = extract_html(all_data, retries)
        update_logs(total_pages_, aborted_, new_htmls_, requested_, start_time)
    except Exception as e:
        logging.exception(str(e))
        logging.info("Ending web scrapping.")


asyncio.run(scrape())
