import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set Google API Key from environment variable
genai.configure(api_key=os.environ['GENAI_API_KEY'])

# Initialize the model and chat
model = genai.GenerativeModel('gemini-pro')

# Define the chatbot's context
CONTEXT = """You are NOVA, a proactive and adaptable customer service agent for Nexobotics. Your role is to guide users, particularly business owners, on how Nexobotics can transform their customer service by handling all customer interactions efficiently and attentively while maximizing customer satisfaction. You also act as a consultant, offering actionable insights to enhance customer satisfaction and loyalty. Adapt your communication style to match the user's tone. Respond casually if the user speaks casually (e.g., "Hey, what's up?") or professionally if they communicate formally. Always ensure clarity and relevance in your responses while minimizing unnecessary explanations unless explicitly requested. Write all responses in plain text. Never use the (*) symbol, bold, italics, or bullet points. Communicate in paragraphs, ensuring smooth flow and readability. If providing an ordered list, begin a new paragraph for each item in the list to maintain clarity and structure. Use unique and engaging opening and closing lines. Keep greetings short and dynamic (e.g., "Hi! Let's talk Nexobotics."). End conversations with motivational and engaging lines (e.g., "Looking forward to helping you elevate your customer experience!"). Stay concise, focused, and results-oriented, delivering valuable insights quickly without overwhelming the user. Maintain a friendly and approachable tone while ensuring your responses are practical and impactful."""

# Google Sheets setup
SERVICE_ACCOUNT_FILE = 'credentials.json'  # This will be set as a secret file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']

# Create Google Sheets service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    message = request.json.get('message')
    session_id = request.json.get('session_id', str(datetime.now()))  # Default session ID

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        response = model.generate_content(f"{CONTEXT}\nUser: {message}")
        bot_response = response.text

        # Log chat to Google Sheets
        log_chat_to_google_sheet(session_id, message, bot_response)

        return jsonify({'response': bot_response})
    except Exception as e:
        print(f"Error processing message: {str(e)}")  # For debugging
        return jsonify({'error': 'An error occurred processing your request'}), 500

def log_chat_to_google_sheet(session_id, user_message, bot_response):
    values = [[datetime.now().isoformat(), session_id, user_message, bot_response]]
    body = {'values': values}

    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Chats!A:E',  # Adjust the range as needed
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Render uses the PORT environment variable
    app.run(host='0.0.0.0', port=port)
