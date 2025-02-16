import os
from flask import Flask, redirect, request, jsonify, session
from datetime import datetime
from dotenv import load_dotenv
import requests
from flask_cors import CORS
from db_operations import save_user_info, save_user_emails, get_emails
from auth.oauth2 import get_access_token, get_user_info, get_user_emails
from flask_session import Session

load_dotenv()

app = Flask(__name__)

# Use a persistent session storage instead of default cookies
app.config["SESSION_TYPE"] = "filesystem"  # Stores sessions in a temporary directory
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_FILE_DIR"] = "/tmp/flask_sessions"  # Change if needed
app.config["SESSION_COOKIE_NAME"] = "flask_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"  # Required for cross-origin requests
app.config["SESSION_COOKIE_SECURE"] = True  # Required for HTTPS
# Optional: Use Redis for better session management
# app.config["SESSION_TYPE"] = "redis"
# app.config["SESSION_REDIS"] = redis.StrictRedis(host="localhost", port=6379, db=0)
Session(app)  # Initialize Flask-Session
app.secret_key = os.getenv('FLASK_SECRET_KEY')

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
FRONTEND = os.getenv('FRONTEND')

CORS(app, origins=[FRONTEND], supports_credentials=True)

@app.route("/")
def home():
    """Redirect user to the Microsoft login page"""
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=User.Read Mail.Read"
    return redirect(auth_url)

@@ -41,11 +59,13 @@ def callback():
            return "Error: Access token not found.", 500

        session["access_token"] = access_token
        print("Stored access_token in session:", session.get("access_token"))  # Debugging

        user_info = get_user_info(access_token)
        user_id = user_info['id']
        session["user_id"] = user_id
        print("Stored user_id in session:", session.get("user_id"))  # Debugging
        save_user_info(user_info)

        user_emails = get_user_emails(access_token)
@@ -55,50 +75,44 @@ def callback():
        return redirect(redirect_url)
    except Exception as e:
        return f"Error exchanging code for token: {str(e)}", 500
@app.route('/update')
def update():
    print("🔍 Checking session data:", dict(session))  # Debugging
    access_token = session.get("access_token")
    if not access_token:
        return "Error: Access token not found.", 500
    user_id = session.get("user_id")
    if not user_id:
        return "Error: User ID not found.", 500
    user_emails = get_user_emails(access_token)
    save_user_emails(user_emails, user_id)
    try:
        result = get_emails(user_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    response = jsonify({"message": "Logged out successfully"})
    response.set_cookie('flask_session', '', expires=0)  # Ensure session cookie is cleared
    return response

@app.route('/emails', methods=['GET'])
def emails():
    try:
        user_id = request.args.get("user_id")
        print("🔍 Requesting emails for user_id:", user_id)  # Debugging
        result = get_emails(user_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True) 
