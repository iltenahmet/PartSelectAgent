'''
This file crawls PartSelect for product information and stores relevant data in a vector database.
It uses asynchronous web crawling to gather markdown content from specified URLs and extracts product URLs.
The script also processes the extracted data, adding product details to a vector database if not already present.
Command-line arguments allow customization of the starting URL and the number of products to scrape.

Check README.md for instruction on how to use this script.
'''

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import re
import queue
import argparse
from vector_db import add_to_vector_db, is_in_vector_db
from app import llm_client


async def crawl_async(url):
    '''
    Crawl a given url with crawl4AI, return the resulting document in a markdown format.
    '''
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return result.markdown


def crawl(url):
    '''
    Calls the async crawl function. 
    Other files should use this instead of crawl_async so that the async operations are handled within this file
    '''
    return asyncio.run(crawl_async(url))


def crawl_multiple(urls: list) -> list:
    '''
    Crawls multiple urls, returns a list of markdown content
    '''
    res = []
    for url in urls:
        res.append(asyncio.run(crawl_async(url)))
    return res


def find_and_add_products(limit: int, starting_url: str):
    '''
    Crawls websites in a breadth-first manner, starting from the starting_url.
    Continues until it can't find additional pages to crawl or limit is reached.
    Limit specifies the maximum amount of product pages the algorithm will crawl.
    '''

    # Make sure we visit each url only once
    visited_urls = set()
    visited_product_urls = set()

    urls = queue.Queue()
    urls.put(starting_url)

    # Continue until the queue has no items left or we reach the limit
    while urls and len(visited_product_urls) < limit:
        url = urls.get()
        if url in visited_urls:
            continue

        visited_urls.add(url)
        markdown = asyncio.run(crawl_async(url))
        # add urls with potential product links into the queue to be processed later
        for url in extract_general_urls(markdown):
            if url not in visited_urls:
                urls.put(url) 

        # process the product links in the current url
        product_urls = extract_product_urls(markdown)
        for product_url in product_urls:
            if len(visited_product_urls) >= limit:
                break
            if product_url in visited_product_urls:
                continue
            visited_urls.add(product_url)
            visited_product_urls.add(product_url)
            # no need to crawl again if the product is already in the database
            if is_in_vector_db(product_url):
                continue

            # scrape the product page and pass the markdown to add to the database
            product_markdown = asyncio.run(crawl_async(product_url))
            add_to_vector_db(product_markdown, product_url, llm_client)


def extract_product_urls(text):
    '''
    Given a text in markdown format, extracts all the urls that leads to a product page
    '''

    if "page not found" in text.lower():
        return []

    # This pattern indicates the line above contains a link to a product page
    partselect_pattern = r"PartSelect Number \*\*PS(\d{8})\*\*"
    lines = text.splitlines()
    extracted_urls = []

    for i in range(1, len(lines)):
        match = re.search(partselect_pattern, lines[i])
        if match:
            # If a given line matches with the pattern, the line above usually contains a link to the product page
            previous_line = lines[i - 1]

            # Extract the url for the product page
            url_match = re.search(r"https://www\.partselect\.com/.*?\) ", previous_line)
            if url_match:
                url = url_match.group(0)
                extracted_urls.append(clean_url(url))

    return extracted_urls


def extract_general_urls(text):
    '''
    Given a text in markdown format, extract urls that may contain links to product pages
    '''

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
        # Make sure the resulting page is contains the keywords dishwashers and refrigerators
        # otherwise it's most likely to be irrelevant
        if "dishwasher" in url.lower() or "refrigerator" in url.lower():
            extracted_urls.append(url)

    return extracted_urls


def clean_url(url):
    extracted_part = url.split("</")[-1].split(">")[0]
    cleaned_url = f"https://www.partselect.com/{extracted_part}"
    return cleaned_url


if __name__ == "__main__":
    '''
    Parse command line arguments and call find_and_add_products with the given arguments
    '''

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
