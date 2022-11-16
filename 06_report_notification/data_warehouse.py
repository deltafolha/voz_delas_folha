import os
import datetime
from decouple import config
from google.cloud import bigquery

# CONFIGURING CREDENTIALS TO WORK WITH BQ
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = current_dir + "/" + config("GCP_CREDENTIALS")

# CREATING CLIENT AND OBTAINING TABLE ID
bigquery_client = bigquery.Client()
bigquery_table_path = config("GCP_PROJECT_ID") + "." + config("BQ_DATASET_ID") + "." + config("BQ_TABLE_ID")

queries = config("QUERIES").split(",")

def fetch_data_filtered_by(initial_date=None, end_date=None, channels=None, kickers=None, products=None, tags=None):
    yesterday = datetime.datetime.now().date() - datetime.timedelta(days=11)

    initial_date = yesterday if initial_date == None else initial_date
    end_date = yesterday if end_date == None else end_date

    # NO FILTERS
    if channels == None and kickers == None and products == None and tags == None:
        data = {}

        for index, query_title in enumerate(queries):
            query = handle_query_text(query_title=query_title, initial_date=initial_date, end_date=end_date)
            query_result = bigquery_client.query(query).to_dataframe().melt(var_name="category", value_name="value")
            data[query_title] = query_result
            
            # THE FIRST QUERY WILL TELL IF THERE ARE TEXTS OR NOT
            if index == 0:
                if check_empty_data(data[query_title]):
                    break
        return data

    # CHANNELS
    if channels != None:
        data = {}

        for channel in channels:
            data[channel] = handle_query(initial_date=initial_date, end_date=end_date, channel=channel)
        return data
    
    # KICKERS
    if kickers != None:
        data = {}

        for kicker in kickers:
            data[kicker] = handle_query(initial_date=initial_date, end_date=end_date, kicker=kicker)
        return data
    
    # PRODUCTS
    if products != None:
        data = {}

        for product in products:
            data[product] = handle_query(initial_date=initial_date, end_date=end_date, product=product)
        return data

    # TAGS
    if tags != None:
        data = {}

        for tag in tags:
            data[tag] = handle_query(initial_date=initial_date, end_date=end_date, tag=tag)
        return data


def handle_query(initial_date=None, end_date=None, channel=None, kicker=None, product=None, tag=None):
    data = {}

    for index, query_title in enumerate(queries):
        query = handle_query_text(query_title=query_title, initial_date=initial_date, end_date=end_date, channel=channel, kicker=kicker, product=product, tag=tag)
        query_result = bigquery_client.query(query).to_dataframe().melt(var_name="category", value_name="value")
        data[query_title] = query_result

        # THE FIRST QUERY WILL TELL IF THERE ARE TEXTS OR NOT
        if index == 0:
            if check_empty_data(data[query_title]):
                break
    return data


def handle_query_text(query_title=None, initial_date=None, end_date=None, channel=None, kicker=None, product=None, tag=None):
    # NO FILTERS
    if channel == None and kicker == None and product == None and tag == None:
        return (config("QUERY_" + query_title).format("", initial_date, end_date, ""))
    if channel != None:
        return (config("QUERY_" + query_title).format("", initial_date, end_date, "AND channel.name = '{}' ".format(channel)))
    if product != None:
        return (config("QUERY_" + query_title).format("", initial_date, end_date, "AND product.name = '{}' ".format(product)))
    if kicker != None:
        return (config("QUERY_" + query_title).format(", UNNEST(kickers) as kicker", initial_date, end_date, "AND kicker.name = '{}' ".format(kicker)))
    if tag != None:
        return (config("QUERY_" + query_title).format(", UNNEST(tags) as tag", initial_date, end_date, "AND tag.name = '{}' ".format(tag)))


def check_empty_data(data):
    # CHECKING IF ALL VALUES FROM FILTER "TEXTS" ARE ZERO
    return (data["value"] == 0).all()