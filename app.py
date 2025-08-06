import requests
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Correctly get the environment variable names
# The values will be set during deployment on IBM Cloud Code Engine
API_KEY = os.environ.get("API_KEY")
DEPLOYMENT_ID = os.environ.get("DEPLOYMENT_ID")

if not API_KEY or not DEPLOYMENT_ID:
    # This check is now effective. It will raise an error if the variables are not set
    # during local run or deployment.
    raise ValueError("API_KEY and DEPLOYMENT_ID must be set as environment variables.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'response': 'No message provided.'})

    try:
        # Get the access token
        token_response = requests.post(
            'https://iam.cloud.ibm.com/identity/token',
            data={"apikey": API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'}
        )
        mltoken = token_response.json()["access_token"]
        header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}

        # Build the payload for the watsonx model
        payload_scoring = {
            "messages": [
                {"content": f"You are an AI Career Counselor. A rural youth asks: '{user_message}'", "role": "user"}
            ]
        }

        # Make the API call to your deployed watsonx model
        response_scoring = requests.post(
            f'https://eu-gb.ml.cloud.ibm.com/ml/v4/deployments/{DEPLOYMENT_ID}/ai_service_stream?version=2021-05-01',
            json=payload_scoring,
            headers=header
        )
        
        # Check if the request was successful
        response_scoring.raise_for_status()

        # Extract the model's response
        bot_response = response_scoring.json()["results"][0]["generated_text"]
    except requests.exceptions.RequestException as e:
        bot_response = f"Sorry, there was an issue connecting to the AI service: {e}"
    except (ValueError, KeyError) as e:
        bot_response = f"Sorry, there was an issue with the AI service response: {e}"

    return jsonify({'response': bot_response})

if __name__ == '__main__':
    # Use 0.0.0.0 to make the app accessible in the container
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)