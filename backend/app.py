from flask import Flask, request, jsonify, session
from flask_cors import CORS
from customer_agent import query_customer_agent
from openai import OpenAI
from vector_db import *
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY")
CORS(app, resources={r"/*": {"origins": ["chrome-extension://"]}})

llm_client = OpenAI()


@app.route("/api/message", methods=["POST"])
def handle_message():
    data = request.get_json()
    user_message = data.get("message", "")
    enable_browsing = data.get("enable_browsing", True)
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    if "chat_history" not in session:
        session["chat_history"] = []

    print(len(session["chat_history"]))

    content = query_customer_agent(
        user_message, session["chat_history"], llm_client, enable_browsing
    )

    session["chat_history"].append({"role": "user", "content": user_message})
    session["chat_history"].append({"role": "assistant", "content": content.strip()})
    session.modified = True

    return jsonify({"response": content.strip()})


@app.route("/api/reset_session", methods=["POST"])
def reset_session():
    # Clear the session to reset the chat memory
    session.clear()  # This clears all session data
    return jsonify({"message": "Session memory reset successfully"})


if __name__ == "__main__":
    app.run()
