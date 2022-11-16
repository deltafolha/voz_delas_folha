import os
from decouple import config
from google.cloud import firestore

# CONFIGURING CREDENTIALS TO WORK WITH FIRESTORE
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = current_dir + "/" + config("GCP_CREDENTIALS")

db = firestore.Client(project=config("GCP_PROJECT_ID"))

def get_speaker(speaker):
    docs = db.collection(config("FS_SPEAKERS_COLLECTION")).where('speaker', '==', speaker).get()
    return docs


def add_new_speaker(speaker_name, data, now):
    db.collection(config("FS_SPEAKERS_COLLECTION")).document().set({
        "speaker" : speaker_name,
        "articles" : [{ "id" : data["id"], "title" : data["title"], "publication_datetime" : data["publication_datetime"], "url" : data["url"] }],
        "channels" : [data["channel"]], # ATTENTION: THE KEY BECOMES "CHANNELS"
        "topics" : data["topics"],
        "tags" : data["tags"],
        "update_history" : [now]
    })


def update_speaker(speaker_data, new_data, now):
    # COPYING THE CURRENT SPEAKER DATA TO BE UPDATED WITH THE NEW ONES
    data_to_update = speaker_data.to_dict()

    article_data = {"id" : new_data["id"], "title" : new_data["title"], "publication_datetime" : new_data["publication_datetime"], "url" : new_data["url"] }
    if article_data not in data_to_update["articles"]:
        data_to_update["articles"].append(article_data)

    if new_data["channel"] not in data_to_update["channels"]:
        data_to_update["channels"].append(new_data["channel"])

    for topic in new_data["topics"]:
        if topic not in data_to_update["topics"]:
            data_to_update["topics"].append(topic)
    
    for tag in new_data["tags"]:
        if tag not in data_to_update["tags"]:
            data_to_update["tags"].append(tag)
 
    data_to_update["update_history"].append(now)

    speaker_data.reference.update(data_to_update)


def insert_channel_tags_topics(channel, tags, topics):
    db.collection(config("FS_CHANNELS_COLLECTION")).document(channel.replace("/", "|")).set({"name":channel}, merge=True)
    for tag in tags:
        db.collection(config("FS_TAGS_COLLECTION")).document(tag.replace("/", "|")).set({"name":tag}, merge=True)
    for topic in topics:
        db.collection(config("FS_TOPICS_COLLECTION")).document(topic.replace("/", "|")).set({"name":topic}, merge=True)