"""
receives data from qualtrics and process it to gc nl and add the result to gc big query

Python version 3.6.6
"""

# import
import requests
import zipfile
import json
import io
import os

# import - google cloud big query api
from google.cloud import bigquery

# import - google cloud natural language api
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

"""
    initialization
"""
api_token = os.environ["Q_API_TOKEN"]
data_center = os.environ["Q_DATA_CENTER"]
file_format = "json"
surveys = []
survey_info = []


"""
    list surveys
"""
# setting user Parameters
baseUrl = "https://{0}.qualtrics.com/API/v3/surveys".format(data_center)
headers = {
    "x-api-token": api_token,
    }

# adding surveys to the surveys list
offset = 0
while True:
    surveys_request_payload = '{"offset":"' + str(offset) + '"}'
    surveys_request_json = requests.get(baseUrl, data=surveys_request_payload, headers=headers)
    surveys_json = json.loads(surveys_request_json.text)
    meta = surveys_json['meta']
    #TODO error check
    result = surveys_json['result']
    elements = result['elements']
    if elements:
        for element in elements:
            surveys.append(element)
    if result['nextPage'] is None:
        break

"""
    list survey info
"""
for survey in surveys:
    survey_id = survey['id']

    # setting user parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(data_center, survey_id)
    headers = {
    "x-api-token": api_token,
    }

    # adding survey info to the survey_info list
    survey_info_request_json = requests.get(base_url, headers=headers)
    survey_info_json = json.loads(survey_info_request_json.text)
    meta = survey_info_json['meta']
    # TODO error check
    result = survey_info_json['result']
    survey_info.append(result)

"""
    get data from qualtrics and submit to gc bigquery
"""
for survey_i in survey_info:
    survey_id = survey_i['id']
    questions = survey_i['questions']
    text_question_names = []
    for question in questions:
        question_type = question['type']
        if question_type is "TX":
            question_name = question['questionName']
            text_question_names.append(question_name)

    get_and_submit_responses(survey_id, text_question_names)


"""
    gets data from qualtrics and submit to gc bigquery
"""
def get_and_submit_responses(survey_id, text_question_names):

    """
        downloading data from qualtrics
    """

    #TODO get current time and only get responses within a certain period of time

    # qualtrics get rest api static parameters
    request_check_progress = 0
    progress_status = "in progress"
    base_url = "https://{0}.qualtrics.com/API/v3/responseexports/".format(data_center)
    headers = {
        "content-type": "application/json",
        "x-api-token": api_token,
    }

    # creating data export
    download_request_payload = '{"format":"' + file_format + '","surveyId":"' + survey_id + '"}'
    download_request_url = base_url
    download_request_response = requests.request("POST", download_request_url, data=download_request_payload,
                                                 headers=headers)
    progress_id = download_request_response.json()["result"]["id"]

    # checking on data export progress and waiting until export is ready
    while request_check_progress < 100 and progress_status is not "complete":
        request_check_url = base_url + progress_id
        request_check_response = requests.request("GET", request_check_url, headers=headers)
        request_check_progress = request_check_response.json()["result"]["percentComplete"]

    # downloading file
    request_download_url = base_url + progress_id + '/file'
    request_download = requests.request("GET", request_download_url, headers=headers, stream=True)

    # unzipping the file
    cwd = os.getcwd()
    download_path = cwd + '/json_downloads'
    zipfile.ZipFile(io.BytesIO(request_download.content)).extractall(download_path)

    # get all the responses in downloaded jsons
    responses = []
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            with open(file) as json_file:
                json_response = json.load(json_file)
                if json_response['responses']:
                    responses.append(json_response['responses'])

    # when no responses do nothing
    if not responses:
        return None


    """
        responses processing, sending to gc natural language, then gc bigquery
    """

    # google cloud natural language init
    client = language.LanguageServiceClient()

    for response in responses:
        response_id = response['ResponseID']
        # TODO add response id to big query

        for key in response:

            # text question types
            if key in text_question_names:
                text = responses[key]
                # TODO add text to big query

                # document initialization
                document = types.Document(
                    content=text,
                    type=enums.Document.Type.PLAIN_TEXT,
                )

                # text sentiment analysis
                analyzed_text = client.analyze_sentiment(
                    document=document,
                    encoding_type='UTF32',
                )
                sentiment = analyzed_text.document_sentiment
                sentiment_score = sentiment.score
                # TODO add sentiment score to big query

                # entities sentiment analysis
                analyzed_text_entities = client.analyze_entity_sentiment(
                    document=document,
                    encoding_type='UTF32',
                )
                entities = analyzed_text_entities.entities
                entity_name = ''
                entity_score = 0
                for i in range(0, len(entities)):
                    entity_name = entities[i].name
                    entity_score = entities[i].sentiment.score
                    # TODO add id, entities, entitiy scores to big query

            # different question types
            else:
                #TODO all question types other than text

    # delete downloaded files
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            os.remove(file)

@app.route('/')
def it_works():
    """Return It works."""
    try:
        ret_str = "It works<br> \n"
        return ret_str
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    app.run(host='127.0.0.1', port=8080, debug=True)