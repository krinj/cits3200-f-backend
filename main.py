import datetime
import os
import random
import time
import uuid
from typing import List
from response_data import ResponseData

from flask import Flask
from google.cloud import bigquery

# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.


app = Flask(__name__)

K_DATASET = "analytics"
K_TABLE = "responses"


@app.route('/')
def index():
    return "CITS 3200: Backend Server"


@app.route('/submit')
def submit():
    return "CITS 3200: Submission Endpoint"


@app.route('/test_submit')
def test_submit():

    response_data = ResponseData()
    response_data.year_of_birth = 1986
    response_data.organization = "Google"
    response_data.question_name = "How are you today?"
    response_data.question_id = "nlp_how_are_you"
    response_data.gender = "male"
    response_data.timestamp = time.time()
    response_data.employment_status = "full_time"
    response_data.response = "I had a great day today! I love this new CEO, he bought us a fantastic ping pong table."
    response_data.survey_id = uuid.uuid4().hex
    response_data.submission_id = uuid.uuid4().hex
    response_data.survey_name = "default_survey"

    _upload_response([response_data])

    return "Test Submission With Fake Data"


# @app.route('/')
# def hello():
#     """Return a friendly HTTP greeting."""
#     try:
#         return "Hello App Example"
#
#         # ret_str = "Hello World<br> \n"
#         # ret_str += f"{bigquery.__version__}<br>"
#         # auth = os.listdir(".")
#         # ret_str += "List Dir<br> \n"
#         # for i in auth:
#         #     ret_str += f"{i}<br> \n"
#         #
#         # feedback = "I think this is a great product. " \
#         #            "I had an amazing time at the BBQ party, but I wish there was more alcohol."
#         # s_score, s_mag = submit_nlp_request(feedback)
#         # ret_str += submit_data(feedback, s_score, s_mag)
#         # return ret_str
#     except Exception as e:
#         return str(e)

def _upload_response(response_data_list: List[ResponseData]):
    """ Upload this response data to the BigQuery table. """

    # Setup the client.
    client = bigquery.Client()
    table_ref = client.dataset(K_DATASET).table(K_TABLE)
    table = client.get_table(table_ref)

    # Convert the responses to JSON format and submit them.
    rows_to_insert = [r.export_as_json() for r in response_data_list]
    errors = client.insert_rows(table, rows_to_insert)

    # Return the error status.
    if not errors:
        return "Submit Data Success"
    else:
        return "Submit Data Failure"


def submit_nlp_request(text):
    # Instantiates a client
    client = language.LanguageServiceClient()

    # The text to analyze
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment
    print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))
    return sentiment.score, sentiment.magnitude


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

