import os
from decouple import config
from google.cloud import pubsub_v1

current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = current_dir + "/" + config("GCP_CREDENTIALS")

publisher = pubsub_v1.PublisherClient()

def publish_error_message(error_type):
    error_message = config("PS_ERROR_MESSAGE_" + error_type.upper())
    topic_path = publisher.topic_path(config("GCP_PROJECT_ID"), config("PS_ERROR_TOPIC_ID"))

    data = f"".encode("utf-8")
    future = publisher.publish(
        topic_path, 
        data, 
        application_name=config("APPLICATION_NAME"),
        error=error_message
    )
    return future.result()