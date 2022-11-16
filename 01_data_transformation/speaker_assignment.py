import requests
from decouple import config

def get_article_speakers(article_text):
    auth_token = config("SA_AUTH_TOKEN")
    header = {"Authorization": "Bearer " + auth_token}
    data = {"article_text" : article_text}

    url = config("SA_API_URL")
    response = requests.post(url, json=data, headers=header)
    return response.json()