from flask import Flask, request, jsonify
from flask_cors import CORS
from customer_agent import query_customer_agent
from openai import OpenAI
from vector_db import *

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["chrome-extension://<your-extension-id>"]}})

llm_client = OpenAI()

NUM_PRODUCTS = 100

start = time.time()
fill_vector_db(llm_client, NUM_PRODUCTS)
end = time.time()
print(f"TOTAL time spent to scrape and add {NUM_PRODUCTS} products: {end - start:.2f}s ")

query = "Which part fixes leaking issues in Whirlpool dishwashers?"
query_chroma(query)


@app.route("/api/message", methods=["POST"])
def handle_message():
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    content = query_customer_agent(user_message, llm_client)
    return jsonify({"response": content})


if __name__ == "__main__":
    app.run()
