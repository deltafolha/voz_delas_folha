import os
import json
from decouple import config
from google.cloud import storage
from datetime import timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = current_dir + "/" + config("GCP_CREDENTIALS")

cloud_storage_client = storage.Client()
bucket = cloud_storage_client.get_bucket(config("CS_BUCKET_NAME"))

def cs_get_files_uploaded_today(today):
    all_files_json = []
    yesterday = today - timedelta(days=1)

    filename_prefix = config("CS_BUCKET_FOLDER") + "/" + config("CS_FILENAME_PREFIX") + str(yesterday) + "-" + str(today)
    all_blobs = list(cloud_storage_client.list_blobs(bucket, prefix=filename_prefix))
    # CHECKING THAT FILES HAVE BEEN UPLOADED TO BUCKET
    if len(all_blobs) == 0:
        return "error-no-files-in-bucket"

    for blob in all_blobs:
        if check_filename(blob.name) != "forbidden":
            file_data = json.loads(blob.download_as_string())
            file_data["filename"] = blob.name
            all_files_json.append(file_data)
    return all_files_json

def check_filename(filename):
    forbidden_files = config("FORBIDDEN_FILES").split(",")
    for ff in forbidden_files:
        if ff in filename:
            return "forbidden"
    return "ok"