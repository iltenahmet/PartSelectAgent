# PartSelectAgent

PartSelectAgent is a customer support agent designed to help users find parts for Refrigerators and Dishwashers. The agent interacts with users via a chat interface, retrieving relevant part information from a local database or, if needed, by browsing the PartSelect website.

The backend is built with Flask, while the PartSelect website is crawled using `crawl4AI`. The data is stored in a ChromaDB vector database. For browsing functionality, Playwright is used for web interaction, and BeautifulSoup is used to parse the content of the web pages.

The agent operates on GPT-4o-mini, with the browsing tool and ChromaDB integrated to provide the best user experience. When a user asks a question, the agent first queries ChromaDB for relevant data. If relevant results are found, the browsing tool is bypassed. If no relevant results are found, the agent uses the browsing tool to search the PartSelect website for the correct part and retrieves detailed information.

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

NOTE: This setup is intended for local development, changes will be required to deploy this project on a remote server,

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

### 3. Fill the Database with PartSelect Data

To crawl PartSelect and populate the database before running the app, execute the following command:

```bash
python crawl.py --starting-url https://www.partselect.com --limit 25
```

- `--starting-url`: The URL from which the crawl will begin.
- `--limit`: The maximum number of product pages to visit (adjust according to your needs).

The crawler uses a breadth-first search strategy to gather data.

---