# -*- coding: utf-8 -*-

"""
    response
"""

import requests
import zipfile
import json
import io
import os
import datetime

# user parameters
#api_token = os.environ["QUALTRICS_API_TOKEN"]
api_token = "2uru8E7EJNNE7EwylDz5ca4ZUOeFo4ceb3TMG8oY"

#data_center = os.environ["QUALTRICS_DATA_CENTER"]
data_center = "ca1"

file_format = "csv"

def get_survey_id(survey_name):

    # initialisation
    surveys = []

    # static parameters
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
        # TODO error check using meta
        result = surveys_json['result']
        elements = result['elements']
        if elements:
            for element in elements:
                surveys.append(element)
        if result['nextPage'] is None:
            break

    # search survey id based on survey name
    for survey in surveys:
        name = survey['name']
        if name == survey_name:
            survey_id = survey['id']
            return survey_id

def get_text_questions(survey_id):

    #initialisation
    text_question_names = []

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(data_center, survey_id)
    headers = {
        "x-api-token": api_token,
    }

    survey_info_request_json = requests.get(base_url, headers=headers)
    survey_info_json = json.loads(survey_info_request_json.text)
    meta = survey_info_json['meta']
    # TODO error check using meta, when not return 200
    result = survey_info_json['result']
    questions = result['questions']
    for question_name in questions.keys():
        question = questions[question_name]
        question_type = question['questionType']
        type = question_type['type']
        if type == "TE":
            question_name = question['questionName']
            text_question_names.append(question_name)

    if not text_question_names:
        return None
    else:
        return text_question_names

def get_response(survey_id, last_response_date):

    # initialisation
    responses = []

    # static parameters
    progress_status = "inProgress"
    base_url = "https://{0}.qualtrics.com/API/v3/survey/{1}/export-responses/".format(data_center, survey_id)
    headers = {
        "content-type": "application/json",
        "x-api-token": api_token,
    }

    # creating data export
    download_request_url = base_url
    end_date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat()) + "Z"
    download_request_payload = '{"format":"' + file_format + '","startDate":"' + last_response_date + '","endDate":"' + end_date + '","limit":"' + str(1) + '"}'
    download_request_response = requests.request("POST", download_request_url, data=download_request_payload,
                                                 headers=headers)
    print(download_request_response.text)
    # TODO ERRROR in result
    progress_id = download_request_response.json()["result"]["progressId"]

    # checking on data export progress and waiting until export is ready
    while progress_status is not "complete" and progress_status is not "failed":
        request_check_url = base_url + progress_id
        request_check_response = requests.request("GET", request_check_url, headers=headers)

    # check for error
    if progress_status is "failed":
        raise Exception("export failed")

    file_id = request_check_response.json()["result"]["fileId"]

    # downloading file
    request_download_url = base_url + file_id + '/file'
    request_download = requests.request("GET", request_download_url, headers=headers, stream=True)

    # unzipping the file
    cwd = os.getcwd()
    download_path = cwd + '/response_downloads'
    zipfile.ZipFile(io.BytesIO(request_download.content)).extractall(download_path)

    # get all the responses in downloaded jsons
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            with open(file) as json_file:
                json_response = json.load(json_file)
                if json_response['responses']:
                    responses.append(json_response['responses'])

    # delete downloaded files
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            os.remove(file)

    if not responses:
        return None
    else:
        return responses
