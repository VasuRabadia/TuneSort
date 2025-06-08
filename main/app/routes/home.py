from flask import Blueprint, request, session, jsonify, render_template
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import os

load_dotenv()

home_bp = Blueprint("home", __name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


@home_bp.route("/home")
def callback():
    code = request.args.get("code")

    # Exchange code for access token
    token_response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        return (
            jsonify(
                {
                    "error": "Failed to get access token",
                    "status_code": token_response.status_code,
                    "spotify_response": token_response.json(),
                }
            ),
            400,
        )

    tokens = token_response.json()

    # Store access token in session
    session["access_token"] = tokens.get("access_token")

    return render_template(
        "home.html",
        access_token=session["access_token"],
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        token_type=tokens.get("token_type"),
        expires_in=tokens.get("expires_in"),
        scope=tokens.get("scope"),
        refresh_token=tokens.get("refresh_token"),
    )
