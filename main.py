import time
from typing import List
from flask import Flask
from response_data import ResponseData
from response_generator import generate_random_response

from google.cloud import bigquery
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# ===================================================================================================
# Settings.
# ===================================================================================================


K_DATASET = "analytics"
K_TABLE = "responses"
K_NLP_TAG = "nlp_"

# ===================================================================================================
# App: Initialization.
# ===================================================================================================


app = Flask(__name__)


# ===================================================================================================
# App: Routing.
# ===================================================================================================


@app.route('/')
def index():
    return "CITS 3200: Backend Server"


@app.route('/submit', methods=["GET", "POST"])
def submit():
    # TODO: Fill in the code to send to the server here.
    # Keep this script clean. Write the Qualtrics extraction logic in a different file.

    response_data = ResponseData()
    response_data.year_of_birth = 1985
    response_data.organization = "<Organization>"
    response_data.question_name = "<Question Name>"
    response_data.question_id = "<Qualtrics Question ID>"
    response_data.gender = "<Gender>"
    response_data.timestamp = int(time.time())
    response_data.employment_status = "<Employment Status>"
    response_data.response = "<Response Text>"
    response_data.survey_id = "<Qualtrics Survey ID>"
    response_data.submission_id = "<Qualtrics Submission ID>"
    response_data.survey_name = "<Qualtrics Survey Name>"

    _process_responses([response_data])

    return "CITS 3200: Submission Endpoint"


@app.route('/test_submit', methods=["GET", "POST"])
def test_submit():
    # The good response uses the K_NLP_TAG tag so it should process.
    good_response = generate_random_response()
    good_response.question_id = f"{K_NLP_TAG}good_question"
    good_response.response = "I really like the new kitchen. The lighting is fantastic."

    # If the question ID does not have the K_NLP_TAG tag, it should be ignored.
    bad_response = generate_random_response()
    bad_response.question_id = "bad_question"

    _process_responses([good_response, bad_response])

    return "Test Submission With Fake Data"


# ===================================================================================================
# Private API Calls: BigQuery and Google NLP.
# ===================================================================================================


def _process_responses(response_data_list: List[ResponseData]):
    """ Filter out any responses without the correct question ID. """
    response_data_list = [r for r in response_data_list if K_NLP_TAG in r.question_id[:len(K_NLP_TAG)]]
    _process_nlp_inference(response_data_list)
    _upload_response(response_data_list)


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


def _process_nlp_inference(response_data_list: List[ResponseData]):
    """ Populates a list of ResponseData with sentiment and entity scores. """

    client = language.LanguageServiceClient()
    for response_data in response_data_list:

        # Create the text to analyze as a document.
        document = types.Document(
            content=response_data.response,
            type=enums.Document.Type.PLAIN_TEXT)

        # Submit the document text to the NLP sentiment analysis API.
        sentiment = client.analyze_sentiment(document=document).document_sentiment
        response_data.overall_sentiment = sentiment.score

        # Submit the document text to the NLP entity analysis API.
        entity_result = client.analyze_entity_sentiment(document=document)
        entities = entity_result.entities
        for entity in entities:
            response_data.add_entity(entity.name, entity.sentiment.score)


# ===================================================================================================
# Start the App.
# ===================================================================================================


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
