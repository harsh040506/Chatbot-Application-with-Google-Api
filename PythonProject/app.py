from flask import Flask, jsonify, request  # Import Flask for building the app and jsonify/request for handling requests
import requests, json, time  # Import necessary libraries for API calls and handling JSON data
from flask_cors import CORS  # Import CORS for enabling cross-origin requests

# Initialize the Flask application
application = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) for all routes
CORS(application)


# Define a POST route at `/call-api` to handle API requests
@application.route('/call-api', methods=['POST'])
def call_api():
    # Get JSON data from the incoming request
    data = request.get_json()

    # Extract the `conversation` list from the request, defaulting to an empty list if not provided
    conversation = data.get('conversation', [])

    # Format the conversation into a single text block, prepending "User: " or "Bot: " to each message
    conversation_text = "\n".join(
        f"User: {entry['message']}" if entry['sender'] == 'user' else f"Bot: {entry['message']}"
        for entry in conversation
    )

    # Define the base URL for the external API. Replace `your_api_key` with your actual API key
    base_url = ("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?"
                "key=your_api_key")

    # Set the request headers for the API call
    headers = {"Content-Type": "application/json"}

    # Construct the payload to send to the external API
    payload = {
        "contents": [
            {"parts": [
                {"text": conversation_text}
            ]}
        ]
    }

    # Define the maximum number of retry attempts in case of server unavailability
    max_retries = 50

    # Retry logic with exponential backoff for handling server errors (HTTP 503)
    for attempt in range(max_retries):
        # Send the POST request to the API
        response = requests.post(base_url, headers=headers, data=json.dumps(payload))

        # If the server is unavailable, wait and retry (exponential backoff)
        if response.status_code == 503:
            time.sleep(2 ** attempt)
        else:
            break  # Exit the loop if a response other than 503 is received

    # Check if the API response was successful
    if response.status_code == 200:
        response_json = response.json()  # Parse the JSON response

        # Check if the response contains valid candidates
        if 'candidates' in response_json:
            # Extract the text from all candidate parts and combine them
            text_parts = [part['text'] for candidate in response_json['candidates']
                          for part in candidate['content']['parts']]
            combined_text = "\n\n".join(text_parts)

            # Return the combined text as a JSON response
            return jsonify({"response": combined_text})
        else:
            # Handle the case where no valid response text is found
            return jsonify({"error": "No valid response text found."}), 500
    else:
        # Handle errors by returning the API's error message and status code
        return jsonify({"error": response.text}), response.status_code


# Run the Flask application in debug mode on port 5000
if __name__ == '__main__':
    application.run(debug=True, port=5000)