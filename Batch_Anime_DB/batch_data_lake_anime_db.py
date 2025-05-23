import os
from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

load_dotenv(dotenv_path=r"C:\Users\Marcelo\Projetos\Anime_DB\API_extract_Anime_DB\.env")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
bg_projeto = os.getenv("BIGQUERY_PROJECT_ID")

client = bigquery.Client(project=bg_projeto)

dataset_id = f"{bg_projeto}.Anime_DB"
table_id = f"{dataset_id}.animes_info_raw"

### Checando se os datasets e tabelas existem antes do batch

def dataset_exists(client, dataset_id):
    try:
        client.get_dataset(dataset_id)
        return True
    except NotFound:
        return False

def create_dataset(client, dataset_id):
    dataset = bigquery.Dataset(dataset_id)
    dataset = client.create_dataset(dataset)
    print(f"Dataset {dataset_id} criado.")

def table_exists(client, table_id):
    try:
        client.get_table(table_id)
        return True
    except NotFound:
        return False

def create_table(client, table_id):
    schema = [
        bigquery.SchemaField("id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("start_date", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("end_date", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("synopsis", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("mean", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("rank", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("popularity", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("num_list_users", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("num_scoring_users", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("num_episodes", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("average_episode_duration", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("rating", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("background", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("season", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("season_year", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("broadcast_day", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("broadcast_time", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("main_picture_url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("genres", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("studios", "STRING", mode="NULLABLE"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table)
    print(f"Tabela {table_id} criada.")

### Funções para fazer o batch dos dados

def list_files(dir_path, ext=".xlsx"):
    return [f for f in os.listdir(dir_path) if f.endswith(ext)]

def file_name_to_table_name(file_name):
    base_name = os.path.splitext(file_name)[0]
    return f"{base_name}_raw"

def load_data_from_file_to_table(client, dataset_id, table_name, file_path):
    table_id = f"{dataset_id}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        max_bad_records=500,
        ignore_unknown_values=True,
        field_delimiter=",",
        quote_character='"',
        allow_quoted_newlines=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )

    with open(file_path, "rb") as source_file:
        load_job = client.load_table_from_file(source_file, table_id, job_config=job_config)

    load_job.result()
    print(f"Dados do arquivo {file_path} carregados na tabela {table_id}")

def batch_load_from_dir(client, dataset_id, dir_path):
    files = list_files(dir_path, ext=".csv")
    for f in files:
        table_name = file_name_to_table_name(f)
        table_id = f"{dataset_id}.{table_name}"
        file_path = os.path.join(dir_path, f)

        if table_exists(client, table_id):
            load_data_from_file_to_table(client, dataset_id, table_name, file_path)
        else:
            print(f"Tabela {table_id} não existe. Pulei o arquivo {f}.")

### Verificação das tabelas e carregamento de dados

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    bg_projeto = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = f"{bg_projeto}.Anime_DB"
    diretorio = r"C:\Users\Marcelo\Projetos\Anime_DB\API_extract_Anime_DB"

    client = bigquery.Client(project=bg_projeto)


    if not dataset_exists(client, dataset_id):
        create_dataset(client, dataset_id)
    else:
        print(f"Dataset {dataset_id} já existe.")

    arquivos = list_files(diretorio, ext=".csv")

    for arquivo in arquivos:
        table_name = file_name_to_table_name(arquivo)
        table_id = f"{dataset_id}.{table_name}"
        file_path = os.path.join(diretorio, arquivo)

        if not table_exists(client, table_id):
            create_table(client, table_id)
        else:
            print(f"Tabela {table_id} já existe.")

        load_data_from_file_to_table(client, dataset_id, table_name, file_path)
