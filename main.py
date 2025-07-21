import asyncio
from scrappers.gongu import scrape
import logging

logging.basicConfig(level=logging.INFO)
def main():
    asyncio.run(scrape())

if __name__ == '__main__':
    main()