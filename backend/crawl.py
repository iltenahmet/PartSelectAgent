import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import re

async def crawl_async():
	browser_config = BrowserConfig()  # Default browser configuration
	run_config = CrawlerRunConfig()  # Default crawl run configuration

	async with AsyncWebCrawler(config=browser_config) as crawler:
		result = await crawler.arun(
			url="https://www.partselect.com/Dishwasher-Dishracks.htm", config=run_config
		)
		with open("results1.md", "w") as file:
			file.write(result.markdown)

		with open("extractedLists.md", "w") as file:
			for url in extract_list_urls(result.markdown):
				file.write("\n")
				file.write(url)


# TODO: Explain
def extract_part_urls(text):
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
				cleaned_url = url.replace("</", "").replace(">", "").strip(" )")
				extracted_urls.append(cleaned_url)

	return extracted_urls

def extract_list_urls(text):
	list_item_pattern = r"\*\s+\[.*?\]\((https://www\.partselect\.com/.*?)\)"
	
	lines = text.splitlines()
	extracted_urls = []

	for line in lines:
		match = re.search(list_item_pattern, line)
		if match and ("dishwasher" in line.lower() or "refrigerator" in line.lower()):
			url = match.group(1)  # Extract the URL from the regex match
			cleaned_url = url.replace("</", "").replace(">", "").strip()
			extracted_urls.append(cleaned_url)
		match = re.search(list_item_pattern, line)

	return extracted_urls


def crawl():
	asyncio.run(crawl_async()) 
