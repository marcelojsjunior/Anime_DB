import praw
from google.cloud import bigquery
from dotenv import load_dotenv
import os
import pandas as pd
import time

load_dotenv(dotenv_path=r"C:\Users\Marcelo\Projetos\Anime_DB\API_extract_Anime_DB\.env")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

bg_projeto = os.getenv("BIGQUERY_PROJECT_ID")
client = bigquery.Client(project=bg_projeto)

dataset_id = f"{bg_projeto}.Anime_DB"
table_id = f"{dataset_id}.animes_info_bronze"

reddit = praw.Reddit(
    client_id="xywdoBzPDWv7qrGhCcDsuA",
    client_secret="A2Y1BltgvL2i9IOQBaSXdBWHZqcwcw",
    user_agent="Base de Animes by marcelojsjunior"
)

def get_top_500_animes(client, table_id):
    query = f"""
        SELECT id, title, popularity
        FROM `{table_id}`
        ORDER BY popularity ASC
        LIMIT 500
    """
    query_job = client.query(query)
    results = query_job.result()

    animes = []
    for row in results:
        animes.append({
            "id": row.id,
            "title": row.title,
            "popularity": row.popularity
        })
    return animes


def get_top_posts_for_animes(reddit, anime_list, limit=10):
    all_posts = {}
    for idx, anime in enumerate(anime_list):
        title = anime["title"]
        anime_id = anime["id"]
        print(f"[{idx + 1}/{len(anime_list)}] Buscando posts para: {title} (ID: {anime_id})")

        search_query = f"{title} anime"
        posts = []
        try:
            search_results = list(reddit.subreddit("anime").search(
                search_query,
                sort="top",
                limit=limit,
                time_filter="all"
            ))

            all_posts[title] = {
                "anime_id": anime_id,
                "posts": search_results
            }
        except Exception as e:
            print(f"ERRO buscando posts para {title}: {str(e)}")
            all_posts[title] = {
                "anime_id": anime_id,
                "posts": []
            }
        time.sleep(1)
    return all_posts

def extract_comments_from_post(post, anime_title):
    try:
        print(f"Iniciando extração de comentários do post {post.id} ({post.title[:30]}...) para o anime '{anime_title}'")
        post.comments.replace_more(limit=0)
        comments_data = []

        comment_list = post.comments.list()
        total_comments = len(comment_list)
        erros_comment = 0

        for comment in comment_list:
            try:
                comments_data.append({
                    "anime_title": anime_title,
                    "post_id": post.id,
                    "comment_id": comment.id,
                    "comment_author": comment.author.name if comment.author else None,
                    "comment_body": comment.body,
                    "comment_score": comment.score,
                    "comment_created_utc": comment.created_utc,
                    "comment_parent_id": comment.parent_id,
                    "comment_depth": comment.depth
                })
            except Exception as e:
                erros_comment += 1
                print(f"[ERRO] Falha ao processar comentário {comment.id} do post {post.id}: {e}")

        print(f"Extraídos {total_comments - erros_comment} comentários do post {post.id} (ignorados {erros_comment} com erro)")
        return comments_data

    except Exception as e:
        print(f"[ERRO] Falha ao extrair comentários do post {post.id}: {e}")
        return []


if __name__ == "__main__":
    top_500_animes = get_top_500_animes(client, table_id)
    print(f"Total de animes carregados: {len(top_500_animes)}")
    top_posts = get_top_posts_for_animes(reddit, top_500_animes, limit=10)

    # Verificação ajustada
    print("\nVerificação dos posts coletados:")
    for anime_title, data in top_posts.items():
        print(f"\nAnime: {anime_title} (ID: {data['anime_id']})")
        print(f"Total posts: {len(data['posts'])}")
        for post in data['posts']:
            print(f"- {post.title[:60]}... (ID: {post.id}, Score: {post.score})")

    post_data = []
    comments_data = []

    for anime_title, data in top_posts.items():
        anime_id = data['anime_id']
        for post in data['posts']:
            post_data.append({
                "anime_id": anime_id,
                "anime_title": anime_title,
                "post_id": post.id,
                "post_title": post.title,
                "score": post.score,
                "url": post.url,
                "created_utc": post.created_utc,
                "num_comments": post.num_comments,
                "author": post.author.name if post.author else None,
                "subreddit": post.subreddit.display_name,
                "upvote_ratio": post.upvote_ratio,
                "over_18": post.over_18,
                "spoiler": post.spoiler,
                "is_original_content": post.is_original_content,
                "flair": post.link_flair_text,
                "total_awards_received": post.total_awards_received,
                "selftext": post.selftext
            })

            comments = extract_comments_from_post(post, anime_title)
            for comment in comments:
                comment['anime_id'] = anime_id  # Adicionando ID aos comentários
            comments_data.extend(comments)

    df_posts = pd.DataFrame(post_data)
    df_comments = pd.DataFrame(comments_data)


    df_posts = df_posts[
        ['anime_id', 'anime_title'] + [col for col in df_posts.columns if col not in ['anime_id', 'anime_title']]]

    df_posts.to_csv("forum_info.csv", index=False)
    df_comments.to_csv("comments_info.csv", index=False)

    print("\nResumo final:")
    print(f"- Total de posts salvos: {len(df_posts)}")
    print(f"- Total de comentários salvos: {len(df_comments)}")
    print(f"- Animes com posts encontrados: {df_posts['anime_id'].nunique()}")


