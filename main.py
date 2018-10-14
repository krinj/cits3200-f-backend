from flask import Flask, request, jsonify
from response_data import *
import time
from typing import List

from response import get_survey_id
from response import get_response
from response import get_text_questions
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


@app.route('/debug', methods=["GET", "POST"])
def debug():
    """ Return the POST object back as JSON. """
    post_data = request.json
    return jsonify(post_data)


@app.route('/manual_submit', methods=["GET", "POST"])
def manual_submit():
    """
    Receive Survey Response as a POST request.
    Assumes that we receive a JSON object with all of the keys populated.
    """
    post_data = request.json

    r_data = ResponseData()
    r_data.year_of_birth = int(post_data[K_YEAR_OF_BIRTH])
    r_data.organization = post_data[K_ORGANIZATION]
    r_data.question_name = post_data[K_QUESTION_NAME]
    r_data.question_id = post_data[K_QUESTION_ID]
    r_data.gender = post_data[K_GENDER]
    r_data.timestamp = int(time.time())
    r_data.employment_status = post_data[K_EMPLOYMENT_STATUS]
    r_data.response = post_data[K_RESPONSE]
    r_data.survey_id = post_data[K_SURVEY_ID]
    r_data.submission_id = post_data[K_SUBMISSION_ID]
    r_data.survey_name = post_data[K_SURVEY_NAME]

    _process_responses([r_data])

    return "CITS 3200: Manual Submission Endpoint"


@app.route('/submit', methods=["GET", "POST"])
def submit():
    # TODO: Fill in the code to send to the server here.
    # Keep this script clean. Write the Qualtrics extraction logic in a different file.

    post_data = request.json
    last_response_id = post_data['last_response_id']
    last_response_date = post_data['last_response_date']
    survey_id = get_survey_id(post_data['survey_id'])
    response = get_response(survey_id, last_response_date)

    r_data = ResponseData()
    r_data.year_of_birth = 1985
    r_data.organization = "<Organization>"
    r_data.question_name = "<Question Name>"
    r_data.question_id = "<Qualtrics Question ID>"
    r_data.gender = "<Gender>"
    r_data.timestamp = int(time.time())
    r_data.employment_status = "<Employment Status>"
    r_data.response = "<Response Text>"
    r_data.survey_id = "<Qualtrics Survey ID>"
    r_data.submission_id = "<Qualtrics Submission ID>"
    r_data.survey_name = "Manual Qualtrics Survey"

    _process_responses([r_data])

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
