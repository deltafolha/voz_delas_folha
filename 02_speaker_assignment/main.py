import os
import json
from decouple import config
from flask import Flask, request
from flask_httpauth import HTTPTokenAuth
from text_analysis import check_quotation_marks, check_zero_quotation_marks
from speaker_assignment import identify_speakers

app = Flask(__name__)
auth = HTTPTokenAuth(scheme="Bearer")
system_token = config("SYSTEM_TOKEN")

@auth.verify_token
def verify_token(token):
    if token == system_token:
        return True

@app.route('/get_article_speakers', methods=["POST"])
@auth.login_required
def get_article_speakers():
    article_data = request.json
    # CHECKING IF THE REQUEST COMES WITH A TEXT
    if "article_text" not in article_data:
        return json.dumps({"response" : "error-01"}), 400, {'ContentType':'application/json'}

    article_text = article_data["article_text"]
    id_text = article_data["id_text"]
  
    # CHECKING IF THE TEXT HAS AN EVEN AMOUNT OF QUOTATION MARKS
    if check_quotation_marks(article_text):

        if check_zero_quotation_marks(article_text):
            return json.dumps({"response" : {
            "quotes_and_speakers" : None,
            "unique_speakers" : None,
            "statistics" : {
                            "total_quotes": 0,
                            "total_defined_speakers": 0,
                            "total_undefined_speakers": 0,
                            "female_speakers": 0,
                            "male_speakers": 0,
                            "undefined_gender_speakers": 0,
                            "unique_defined_speakers": 0,
                            "unique_female_speakers": 0,
                            "unique_male_speakers": 0,
                            "unique_undefined_gender_speakers": 0
                            }
            }}), 200, {'ContentType':'application/json'}
        else:
            res_identify_speakers = identify_speakers(article_text,id_text)

            if isinstance(res_identify_speakers, int): 
                if res_identify_speakers == 111111:
                    return json.dumps({"response" : "error-03"}), 400, {'ContentType':'application/json'}

                if res_identify_speakers == 222222:
                    return json.dumps({"response" : "error-04"}), 400, {'ContentType':'application/json'}
                
                if res_identify_speakers == 444444:
                    return json.dumps({"response" : "error-05"}), 400, {'ContentType':'application/json'}

                if res_identify_speakers == 555555:
                    return json.dumps({"response" : "error-06"}), 400, {'ContentType':'application/json'}
                    
                if res_identify_speakers == 999999:
                    return json.dumps({"response" : "error-07"}), 400, {'ContentType':'application/json'}

            else:    
                quotes_and_speakers, unique_speakers, stats = identify_speakers(article_text,id_text)
                return json.dumps({
                    "response" : {
                        "quotes_and_speakers" : quotes_and_speakers,
                        "unique_speakers" : unique_speakers,
                        "statistics" : stats
                    }}), 200, {'ContentType':'application/json'}
    else:
        return json.dumps({"response" : "error-02"}), 400, {'ContentType':'application/json'}

if __name__ == "__main__":
    app.run(debug=True, port="8080", host="0.0.0.0")