from flask import Flask, request, jsonify
import os
import logging
from google.cloud import dialogflowcx_v3 as dialogflow
import re
from meta_ai_api import MetaAI
from wordcloud import WordCloud
import numpy as np

ai = MetaAI()

app = Flask(__name__)

# Set Dialogflow credentials from environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH", 'pt-generative-bot-04bdfdba5a53.json')

# Initialize the Dialogflow session client
session_client = dialogflow.SessionsClient()

# Define your Dialogflow project, location, and agent ID
PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID", 'pt-generative-bot')
LOCATION = os.getenv("DIALOGFLOW_LOCATION", 'global')
AGENT_ID = os.getenv("DIALOGFLOW_AGENT_ID", '1f1d819c-4c53-4ac2-845b-79060f54ad11')

# Regular expression pattern to match alphanumeric sequences that resemble model numbers
model_number_pattern = r'\b[A-Z0-9-]+\b'

    
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    if not req or 'queryResult' not in req or 'session' not in req:
        logging.error("Invalid request received: %s", req)
        return jsonify({'fulfillmentText': "Invalid request"}), 400

    session_id = req['session']
    query_text = req['queryResult'].get('queryText', '')

    # Check if query contains alphanumeric sequences resembling model numbers
    if re.search(model_number_pattern, query_text):
        return jsonify({'fulfillmentText': "Thanks for providing the model number. Can you please tell what specific problem you are facing?"})


    response_text = detect_intent_texts(PROJECT_ID, LOCATION, AGENT_ID, session_id, query_text, 'en-US')

    return jsonify({'fulfillmentText': response_text})

def detect_intent_texts(project_id, location, agent_id, session_id, text, language_code):
    """Sends the user query to Dialogflow CX and returns the agent's response."""
    session_path = f"projects/{project_id}/locations/{location}/agents/{agent_id}/sessions/{session_id}"
    text_input = dialogflow.TextInput(text=text)
    query_input = dialogflow.QueryInput(text=text_input, language_code=language_code)

    try:
        response = session_client.detect_intent(request={"session": session_path, "query_input": query_input})

        # Extract fulfillment text from the first text response
        if response.query_result.response_messages and response.query_result.response_messages[0].text:
            return response.query_result.response_messages[0].text.text[0]
        else:
            return "No valid response from Dialogflow"

    except Exception as e:
        logging.error("Error during Dialogflow CX interaction: %s", e)
        return "An error occurred while processing your request."
    


# if __name__ == '__main__':
#     app.run(debug=True)
