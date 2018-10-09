import time
import uuid
from typing import List
from response_data import ResponseData
from flask import Flask
from google.cloud import bigquery

from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types


# ===================================================================================================
# Settings.
# ===================================================================================================

K_DATASET = "analytics"
K_TABLE = "responses"


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

    _process_nlp_inference([response_data])
    _upload_response([response_data])

    return "Test Submission With Fake Data"


# ===================================================================================================
# Private API Calls: BigQuery and Google NLP.
# ===================================================================================================


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

