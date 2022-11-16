import os
from decouple import config
from google.cloud import firestore

# CONFIGURING CREDENTIALS TO WORK WITH FIRESTORE
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = current_dir + "/" + config("GCP_CREDENTIALS")

db = firestore.Client(project=config("GCP_PROJECT_ID"))

def check_search_input(search_input):
    search_input_upper = search_input.upper()
    keywords = [kw[1:] if kw[0] == " " else kw for kw in search_input_upper.split(",")]
    return len(keywords), keywords

def get_speakers(keywords, search_for_tags, search_for_topics):
    if search_for_tags == "tags_checked" and search_for_topics == "topics_checked":
        docs_tags = db.collection(config("FS_SPEAKERS_COLLECTION")).where("tags", "array_contains_any", keywords).get()
        docs_topics = db.collection(config("FS_SPEAKERS_COLLECTION")).where("topics", "array_contains_any", keywords).get()
        docs = set(docs_tags + docs_topics)
    elif search_for_tags == "tags_checked" and search_for_topics == None:
        docs = db.collection(config("FS_SPEAKERS_COLLECTION")).where("tags", "array_contains_any", keywords).get()
    elif search_for_tags == None and search_for_topics == "topics_checked":
        docs = db.collection(config("FS_SPEAKERS_COLLECTION")).where("topics", "array_contains_any", keywords).get()
    return docs