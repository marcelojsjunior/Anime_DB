import os
import requests
from dotenv import load_dotenv, set_key

ENV_FILE = '.env'
load_dotenv(ENV_FILE)

CLIENT_ID = os.getenv('MAL_CLIENT_ID')
TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"


def get_valid_token():
    access_token = os.getenv('MAL_ACCESS_TOKEN')

    if not access_token:
        print("Access token não encontrado. Tentando renovar...")
        return refresh_access_token()

    test_response = requests.get(
        "https://api.myanimelist.net/v2/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if test_response.status_code != 401:
        return access_token

    print("Token expirado ou inválido. Tentando renovar...")
    new_token = refresh_access_token()

    if new_token:
        return new_token

    print("Não foi possível obter um token válido.")
    return None


def refresh_access_token():
    refresh_token = os.getenv('MAL_REFRESH_TOKEN')
    if not refresh_token:
        print("Refresh token não encontrado. É necessário autenticar novamente.")
        return None

    data = {
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        print(f"Erro ao renovar token: {response.text}")
        return None

    new_tokens = response.json()

    set_key(ENV_FILE, 'MAL_ACCESS_TOKEN', new_tokens['access_token'])
    if 'refresh_token' in new_tokens:
        set_key(ENV_FILE, 'MAL_REFRESH_TOKEN', new_tokens['refresh_token'])

    print("Token renovado com sucesso!")
    return new_tokens['access_token']


def get_anime_info(anime_id):
    token = get_valid_token()
    if not token:
        print("Não foi possível obter um token válido.")
        return None

    FIELDS = (
        'id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,'
        'popularity,num_list_users,num_scoring_users,status,genres,'
        'num_episodes,start_season,broadcast,source,average_episode_duration,rating,'
        'pictures,background,related_anime,related_manga,recommendations,studios,statistics'
    )

    url = f"https://api.myanimelist.net/v2/anime/{anime_id}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"fields": FIELDS}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao buscar anime ID {anime_id}: {response.status_code}")
        print(response.text)
        return None


if __name__ == "__main__":
    anime_id = 1
    anime_info = get_anime_info(anime_id)

    if anime_info:
        print("Informações do Anime:")
        for key, value in anime_info.items():
            print(f"{key}: {value}")