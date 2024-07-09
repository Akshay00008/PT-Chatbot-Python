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
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH", 'C:/Users/hp/Downloads/PT-ChatBot-BE-staging/PT-ChatBot-BE-staging/v1/src/secrets/pt-generative-bot-04bdfdba5a53.json')

# Initialize the Dialogflow session client
session_client = dialogflow.SessionsClient()

# Define your Dialogflow project, location, and agent ID
PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID", 'pt-generative-bot')
LOCATION = os.getenv("DIALOGFLOW_LOCATION", 'global')
AGENT_ID = os.getenv("DIALOGFLOW_AGENT_ID", '1f1d819c-4c53-4ac2-845b-79060f54ad11')

# Regular expression pattern to match alphanumeric sequences that resemble model numbers
model_number_pattern = r'\b[A-Z0-9-]+\b'

def lama_layer(text) :

    response = ai.prompt(message=''' you are not allowed to use feeds present on internet your every response  should be targeted and specific and your response should not exceed 25 to 50 words this is important
                         
                         User queries will be related to only Process Technology PVT. LTD, specializing in ISO-certified heaters and power supplies for various industries. Your responses must be relevant and avoid generic internet options please visit to "https://www.processtechnology.com/" to have an idea do not give response related to sports, computers,.

                                        1. Handling Queries with Model Numbers:

                                        If a query includes model numbers (e.g., 'T4429-P1', '3S12429-3-P6'), respond:
                                        "Thank you for providing the model number. Can you please describe the issue you are experiencing in detail?"
                                        2. Handling Incomplete Queries:

                                        If a query lacks specificity or refers to a general item:
                                        "Could you please provide more details or specify the product you are referring to?"
                                        3. Example Scenarios:

                                        Scenario 1: Specific Query on Programming:

                                        Query: "How do I program my controller?"
                                        Response: "To assist you, could you please specify the model number of your controller?"
                                        Scenario 2: Warranty Query:

                                        Query: "What is the warranty period for my product?"
                                        Response: "Could you please provide the model number so I can check the specific warranty information?"
                                        Scenario 3: Device Issue Query:

                                        Query: "My device won't turn on."
                                        Response: "Please provide the model number and describe any lights, sounds, or messages observed."
                                        Scenario 4: Software Update Query:

                                        Query: "How do I update the software on my device?"
                                        Response: "For the correct update instructions, please specify the model number of your device."
                                        Scenario 5: Manual Request:

                                        Query: "I lost the manual for my product. Can you help?"
                                        Response: "Please provide the model number, and I'll find the digital manual for you."
                                        Scenario 6: Return Process Inquiry:

                                        Query: "I want to return my product. What is the process?"
                                        Response: "May I know your order number and the product's model number for return assistance?"
                                        4. Confirmation of Question Addressing:

                                        If the user query is specific and addresses an issue directly:
                                        "Question is addressed.'''
                                                    )

    response2 = ai.prompt(message=f'''{text}.''')



    message = response2['message']

    lines = message.split('\n')

    # print(lines)

    return lines[0]
    


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    if not req or 'queryResult' not in req or 'session' not in req:
        logging.error("Invalid request received: %s", req)
        return jsonify({'fulfillmentText': "Invalid request"}), 400

    session_id = req['session']
    query_text = req['queryResult'].get('queryText', '')
    # query_text=query_text.lower()

    # Check if query contains alphanumeric sequences resembling model numbers
    if re.search(model_number_pattern, query_text):
        return jsonify({'fulfillmentText': "Thanks for providing the model number. Can you please tell what specific problem you are facing?"})

    # If model number format not detected, proceed with Dialogflow CX
    # query_text_sample=lama_layer(query_text)
    # if query_text_sample == 'Question is adressed' :
    #     pass
    # else :
    #     return jsonify({'fulfillmentText' :query_text_sample })


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
    


if __name__ == '__main__':
    app.run(debug=True)
