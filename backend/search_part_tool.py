from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from markdownify import markdownify
import time


def search_partselect(search_term: str):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            page.goto("https://www.partselect.com/", timeout=10000)
            page.wait_for_load_state("networkidle")

            decline_button_locator = page.locator(
                "button[aria-label='Decline; close the dialog']"
            )
            for i in range(decline_button_locator.count()):
                if decline_button_locator.nth(i).is_visible():
                    print(f"Clicking decline button {i + 1}...")
                    decline_button_locator.nth(i).click()
                    time.sleep(0.5)

            page.wait_for_selector("#searchboxInput", timeout=10000)
            page.fill("#searchboxInput", search_term)
            with page.expect_navigation(timeout=10000):
                page.click("button.btn--teal")

            return html_to_markdown(page.content())

        except Exception as e:
            print(f"An error occurred: {e}")
            return "An error has occurred during searching Part Select."

        finally:
            browser.close()


def html_to_markdown(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    cleaned_html = soup.prettify()

    markdown_content = markdownify(cleaned_html, heading_style="ATX")
    return markdown_content
