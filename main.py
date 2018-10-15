from flask import Flask, request, jsonify
from response_data import *
import time
from typing import List

from response import *
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
K_YEAR_OF_BIRTH_TAG = "yob_"
K_ORGANIZATION_TAG = "org_"
K_GENDER_TAG = "gen_"
K_EMPLOYMENT_STATUS_TAG = "emp_"

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

    # post
    post_data = request.json
    survey_id = post_data['sid']

    # dictionaries
    survey_info_dict = get_survey_info_dict(survey_id)
    if survey_info_dict is None:
        raise Exception("Survey info not found")
        return None
    qname_qid_dict = get_qname_qid_dict(survey_info_dict)
    if qname_qid_dict is None:
        raise Exception("Questions not found in survey")
        return None
    response_dict = get_last_response_dict(survey_id)
    if response_dict is None:
        raise Exception("Last response not found")
        return None

    # QIDs
    nlp_qid = qname_qid_dict[K_NLP_TAG]
    gender_qid = qname_qid_dict[K_GENDER_TAG]
    employment_status_qid = qname_qid_dict[K_EMPLOYMENT_STATUS_TAG]

    # r_data assignment
    r_data = ResponseData()
    r_data.year_of_birth = int(response_dict[K_YEAR_OF_BIRTH_TAG])
    r_data.organization = response_dict[K_ORGANIZATION_TAG]
    r_data.question_name = ((survey_info_dict['questions'])[nlp_qid])['questionText']
    r_data.question_id = K_NLP_TAG
    r_data.gender = ((((survey_info_dict['questions'])[gender_qid])['choices'])[response_dict[K_GENDER_TAG]])[
        'choiceText']
    r_data.timestamp = int(time.time())
    r_data.employment_status = ((((survey_info_dict['questions'])[employment_status_qid])['choices'])[response_dict[
        K_EMPLOYMENT_STATUS_TAG]])['choiceText']
    r_data.response = response_dict[K_NLP_TAG]
    r_data.survey_id = survey_id
    r_data.submission_id = response_dict['ResponseId']
    r_data.survey_name = survey_info_dict['name']

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
