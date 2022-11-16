from decouple import config
from datetime import datetime
from flask import Flask, request
from flask_httpauth import HTTPTokenAuth
from pubsub import publish_error_message
from database import get_speaker, add_new_speaker, update_speaker, insert_channel_tags_topics

app = Flask(__name__)
auth = HTTPTokenAuth(scheme="Bearer")

system_token = config("SYSTEM_TOKEN")

@auth.verify_token
def verify_token(token):
    if token == system_token:
        return True

@app.route('/add_speakers_to_database', methods=["POST"])
@auth.login_required
def add_speakers_to_database():
    data = request.json
    speakers = data["speakers"]
    now = str(datetime.now().replace(microsecond=0))
    first = True

    for speaker in speakers:
        if speaker["gender"] == "F":
            if first:
                insert_channel_tags_topics(data["channel"], data["tags"], data["topics"])
                first = False
                
            # CHECK IF THE SPEAKER HAS BEEN STORED IN THE DB PREVIOUSLY
            result = get_speaker(speaker["speaker"])

            # IF THERE IS NO RECORD OF THE SPEAKER IN THE DB, WE ADD IT
            if len(result) == 0:
                add_new_speaker(speaker["speaker"], data, now)

            # IF THERE IS ONE RECORD OF THE SPEAKER IN THE DB, WE UPDATE IT WITH NEW DATA
            elif len(result) == 1:
                update_speaker(result[0], data, now)

            # ERROR
            elif len(result) > 1:
                publish_error_message("firestore", speaker["speaker"], data["id"])
    
    return {"response" : "ok"}, 200
    
if __name__ == "__main__":
    app.run(debug=True, port=config("SERVER_PORT"), host="0.0.0.0")