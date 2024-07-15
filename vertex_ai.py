from flask import Flask, request, jsonify
import json
import uuid
from google.cloud import dialogflowcx_v3
from google.auth import jwt
import logging

app = Flask(__name__)

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Replace with your project ID
project_id = "pt-generative-bot"

# Path to your downloaded JSON key file
json_key_file_path = "C:/Users/hp/Desktop/Process Technology bot Python/pt-generative-bot-99bcae6381a9.json"

# Read the JSON key file content
with open(json_key_file_path, "r") as f:
    key_file_content = json.load(f)

# Audience for the JWT credential (usually the target API endpoint)
audience = "https://dialogflow.googleapis.com/google.cloud.dialogflow.cx.v3.Sessions"

# Create a JWT credential object
credentials = jwt.Credentials.from_service_account_info(
    key_file_content, audience=audience
)

# Location (e.g., 'global')
location = "global"

# Agent's unique identifier
agent_id = "1d22275f-4260-41c5-a401-f903264d8163"

# Create a session using the credentials
session_client = dialogflowcx_v3.SessionsClient(credentials=credentials)

@app.route('/webhook', methods=['POST'])
def detect_intent():
    try:
        data = request.json
        text = data['text']
        language_code = data.get('language_code', 'en')  # Default to 'en' if not provided

        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Create the session path
        session_path = session_client.session_path(project_id, location, agent_id, session_id)

        # Create the query input
        query_input = dialogflowcx_v3.QueryInput(
            text=dialogflowcx_v3.TextInput(text=text),
            language_code=language_code
        )

        # Prepare the request with the correct parameters
        detect_intent_request = dialogflowcx_v3.DetectIntentRequest(
            session=session_path,
            query_input=query_input
        )

        # Send the request and get the response
        response = session_client.detect_intent(request=detect_intent_request)
        query_result = response.query_result

        # Extract the fulfillment messages from the response
        fulfillment_messages = []
        for message in query_result.response_messages:
            if message.text:
                for text in message.text.text:
                    fulfillment_messages.append(text)

        return jsonify({"response": fulfillment_messages})

    except Exception as e:
        logging.exception("Error during detect_intent")
        return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True)
