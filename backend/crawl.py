import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import re
import queue
import argparse
from vector_db import add_to_vector_db, is_in_vector_db
from app import llm_client


async def crawl_async(url):
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return result.markdown


def crawl(url):
    return asyncio.run(crawl_async(url))


def crawl_multiple(urls: list) -> list:
    """Returns a list of markdown content"""
    res = []
    for url in urls:
        res.append(asyncio.run(crawl_async(url)))
    return res


def find_and_add_products(limit: int, starting_url: str):
    visited_urls = set()
    visited_product_urls = set()

    urls = queue.Queue()
    urls.put(starting_url)

    while urls and len(visited_product_urls) < limit:
        url = urls.get()
        if url in visited_urls:
            continue

        visited_urls.add(url)
        markdown = asyncio.run(crawl_async(url))
        for url in extract_general_urls(markdown):
            if url not in visited_urls:
                urls.put(url)

        product_urls = extract_product_urls(markdown)
        for product_url in product_urls:
            if len(visited_product_urls) >= limit:
                break
            if product_url in visited_product_urls:
                continue
            visited_urls.add(product_url)
            visited_product_urls.add(product_url)
            if is_in_vector_db(product_url):
                continue
            product_markdown = asyncio.run(crawl_async(product_url))
            add_to_vector_db(product_markdown, product_url, llm_client)


def extract_product_urls(text):
    if "page not found" in text.lower():
        return []

    partselect_pattern = r"PartSelect Number \*\*PS(\d{8})\*\*"
    lines = text.splitlines()
    extracted_urls = []

    for i in range(1, len(lines)):
        match = re.search(partselect_pattern, lines[i])
        if match:
            previous_line = lines[i - 1]

            url_match = re.search(r"https://www\.partselect\.com/.*?\) ", previous_line)
            if url_match:
                url = url_match.group(0)
                extracted_urls.append(clean_url(url))

    return extracted_urls


def extract_general_urls(text):
    if "page not found" in text.lower():
        return []

    general_pattern = r"\*\s+\[.*?\]\((https://www\.partselect\.com/.*?)\)"

    lines = text.splitlines()
    extracted_urls = []

    for line in lines:
        match = re.search(general_pattern, line)
        if not match:
            continue
        url = clean_url(match.group(1))
        if "dishwasher" in url.lower() or "refrigerator" in url.lower():
            extracted_urls.append(url)

    return extracted_urls


def clean_url(url):
    extracted_part = url.split("</")[-1].split(">")[0]
    cleaned_url = f"https://www.partselect.com/{extracted_part}"
    return cleaned_url


if __name__ == "__main__":
    print("called crawl")
    parser = argparse.ArgumentParser(description="PartSelect Customer Support Agent")
    parser.add_argument(
        "--starting-url",
        type=str,
        default="https://www.partselect.com/",
        help='Starting URL for scraping or fetching data (default: "https://www.partselect.com/")',
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit to the number of products to scrape or fetch",
    )
    args = parser.parse_args()

    print("Starting to scrape PartSelect and fill the database.")
    find_and_add_products(args.limit, args.starting_url)
