from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()



@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.get_json()  # Parse the JSON payload
    user_message = data.get('message', '')  # Get the 'message' field
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": user_message
            }
        ]
    )
    ai_response = completion.choices[0].message.content

    return jsonify({'response': ai_response})

if __name__ == '__main__':
    app.run()
