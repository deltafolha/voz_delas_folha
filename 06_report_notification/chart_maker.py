import os
import plotly.express as px
from data_warehouse import check_empty_data

directory = "support_files/charts/"

def make_chart(prefix=None, data=None):
    if prefix == "sr":
        # IF THERE WERE NO TEXTS THAT DAY,
        # THERE IS NO POINT IN CREATING THE CHARTS
        if len(data.keys()) > 1:
            for query_title, result in data.items():
                fig = px.bar(result, x="category", y="value")
                fig.write_image(directory + prefix + "_" + query_title.lower() + ".png")
            
    if prefix == "editor":
        for filter_name, queries_list in data.items():
            # IF THERE WERE NO TEXTS FROM THE CHOSEN FILTER THAT DAY,
            # THERE IS NO POINT IN CREATING THE CHART
            if len(queries_list.keys()) > 1:
                for query_title, result in queries_list.items():
                    fig = px.bar(result, x="category", y="value")
                    fig.write_image(directory + prefix + "_" + filter_name.lower().replace(" ", "") + "_" + query_title.lower() + ".png")


def delete_all_charts():
    files = os.listdir(directory)
    for f in files:
        os.remove(directory + f)