import datetime
import os
import random
import time
import uuid

from flask import Flask
from google.cloud import bigquery

# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)


@app.route('/')
def index():
    return "CITS 3200: Backend Server"


@app.route('/submit')
def submit():
    return "CITS 3200: Submission Endpoint"


@app.route('/test_submit')
def test_submit():
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


def submit_data(text, s_score, s_mag):

    client = bigquery.Client()
    dataset_id = "test_db_ae"
    table_id = "items"  # replace with your table ID
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)  # API request

    name = random.choice(["Jim", "Sarah", "Bob", "Alan", "Steve", "Mary", "Emily"])
    organization = random.choice(["Curtin", "UWA", "ECU", "Murdoch", "Stanford", "MIT", "Harvard"])
    age = random.randrange(18, 70)

    time_str = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    id = uuid.uuid4().hex

    rows_to_insert = [
        (name, organization, age, text, "", time_str, id, s_score, s_mag)
    ]

    errors = client.insert_rows(table, rows_to_insert)  # API request
    if not errors:
        return "Submit Data Success"
    else:
        return "Submit Data Failure"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

