from flask import Flask

app = Flask(__name__)

@app.route('/api/message', methods=['POST'])
def handle_message():
    '''
    data = request.get_json()
    message = data.get('message')
    print("message is: " + message)
    if not message:
        return {'error': 'No message provided'}, 400

    # Placeholder response
    response = f"You said: {message}"
    print(response);
    return {'response': response}
    '''

if __name__ == '__main__':
    app.run()
