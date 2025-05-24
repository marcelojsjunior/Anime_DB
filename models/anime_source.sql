{{ config(materialized='ephemeral') }}

select * from `BG_projeto.Anime_DB.animes_info_raw`
