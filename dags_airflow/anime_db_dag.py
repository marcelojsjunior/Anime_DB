from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'marcelo',
    'start_date': datetime(2025, 5, 25),
    'retries': 1,
}

with DAG(
    dag_id='anime_etl_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
) as dag:

    t1 = BashOperator(
        task_id='run_MyAnimeList_api_connection',
        bash_command='python C:/Users/Marcelo/Projetos/Anime_DB/API_extract_Anime_DB/MyAnimeList_api_connection.py'
    )

    t2 = BashOperator(
        task_id='run_MyAnimeList_extract_data',
        bash_command='python C:/Users/Marcelo/Projetos/Anime_DB/API_extract_Anime_DB/MyAnimeList_extract_data.py'
    )

    t3 = BashOperator(
        task_id='run_Reddit_api_extract_data',
        bash_command='python C:/Users/Marcelo/Projetos/Anime_DB/API_extract_Anime_DB/Reddit_api_extract_data.py'
    )

    t4 = BashOperator(
        task_id='run_batch_data_lake_anime_db',
        bash_command='python C:/Users/Marcelo/Projetos/Anime_DB/Batch_Anime_DB/batch_data_lake_anime_db.py'
    )


    t1 >> t2 >> t3 >> t4
