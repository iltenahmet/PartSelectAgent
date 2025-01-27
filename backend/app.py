from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from searchPartTool import search_partselect
import json
from crawl import crawl

app = Flask(__name__)
client = OpenAI()
CORS(app, resources={r"/*": {"origins": ["chrome-extension://<your-extension-id>"]}})

crawl()

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_partselect",
            "description": "Search PartSelect for information about a specific part number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_number": {
                        "type": "string",
                        "description": "The part number to search for.",
                    }
                },
                "required": ["part_number"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]

system_message = {
    "role": "system",
    "content": (
        "You are a customer success agent for the PartSelect e-commerce website. "
        "Your role is to provide accurate information and assistance related to refrigerator and dishwasher parts. "
        "If the user provides a part number, use the search_partselect function to find information about it. "
        "You can help customers identify compatible parts, provide installation instructions, offer troubleshooting advice, and assist with transactions. "
        "Do not answer questions outside this scope. Focus on providing efficient, clear, user-friendly, and concise responses."
        "Return your output in plain text format, don't use any markdown elements, make sure your answer doesn't have extra newline elements"
    ),
}


@app.route("/api/message", methods=["POST"])
def handle_message():
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    messages = [
        system_message,
        {"role": "user", "content": user_message},
    ]
    response = get_first_completion(messages)

    if not response.tool_calls:
        return jsonify({"response": response.content})

    args = json.loads(response.tool_calls[0].function.arguments)
    result = search_partselect(args["part_number"])
    second_response = get_completion_after_search_tool(messages, response, result)

    return jsonify({"response": second_response.content})


def get_first_completion(messages):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    return completion.choices[0].message


def get_completion_after_search_tool(messages, prevResponse, result):
    messages.append(prevResponse)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": prevResponse.tool_calls[0].id,
            "content": result,
        }
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )

    return completion.choices[0].message


if __name__ == "__main__":
    app.run()
