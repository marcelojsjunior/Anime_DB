import os
import requests
from dotenv import load_dotenv, set_key
import time
import pandas as pd
from tqdm import tqdm
from google.cloud import bigquery

ENV_FILE = '.env'
load_dotenv(ENV_FILE)

CLIENT_ID = os.getenv('MAL_CLIENT_ID')
TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"


load_dotenv(dotenv_path=r"C:\Users\Marcelo\Projetos\Anime_DB\API_extract_Anime_DB\.env")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
bg_projeto = os.getenv("BIGQUERY_PROJECT_ID")

client = bigquery.Client(project=bg_projeto)

dataset_id = f"{bg_projeto}.Anime_DB"
table_id = f"{dataset_id}.animes_info_raw"

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

def flatten_anime_data(data):
    flattened = {
        'id': data.get('id'),
        'title': data.get('title'),
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date'),
        'synopsis': data.get('synopsis'),
        'mean': data.get('mean'),
        'rank': data.get('rank'),
        'popularity': data.get('popularity'),
        'num_list_users': data.get('num_list_users'),
        'num_scoring_users': data.get('num_scoring_users'),
        'status': data.get('status'),
        'num_episodes': data.get('num_episodes'),
        'source': data.get('source'),
        'average_episode_duration': data.get('average_episode_duration'),
        'rating': data.get('rating'),
        'background': data.get('background'),
        'season': data.get('start_season', {}).get('season'),
        'season_year': data.get('start_season', {}).get('year'),
        'broadcast_day': data.get('broadcast', {}).get('day_of_the_week'),
        'broadcast_time': data.get('broadcast', {}).get('start_time'),
        'main_picture_url': data.get('main_picture', {}).get('large'),

        'genres': ', '.join([g['name'] for g in data.get('genres', [])]),
        'studios': ', '.join([s['name'] for s in data.get('studios', [])]),
    }
    return flattened

## Por algum motivo a API não está funcionando corretamente com a paginação, por isso, preciso extrair anime por anime.
## Tentei fazer um paralelismo mas a API da problemas por muitas requisições, o jeito é continuar a extração um por um mesmo.

def get_anime_info(anime_ids, max_retries=3):
    token = get_valid_token()
    if not token:
        print("Não foi possível obter um token válido.")
        return pd.DataFrame()

    FIELDS = (
        "id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,"
        "popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,"
        "status,genres,num_episodes,start_season,broadcast,source,"
        "average_episode_duration,rating,pictures,background,related_anime,related_manga,"
        "recommendations,studios,statistics"
    )

    headers = {"Authorization": f"Bearer {token}"}
    data_list = []

    with tqdm(anime_ids, desc="Extraindo animes", unit="anime") as progress_bar:
        for anime_id in progress_bar:
            os.system('cls' if os.name == 'nt' else 'clear')
            progress_bar.set_postfix_str(f"ID {anime_id}")

            for attempt in range(1, max_retries + 1):
                url = f"https://api.myanimelist.net/v2/anime/{anime_id}"
                params = {"fields": FIELDS}

                response = requests.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    raw_data = response.json()
                    flattened = flatten_anime_data(raw_data)
                    data_list.append(flattened)
                    progress_bar.write(
                        f"[OK] Anime ID {anime_id} extraído com sucesso.")
                    break
                else:
                    progress_bar.write(f"[ERRO] Anime ID {anime_id}, tentativa {attempt}: {response.status_code}")
                    progress_bar.write(response.text[:100] + "...")
                    if attempt < max_retries:
                        time.sleep(1)
                    else:
                        progress_bar.write(f"Falha ao extrair Anime ID {anime_id} após {max_retries} tentativas.")

            time.sleep(1)

    return pd.DataFrame(data_list)

## Função que vai pegar o último anime com ID na base e extrair da API

def get_last_anime_id_bigquery(client, table_id):
    query = f"""
        SELECT MAX(id) as max_id
        FROM `{table_id}`
    """
    try:
        query_job = client.query(query)
        result = query_job.result()
        row = next(result)
        return int(row.max_id) if row.max_id is not None else 0
    except NotFound:
        print("Tabela não encontrada. Começando do ID 1.")
        return 0
    except Exception as e:
        print(f"Erro ao consultar BigQuery: {e}")
        return 0

ultimo_id = get_last_anime_id_bigquery(client, table_id)
print(f"Último ID encontrado: {ultimo_id}")

quantidade_novos_animes = 5000
anime_ids = list(range(ultimo_id + 1, ultimo_id + 1 + quantidade_novos_animes))
df = get_anime_info(anime_ids)
df.to_csv("animes_info.csv", index=False)

