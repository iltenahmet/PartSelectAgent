# PartSelectAgent

**PartSelectAgent** is a customer support agent designed to assist users with finding parts, troubleshooting, and providing product information for refrigerators and dishwashers. The agent interacts with users through a chat interface, retrieving relevant part information from a local database or, if necessary, by browsing the PartSelect website.

The agent remembers the conversation memory as long as the browser session is active or until the user presses the reset memory button.

### Architecture

- **Backend**: Flask
- **Frontend**: React
- **Web Crawling**: Utilizes **crawl4AI** to crawl the PartSelect website and extract data.
- **Data Storage**: Data is stored in a **ChromaDB** vector database.
- **Browsing Functionality**: Implemented with **Playwright** for web interactions and **BeautifulSoup** for HTML parsing.
- **Language Model**: **GPT-4o-mini**, which integrates with the browsing tool and ChromaDB. 

---

## Installation

To set up and run PartSelectAgent locally, you will need Python and Node.js installed on your machine.

### 1. Build the React Frontend

Start by setting up the frontend:

1. Navigate to the `frontend` directory.
2. Create a `.env` file and add the following configuration:

```plaintext
REACT_APP_API_URL=http://127.0.0.1:5000
```
This will allow the React frontend to connect to Flask backend once we launch the server.

NOTE: This setup is intended for local development, changes will be required to deploy this project on a remote server.

3. Once the `.env` file is set up, build the frontend by running the following command in the `frontend` directory:

```bash
npm run build
```

4. After the build is complete, open Chrome and go to the Extensions page (`chrome://extensions/`).
5. Enable Developer Mode and click on **Load Unpacked**.
6. Select the `build` directory inside the `frontend` directory.

To open the extension, right-click the extension icon and choose **Open Side Panel** from the context menu.

### 2. Build the Flask Backend

Next, set up the Flask backend:

1. Navigate to the `backend` directory.
2. Create a `.env` file and add the following configuration:

```plaintext
OPENAI_API_KEY=your-openai-api-key
FLASK_SECRET_KEY=your-flask-secret-key
```

- Replace `your-openai-api-key` with your OpenAI API key.
- Replace `your-flask-secret-key` with a secret key for signing Flask sessions.

3. Create and activate a virtual environment. You can do this with the following commands:

```bash
# For Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

4. Install the required Python dependencies by running:

```bash
pip install -r requirements.txt
```

5. Once you've installed the required the dependencies, you can start the Flask server by running: 
```bash
flask run
```
If you'd like to first populate the vector database, see the next section.

---

## Crawl and Fill the Database with PartSelect Data

To crawl PartSelect and populate the database before running the app, execute the following command:

```bash
python crawl.py --starting-url https://www.partselect.com --limit 25
```

- `--starting-url`: The URL from which the crawl will begin.
- `--limit`: The maximum number of product pages to visit (adjust according to your needs).

This will crawl the PartSelect website in a breadth-first manner. Starting from the url specified, it will add all the urls that might contain links to product pages into a queue. 

If there are links to product pages in the current url we're crawling, we crawl those product pages and pass the resulting markdown to an LLM to extract the product information. The product information is then added to the ChromaDB vector database. 

Once we're done with the current page, we pop another page from the queue and continue until the queue is empty or we hit the limit specified in the arguments.

For more details on the crawling algorithm, check the `find_and_add_products` function in `crawl.py`.

---

## Searching Through The PartSelect Website 

If the browsing functionality is enabled and the agent cannot find relevant information in the ChromaDB, it will use Playwright to search the PartSelect website for the part number. Here's how it works:

- Triggering the Search: The agent calls a function to search for the part on PartSelect. If the function is triggered, Playwright launches a browser instance, navigates to PartSelect, handles pop-ups, and performs a search using the provided part number.
- Extracting Data: Once the product page is found, it's converted into markdown and passed to the LLM.

I implemented this approach because I couldn't find a direct catalog or URL structure to access all available parts. The pages on the site show only 'popular' parts, but not the complete catalog. Some parts can only be found using their specific part number or manufacturer number, which is why the agent performs the search.

Note: This solution is not highly scalable. Launching a browser instance, handling pop-ups, and scraping product pages on every query consumes significant server resources and can be slow. If given more time, I'd optimize the vector database and minimize reliance on browsing. Each time we brose a product page, I'd add the newly scraped data to the database so that browsing becomes less frequent over time.