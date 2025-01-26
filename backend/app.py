from flask import Flask, request, jsonify
from openai import OpenAI
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from playwright.sync_api import sync_playwright
import time
import json
from bs4 import BeautifulSoup
from markdownify import markdownify

app = Flask(__name__)
client = OpenAI()

# Define the tools (functions) schema
tools = [{
    "type": "function",
    "function": {
        "name": "search_partselect",
        "description": "Search PartSelect for information about a specific part number.",
        "parameters": {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "The part number to search for."
                }
            },
            "required": ["part_number"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.get_json()
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400


    messages = [{
                "role": "system",
                "content": (
                    "You are a customer success agent for the PartSelect e-commerce website. "
                    "Your role is to provide accurate information and assistance related to refrigerator and dishwasher parts. "
                    "If the user provides a part number, use the search_partselect function to find information about it. "
                    "You can help customers identify compatible parts, provide installation instructions, offer troubleshooting advice, and assist with transactions. "
                    "Do not answer questions outside this scope. Focus on providing efficient, clear, and user-friendly responses."

                ),
            },
            {"role": "user", "content": user_message},
        ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"  # Allow the model to decide whether to call the function
    )

    response = completion.choices[0].message
    if not response.tool_calls:
        return jsonify({"response": completion.choices[0].message.content})

    args = json.loads(response.tool_calls[0].function.arguments)
    result = search_partselect(args["part_number"])

    messages.append(completion.choices[0].message)  # append model's function call message
    messages.append({                               # append result message
        "role": "tool",
        "tool_call_id": response.tool_calls[0].id,
        "content": result
    })


    completion_2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
    )

    return jsonify({"response": completion_2.choices[0].message.content})

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
            
            decline_button_locator = page.locator("button[aria-label='Decline; close the dialog']")
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
            return None

        finally:
            browser.close()

def html_to_markdown(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.extract()
    cleaned_html = soup.prettify()

    markdown_content = markdownify(cleaned_html, heading_style="ATX")
    return markdown_content


if __name__ == '__main__':
    app.run()
