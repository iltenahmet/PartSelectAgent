from flask import Flask, request, jsonify
from openai import OpenAI
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from playwright.sync_api import sync_playwright
import time

app = Flask(__name__)
client = OpenAI()


@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.get_json()  
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400


    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a customer success agent for the PartSelect e-commerce website. "
                    "Your role is to provide accurate information and assistance related to refrigerator and dishwasher parts. "
                    "You can help customers identify compatible parts, installation instructions, troubleshooting advice, and assist with transactions. "
                    "Do not answer questions outside this scope. Focus on providing efficient, clear, and user-friendly responses."
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )
    ai_response = completion.choices[0].message.content

    return jsonify({'response': ai_response})


async def crawl():
    browser_config = BrowserConfig()  # Default browser configuration
    run_config = CrawlerRunConfig()   # Default crawl run configuration

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.partselect.com/",
            config=run_config
        )
        print(result.markdown)  # Print clean markdown content


def search_partselect(search_term: str):
    print("searching part select")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print("navigating to part select now")
            page.goto("https://www.partselect.com/", timeout=10000)

            page.wait_for_load_state("networkidle")
            
            print("Handling popups...")
            decline_button_locator = page.locator("button[aria-label='Decline; close the dialog']")
            for i in range(decline_button_locator.count()):
                if decline_button_locator.nth(i).is_visible(): 
                    print(f"Clicking decline button {i + 1}...")
                    decline_button_locator.nth(i).click()
                    time.sleep(0.5) 

            print("done with popups")

            page.wait_for_selector("#searchboxInput", timeout=10000)
            page.fill("#searchboxInput", search_term)
            page.click("button.btn--teal")
        
            # TODO: LEFT here

            # Wait for the results page to load
            page.wait_for_selector(".search-results", timeout=10000)  # Adjust based on the results structure

            # Extract search results
            results = page.query_selector_all(".search-result-item")  # Adjust based on result item selector
            output = []
            for result in results:
                title_element = result.query_selector(".title")
                link_element = result.query_selector("a")
                title = title_element.inner_text() if title_element else "No title"
                link = link_element.get_attribute("href") if link_element else "No link"
                output.append({"title": title, "link": link})

            print(output)
            return output


        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        finally:
            # Close the browser
            browser.close()


search_partselect("PS11756150");

if __name__ == '__main__':
    app.run()
