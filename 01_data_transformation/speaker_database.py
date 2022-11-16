import requests
from decouple import config

def add_speakers_to_database(article_data):
    auth_token = config("SD_AUTH_TOKEN")
    header = {"Authorization": "Bearer " + auth_token}
    data = {
        "id" : article_data["id"],
        "publication_datetime" : article_data["publication_datetime"],
        "title" : article_data["title"],
        "url" : article_data["url"],
        "channel" : article_data["channel"]["name"].upper(),
        "topics" : [topic["name"].upper() for topic in article_data["topics"]],
        "tags" : [tag["name"].upper() for tag in article_data["tags"]],
        "speakers" : article_data["unique_speakers_list"]
    }

    url = config("SD_API_URL")
    response = requests.post(url, json=data, headers=header)
    return response.json()