import os
from decouple import config
from datetime import datetime
from google.cloud import bigquery
from text_transformation import clear_text_data

# CONFIGURING CREDENTIALS TO WORK WITH BQ
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = current_dir + "/" + config("GCP_CREDENTIALS")

# CREATING CLIENT AND OBTAINING TABLE ID
bigquery_client = bigquery.Client()
bigquery_table_path = config("GCP_PROJECT_ID") + "." + config("BQ_DATASET_ID") + "." + config("BQ_TABLE_ID")

current_datetime = str(datetime.now().replace(microsecond=0))

# ORGANIZES DATA BEFORE SENDING IT TO GOOGLE BIG QUERY
def organize_row_data(article, product_id, product_name, channel_id, channel_name):
    # TITLES, SUBTITLES AND TEXT COME WITH HTML TAGS, NEW LINE CHARACTERS AND CARRIAGE RETURN CHARACTERS
    article_title = clear_text_data(article["title"])
    article_subtitle = clear_text_data(article["subtitle"])
    article_text = clear_text_data(article["body"])

    new_row = {
        "id"                               : str(article["articleId"]),
        "publication_datetime"             : article["cover_date"],
        "page_type"                        : article["pageType"],
        "article_type"                     : article["articleType"],
        "product"                          : {"id" : product_id, "name" : product_name},
        "channel"                          : {"id" : channel_id, "name" : channel_name},
        "url"                              : article["url"],
        "title"                            : article_title,
        "subtitle"                         : article_subtitle,
        "text"                             : article_text,
        "authors"                          : [],
        "kickers"                          : [],
        "topics"                           : [],
        "tags"                             : [],
        "quotes_and_speakers_list"         : [],
        "unique_speakers_list"             : [],
        "total_quotes"                     : 0,
        "total_defined_speakers"           : 0,
        "total_undefined_speakers"         : 0,
        "female_speakers"                  : 0,
        "male_speakers"                    : 0,
        "undefined_gender_speakers"        : 0,
        "unique_defined_speakers"          : 0,
        "unique_female_speakers"           : 0,
        "unique_male_speakers"             : 0,
        "unique_undefined_gender_speakers" : 0,
        "update_history"                   : [current_datetime]
    }

    # AUTHORS
    for author in article["authors"]:
        new_row["authors"].append({"id" : str(author["id"]), "name" : author["name"]})
    
    # KICKERS
    # SOMETIMES KICKERS COME WITHOUT URL, SOMETIMES WITH THE "ATTENTION" KEY
    for kicker in article["kickers"]:
        kicker_data = {"name" : kicker["name"]}
        if "link_url" in kicker:
            kicker_data["url"] = kicker["link_url"]
        else:
            kicker_data["url"] = None

        if "attention" in kicker:
            kicker_data["attention"] = kicker["attention"]
        else:
            kicker_data["attention"] = None

        new_row["kickers"].append(kicker_data)
    
    # TOPICS
    # SOMETIMES TOPICS COME AS LISTS, SOMETIMES AS DICTS
    if type(article["topics"]) is list:
        for topic in article["topics"]:
            new_row["topics"].append({"id" : str(topic["id"]), "name" : topic["name"]})
    elif type(article["topics"]) is dict:
        topic_keys = article["topics"].keys()
        for topic_key in topic_keys:
            topic = article["topics"][topic_key]
            new_row["topics"].append({"id" : str(topic["id"]), "name" : topic["name"]})

    # TAGS
    # SOMETIMES TAGS COME AS LISTS, SOMETIMES AS DICTS
    if type(article["tags"]) is list:
        for tag in article["tags"]:
            new_row["tags"].append({"id" : str(tag["id"]), "name" : tag["name"]})        
    elif type(article["tags"]) is dict:
        tag_keys = article["tags"].keys()
        for tag_key in tag_keys:
            tag = article["tags"][tag_key]
            new_row["tags"].append({"id" : str(tag["id"]), "name" : tag["name"]})

    return new_row


def insert_articles_in_bigquery(articles_to_insert):
    errors = bigquery_client.insert_rows_json(bigquery_table_path, articles_to_insert)

    # CHECKING IF THE LIST OF ERRORS IS EMPTY
    if not errors:
        return 1, "success"
    else:
        return 0, errors


def update_articles_in_bigquery(articles):
    articles_to_update = []
    for article in articles:
        id = article["id"]

        # CHECKING IF THE ARTICLE HAS BEEN ADDED TO THE WAREHOUSE
        read_result = bigquery_client.query('SELECT * FROM `{}` WHERE id="{}";'.format(bigquery_table_path, id)).result()
        
        if read_result.total_rows == 1:
            for row in read_result:
                # GET THE UPDATE HISTORY
                update_history = [update.strftime('%Y-%m-%d %H:%M:%S') for update in row["update_history"]]
                # ADD THE CURRENT DATETIME TO REGISTER THE NEW UPDATE
                current_datetime = article["update_history"]
                article["update_history"] = update_history + current_datetime

        # IN CASE THE ARTICLE IS NOT IN THE WAREHOUSE, WE ADD IT AS WELL
        articles_to_update.append(article)

        # DELETING THE OLD DATA FROM THE TABLE
        delete_result = bigquery_client.query('DELETE FROM `{}` WHERE id="{}";'.format(bigquery_table_path, id)).result()
    
    # INSERTING THE UPDATED DATA
    return insert_articles_in_bigquery(articles_to_update)