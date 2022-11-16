from datetime import datetime, timedelta
from pubsub import publish_error_message
from speaker_assignment import get_article_speakers
from speaker_database import add_speakers_to_database
from cloud_storage import cs_get_files_uploaded_today
from bigquery import organize_row_data, insert_articles_in_bigquery, update_articles_in_bigquery

if __name__ == "__main__":
    today = datetime.now().date()
    files_uploaded_today = cs_get_files_uploaded_today(today)
    articles_to_insert, articles_to_update = [], []

    for f in files_uploaded_today:
        # PRODUCT AND CHANNEL DATA ARE THE SAME FOR EVERY ARTICLE IN THE FILE
        product_id, product_name = str(f["product"]["id"]), f["product"]["name"]
        channel_id, channel_name = str(f["channel"]["id"]), f["channel"]["name"]

        # USUALLY A FILE CONTAINS MORE THAN ONE ARTICLE
        for article in f["newstexts"]:
            publication_date = datetime.strptime(article["cover_date"], "%Y-%m-%d %H:%M:%S").date()
            
            # THE APPLICATION FOCUS ON TEXTS FROM THE PREVIOUS DAYS, 
            # SINCE IT RUNS IN THE MIDDLE OF THE DAY
            if publication_date < today:
                row_data = organize_row_data(article, product_id, product_name, channel_id, channel_name)
                
                # AFTER ORGANIZING THE ARTICLE DATA, WE SEND A REQUEST TO GET THE SPEAKERS
                speaker_analysis = get_article_speakers(row_data["text"])
                if "error" in speaker_analysis["response"]:
                    row_data["total_quotes"] = -1
                    row_data["total_defined_speakers"] = -1
                    row_data["total_undefined_speakers"] = -1
                    row_data["female_speakers"] = -1
                    row_data["male_speakers"] = -1
                    row_data["undefined_gender_speakers"] = -1
                    row_data["unique_defined_speakers"] = -1
                    row_data["unique_female_speakers"] = -1
                    row_data["unique_male_speakers"] = -1
                    row_data["unique_undefined_gender_speakers"] = -1
                else:
                    row_data["quotes_and_speakers_list"] = speaker_analysis["response"]["quotes_and_speakers"]
                    row_data["unique_speakers_list"] = speaker_analysis["response"]["unique_speakers"]

                    row_data["total_quotes"] = speaker_analysis["response"]["statistics"]["total_quotes"]
                    row_data["total_defined_speakers"] = speaker_analysis["response"]["statistics"]["total_defined_speakers"]
                    row_data["total_undefined_speakers"] = speaker_analysis["response"]["statistics"]["total_undefined_speakers"]
                    row_data["female_speakers"] = speaker_analysis["response"]["statistics"]["female_speakers"]
                    row_data["male_speakers"] = speaker_analysis["response"]["statistics"]["male_speakers"]
                    row_data["undefined_gender_speakers"] = speaker_analysis["response"]["statistics"]["undefined_gender_speakers"]
                    row_data["unique_defined_speakers"] = speaker_analysis["response"]["statistics"]["unique_defined_speakers"]
                    row_data["unique_female_speakers"] = speaker_analysis["response"]["statistics"]["unique_female_speakers"]
                    row_data["unique_male_speakers"] = speaker_analysis["response"]["statistics"]["unique_male_speakers"]
                    row_data["unique_undefined_gender_speakers"] = speaker_analysis["response"]["statistics"]["unique_undefined_gender_speakers"]

                    # IF THE ARTICLE CONTAINS SPEAKERS WE SEND THEM TO THE APPLICATION RESPONSIBLE FOR THE SPEAKER DATABASE
                    if row_data["unique_female_speakers"] > 0:
                        add_speakers_to_database(row_data)

                # DEPENDING ON THE PUBLICATION DATE, WE INSERT NEW ROWS OR UPDATE OLD ONES
                if publication_date == today - timedelta(days=1):
                    articles_to_insert.append(row_data)

                elif publication_date <= today - timedelta(days=2):
                    articles_to_update.append(row_data)
       
    # INSERTING DATA FROM THE PREVIOUS DAY INTO BIGQUERY
    if len(articles_to_insert) > 0:
        result_code_insert, result_message_insert = insert_articles_in_bigquery(articles_to_insert)
        if result_code_insert == 0:
            publish_error_message("bigquery_insert")
            print(">>> BIGQUERY ERROR INSERT: {}".format(result_message_insert))

    # UPDATING DATA FROM ARTICLES ALREADY ADDED TO BIGQUERY
    if len(articles_to_update) > 0:
        result_code_update, result_message_update = update_articles_in_bigquery(articles_to_update)
        if result_code_update == 0:
            publish_error_message("bigquery_update")
            print(">>> BIGQUERY ERROR UPDATE: {}".format(result_message_update))