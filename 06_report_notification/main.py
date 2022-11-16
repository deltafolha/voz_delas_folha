import pandas
from data import data
from data_warehouse import fetch_data_filtered_by
from email_sender import send_emails_to_team
from chart_maker import make_chart, delete_all_charts

# ORGANIZING TEAM MEMBERS BY ROLE
team = pandas.DataFrame(data)
team_sr = team.loc[team["role"] == "SR"]
team_editors = team.loc[team["role"] == "EDITOR"]

# UNIQUE CHANNELS
unique_channels = team["channels"].apply(tuple).explode().unique()
unique_channels = [channel for channel in unique_channels if isinstance(channel, str)] # REMOVING NAN
# UNIQUE KICKERS
unique_kickers = team["kickers"].apply(tuple).explode().unique()
unique_kickers = [kicker for kicker in unique_kickers if isinstance(kicker, str)] # REMOVING NAN
# UNIQUE PRODUCTS
unique_products = team["products"].apply(tuple).explode().unique()
unique_products = [product for product in unique_products if isinstance(product, str)] # REMOVING NAN
# UNIQUE TAGS
unique_tags = team["tags"].apply(tuple).explode().unique()
unique_tags = [tag for tag in unique_tags if isinstance(tag, str)] # REMOVING NAN

all_data = fetch_data_filtered_by() # FETCH ALL DATA
data_filtered_by_channels = fetch_data_filtered_by(channels=unique_channels) # FETCH DATA FILTERING BY CHANNEL
data_filtered_by_kickers = fetch_data_filtered_by(kickers=unique_kickers) # FETCH DATA FILTERING BY KICKERS
data_filtered_by_products = fetch_data_filtered_by(products=unique_products) # FETCH FILTERING BY PRODUCTS
data_filtered_by_tags = fetch_data_filtered_by(tags=unique_tags) # FETCH DATA FILTERING BY TAGS

# CREATING THE CHARTS
make_chart(prefix="sr", data=all_data)
make_chart(prefix="editor", data=data_filtered_by_channels)
make_chart(prefix="editor", data=data_filtered_by_kickers)
make_chart(prefix="editor", data=data_filtered_by_products)
make_chart(prefix="editor", data=data_filtered_by_tags)

# SENDING THE EMAILS
send_emails_to_team(email_to=team, data={"data_team_sr": data_team_sr, "data_team_editors": data_team_editors})

# DELETING THE CHARTS AFTER SENDING THE EMAILS
delete_all_charts()