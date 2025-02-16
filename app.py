import os
from flask import Flask, redirect, request, jsonify, session 
from datetime import datetime
from dotenv import load_dotenv
import requests
from flask_cors import CORS 
from flask_session import Session
import redis
from db_operations import save_user_info, save_user_emails, get_emails
from auth.oauth2 import get_access_token, get_user_info, get_user_emails  

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
FRONTEND = os.getenv('FRONTEND')
CORS(app, origins=[f"{FRONTEND}"], supports_credentials=True)

# Configure Flask-Session with Redis
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_KEY_PREFIX"] = "flask-session:"
app.config["SESSION_REDIS"] = redis.StrictRedis(host='your-redis-host', port=6379, db=0, decode_responses=True)
app.config["SESSION_COOKIE_SECURE"] = True  # Ensures cookies are only sent over HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevents JavaScript from accessing session cookies
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

Session(app)

@app.route("/")
def home():
    """Home route, redirect user to the Microsoft login page"""
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=User.Read Mail.Read"
    return redirect(auth_url)

@app.route("/auth/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: Authorization code not found.", 400

    try:
        tokens = get_access_token(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, code)
        if tokens is None:
            return "Error: Failed to exchange code for access token.", 500

        access_token = tokens.get("access_token")
        if not access_token:
            return "Error: Access token not found.", 500

        session["access_token"] = access_token
        
        user_info = get_user_info(access_token)
        user_id = user_info['id']
        session["user_id"] = user_id
        save_user_info(user_info)

        user_emails = get_user_emails(access_token)
        save_user_emails(user_emails, user_id)

        redirect_url = f"{FRONTEND}/dashboard?user_id={user_id}&email={user_info['mail']}"
        return redirect(redirect_url)
    except Exception as e:
        return f"Error exchanging code for token: {str(e)}", 500
    
@app.route('/update')
def update():
    print(session)  # Debugging statement
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
    response.set_cookie('session', '', expires=0)
    return response

@app.route('/emails', methods=['GET'])
def emails():
    try:
        user_id = request.args.get("user_id")
        print(user_id)
        result = get_emails(user_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
