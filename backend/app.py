from flask import Flask, request, jsonify
from flask_cors import CORS
from customer_agent import query_customer_agent
from openai import OpenAI

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["chrome-extension://<your-extension-id>"]}})

llm_client = OpenAI()

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
