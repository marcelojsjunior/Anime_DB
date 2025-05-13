import secrets
import string
import requests
from flask import Flask, redirect, request, session, jsonify
from dotenv import set_key, get_key, dotenv_values, load_dotenv
from pathlib import Path
from datetime import datetime, timedelta
import time
import os

ENV_FILE = '.env'
load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

CLIENT_ID = os.getenv('MAL_CLIENT_ID')
REDIRECT_URI = os.getenv('REDIRECT_URI')
TOKEN_EXPIRATION_BUFFER = 300


def generate_code_verifier(length=128):
    chars = string.ascii_letters + string.digits + "-._~"
    return ''.join(secrets.choice(chars) for _ in range(length))


def load_tokens():
    env = dotenv_values(ENV_FILE)
    return {
        'access_token': env.get('MAL_ACCESS_TOKEN'),
        'refresh_token': env.get('MAL_REFRESH_TOKEN'),
        'expires_at': float(env.get('MAL_EXPIRES_AT', 0))
    }


def save_tokens(access_token, refresh_token, expires_in):
    expires_at = time.time() + expires_in
    set_key(ENV_FILE, 'MAL_ACCESS_TOKEN', access_token)
    set_key(ENV_FILE, 'MAL_REFRESH_TOKEN', refresh_token)
    set_key(ENV_FILE, 'MAL_EXPIRES_AT', str(expires_at))


def is_token_expired():
    tokens = load_tokens()
    if not tokens['access_token']:
        return True
    return time.time() > (tokens['expires_at'] - TOKEN_EXPIRATION_BUFFER)


def refresh_access_token():
    tokens = load_tokens()
    if not tokens['refresh_token']:
        return None

    token_url = "https://myanimelist.net/v1/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": tokens['refresh_token'],
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return None

    new_tokens = response.json()
    access_token = new_tokens["access_token"]
    refresh_token = new_tokens.get("refresh_token", tokens['refresh_token'])
    expires_in = new_tokens.get("expires_in", 2592000)  # Padrão de 30 dias se não informado

    save_tokens(access_token, refresh_token, expires_in)
    return access_token


def get_valid_token():
    if not is_token_expired():
        tokens = load_tokens()
        return tokens['access_token']

    return refresh_access_token()


@app.route('/login')
def login():
    code_verifier = generate_code_verifier()
    session['code_verifier'] = code_verifier

    auth_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "state": secrets.token_urlsafe(16),
        "redirect_uri": REDIRECT_URI,
        "code_challenge": code_verifier,
        "code_challenge_method": "plain",
    }

    auth_url = "https://myanimelist.net/v1/oauth2/authorize?" + "&".join(
        f"{k}={v}" for k, v in auth_params.items()
    )
    return redirect(auth_url)


@app.route('/callback')
def callback():
    if 'error' in request.args:
        return f"Erro: {request.args.get('error')}", 400

    code = request.args.get('code')
    state = request.args.get('state')

    token_url = "https://myanimelist.net/v1/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": session['code_verifier'],
    }

    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        return f"Erro ao obter token: {response.text}", 400

    tokens = response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    expires_in = tokens.get("expires_in", 2592000)  # 30 dias padrão se não informado

    save_tokens(access_token, refresh_token, expires_in)

    return f"""
    <h1>Autenticado com sucesso!</h1>
    <p>Access Token salvo em {ENV_FILE}</p>
    <p>Refresh Token salvo em {ENV_FILE}</p>
    <p>Expira em: {datetime.fromtimestamp(time.time() + expires_in).strftime('%Y-%m-%d %H:%M:%S')}</p>
    """


@app.route('/test-api')
def test_api():
    access_token = get_valid_token()
    if not access_token:
        return redirect('/login')

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.myanimelist.net/v2/users/@me', headers=headers)

    if response.status_code == 401:  # Token expirado mesmo após renovação
        return redirect('/login')

    return jsonify(response.json())


if __name__ == '__main__':
    if not Path(ENV_FILE).exists():
        with open(ENV_FILE, 'w') as f:
            pass
    app.run(port=8000, debug=True)