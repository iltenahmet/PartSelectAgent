import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from url_normalize import url_normalize
import re
import time

PRODUCT_LIMIT = 50

async def crawl_async(url):
    browser_config = BrowserConfig()  # Default browser configuration
    run_config = CrawlerRunConfig()  # Default crawl run configuration

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return result.markdown


def get_all_relevant_product_urls():
    visited_product_urls = set()
    initial_markdown = asyncio.run(crawl_async("https://www.partselect.com/"))
    list_urls = extract_list_urls(initial_markdown)
    visited_urls = set()

    while list_urls and len(visited_product_urls) < PRODUCT_LIMIT:
        list_url = list_urls.pop()
        if list_url in visited_urls:
            continue

        print("visiting: " + list_url)
        visited_urls.add(list_url)
        list_page_markdown = asyncio.run(crawl_async(list_url))
        other_lists = extract_list_urls(list_page_markdown)
        list_urls += other_lists

        products = extract_product_urls(list_page_markdown)
        for product_url in products:
            if len(visited_product_urls) >= PRODUCT_LIMIT:
                break
            if product_url not in visited_product_urls:
                visited_product_urls.add(product_url)

    return list(visited_product_urls)


# TODO: Explain
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


def extract_list_urls(text):
    if "page not found" in text.lower():
        return []

    list_item_pattern = r"\*\s+\[.*?\]\((https://www\.partselect\.com/.*?)\)"

    lines = text.splitlines()
    extracted_urls = []

    for line in lines:
        match = re.search(list_item_pattern, line)
        if match and ("dishwasher" in line.lower() or "refrigerator" in line.lower()):
            url = match.group(1) 
            extracted_urls.append(clean_url(url))

    return extracted_urls


def clean_url(url):
    extracted_part = url.split("</")[-1].split(">")[0]
    cleaned_url = f"https://www.partselect.com/{extracted_part}"
    return cleaned_url


def crawl():
    start_time = time.time() 
    urls = get_all_relevant_product_urls()
    end_time = time.time()
    
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"Time passed for get_all_relevant_product_urls(): {elapsed_time:.2f} seconds")
    print("total_product_count: " + str(len(urls)))

    with open("product_urls.txt", "w") as file:
        for i, url in enumerate(urls, start=1):
            file.write(f"{i}) {url}\n")
    