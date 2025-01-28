from flask import Flask, request, jsonify, session
from flask_cors import CORS
from customer_agent import query_customer_agent
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Enable cross origin resource sharing to communicate with the React frontend
# NOTE: A more secure approach is needed before deploying on a remote server
CORS(app)

llm_client = OpenAI()

# Receive the user message
@app.route("/api/message", methods=["POST"])
def handle_message():
    data = request.get_json()
    user_message = data.get("message", "")
    enable_browsing = data.get("enable_browsing", True)
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Create a session variable to hold the chat history
    if "chat_history" not in session:
        session["chat_history"] = []

    # Query the LLM
    content = query_customer_agent(
        user_message, session["chat_history"], llm_client, enable_browsing
    )

    # Append the message and the response to the chat history
    session["chat_history"].append({"role": "user", "content": user_message})
    session["chat_history"].append({"role": "assistant", "content": content.strip()})
    session.modified = True

    return jsonify({"response": content.strip()})


# Clear session related data, including the chat memory
@app.route("/api/reset_session", methods=["POST"])
def reset_session():
    session.clear()
    return jsonify({"message": "Session memory reset successfully"})


if __name__ == '__main__':
    app.run()
