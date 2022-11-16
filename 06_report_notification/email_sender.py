import base64
import datetime
import dominate
from dominate.tags import *
from decouple import config
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from data_warehouse import check_empty_data

def send_emails_to_team(email_to=None, data=None):
    for index, team_member in email_to.iterrows():
        # ALL DATA
        if team_member["role"] == "SR":
            if not check_empty_data(data["data_team_sr"]):
                send_email_to_team_member(email=team_member["email"], file_prefix="sr")

        # DATA FILTERED BY CHANNEL
        if team_member["role"] == "SR" or team_member["role"] == "EDITOR":
            for channel in team_member["channels"]:
                if not check_empty_data(data["data_team_editors"][channel]):
                    send_email_to_team_member(email=team_member["email"], file_prefix="editor", channel=channel)


def send_email_to_team_member(email=None, file_prefix=None, channel=None, author=None):
    email = Mail(from_email=config("EMAIL_FROM"), to_emails=email, subject=handle_title(channel, author), html_content=handle_content(file_prefix, channel, author))

    try:
        sendgrid_client = SendGridAPIClient(config('SENDGRID_API_KEY'))
        response = sendgrid_client.send(email)
        
    except Exception as error:
        print("::: ERROR > {}".format(error.message))


def handle_title(channel=None, author=None):
    yesterday = str(datetime.datetime.now().date() - datetime.timedelta(days=1)).split("-")
    yesterday_modified = yesterday[2] + "/" + yesterday[1] + "/" + yesterday[0]

    if channel == None and author == None:
        return "Voz Delas > Relatório do dia {}".format(yesterday_modified)
    if channel != None:
        return "Voz Delas > Relatório da editoria {}, dia {}".format(channel, yesterday_modified)
    if author != None:
        return "Voz Delas > Relatório de {}, dia {}".format(author, yesterday_modified)


def handle_content(file_prefix=None, channel=None, author=None):
    directory = "support_files/charts/"
    doc = dominate.document()
    with doc:
        with div():
            query_types = [config("INITIAL_QUERY")] + config("SUBSEQUENT_QUERIES").split(",")
            for query_type in query_types:
                fig_box = div()
                if file_prefix == "sr":
                    fig = open(directory + file_prefix + "_" + query_type.lower() + ".png", 'rb').read()
                if file_prefix == "editor":
                    fig = open(directory + file_prefix + "_" + channel.lower().replace(" ", "") + "_" + query_type.lower() + ".png", 'rb').read()
                
                fig_data_base64 = base64.b64encode(fig).decode()  # ENCODE TO BASE64 (BYTES) AND THEN CONVERT BYTES TO STRINGencode to base64 (bytes)
                fig_box.add(img(src="data:image/png;base64,{}".format(fig_data_base64)))
    return str(doc)