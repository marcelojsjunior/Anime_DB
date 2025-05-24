{{ config(
    materialized='table',
    alias='animes_info_bronze'
) }}

with raw_data as (
    select * from {{ ref('anime_source') }}
),

removendo_duplicados as (
    select *,
           row_number() over (partition by id order by id) as rn
    from raw_data
),

tipado as (
    select
        SAFE_CAST(id AS INT64) as id,
        title,
        PARSE_DATE('%Y-%m-%d',
            case
                when REGEXP_CONTAINS(start_date, r'^\d{4}-\d{2}-\d{2}$') then start_date
                when REGEXP_CONTAINS(start_date, r'^\d{4}$') then CONCAT(start_date, '-01-01')
                else null
            end
        ) as start_date,
        PARSE_DATE('%Y-%m-%d',
            case
                when REGEXP_CONTAINS(end_date, r'^\d{4}-\d{2}-\d{2}$') then end_date
                when REGEXP_CONTAINS(end_date, r'^\d{4}$') then CONCAT(end_date, '-01-01')
                else null
            end
        ) as end_date,
        synopsis,
        SAFE_CAST(mean AS FLOAT64) as mean,
        SAFE_CAST(rank AS INT64) as rank,
        SAFE_CAST(popularity AS INT64) as popularity,
        SAFE_CAST(num_list_users AS INT64) as num_list_users,
        SAFE_CAST(num_scoring_users AS INT64) as num_scoring_users,
        status,
        SAFE_CAST(num_episodes AS INT64) as num_episodes,
        source,
        SAFE_CAST(average_episode_duration AS INT64) as average_episode_duration,
        rating,
        background,
        season,
        SAFE_CAST(season_year AS INT64) as season_year,
        broadcast_day,
        broadcast_time,
        main_picture_url,
        genres,
        studios
    from removendo_duplicados
    where rn = 1
)
select * from tipado

