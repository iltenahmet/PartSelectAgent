"""
This file is responsible for browsing the part select website, give a product number.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from markdownify import markdownify
import time


def search_partselect(search_term: str) -> str:
    """
    Crawl through the PartSelect website to retrieve information about a specific part or model number
    """
    with sync_playwright() as playwright:
        # Launch a new browser instance
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        """
        NOTE: There is room for optimization here. 
        The browser is not launched in headless mode because PartSelect seems to detect it and denies access.  
        If PartSelect's headless browser detection can be circumvented, it'd take significantly less resources to launch a browser instance.
        """

        try:
            page.goto("https://www.partselect.com/", timeout=10000)
            page.wait_for_load_state("networkidle")

            # If pop-up's appear, find the decline button and close the pop-up window so that we can use the search box
            decline_button_locator = page.locator(
                "button[aria-label='Decline; close the dialog']"
            )
            for i in range(decline_button_locator.count()):
                if decline_button_locator.nth(i).is_visible():
                    print(f"Clicking decline button {i + 1}...")
                    decline_button_locator.nth(i).click()
                    time.sleep(0.5)

            # Wait for the search box to be available, enter the search_term and hit the search button
            page.wait_for_selector("#searchboxInput", timeout=10000)
            page.fill("#searchboxInput", search_term)
            with page.expect_navigation(timeout=10000):
                page.click("button.btn--teal")

            # return the resulting site in markdown format
            return html_to_markdown(page.content())

        except Exception as e:
            print(f"An error occurred: {e}")
            return "An error has occurred during searching Part Select."

        finally:
            browser.close()


def html_to_markdown(html_content: str) -> str:
    '''
    Convert html to easily readable markdown format
    '''
    soup = BeautifulSoup(html_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    cleaned_html = soup.prettify()

    markdown_content = markdownify(cleaned_html, heading_style="ATX")
    return markdown_content
