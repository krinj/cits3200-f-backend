# -*- coding: utf-8 -*-

"""
    response
"""


import io
import os
import datetime
import requests
import zipfile
import json
import csv

# user parameters
api_token = os.environ["QUALTRICS_API_TOKEN"]
data_center = os.environ["QUALTRICS_DATA_CENTER"]
file_format = "csv"

# not needed, use sid from survey flow instead
def get_survey_id(survey_name):

    # initialisation
    surveys = []

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys".format(data_center)
    headers = {
        "x-api-token": api_token,
    }

    # adding surveys to the surveys list
    offset = 0
    while True:
        surveys_request_payload = '{"offset":"' + str(offset) + '"}'
        surveys_request_json = requests.get(base_url, data=surveys_request_payload, headers=headers)
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


def get_questions(survey_id):

    # initialisation
    question_names = []

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
        question_name = question['questionName']
        question_names.append(question_name)

    if not question_names:
        return None
    else:
        return question_names


def get_text_questions(survey_id):

    # initialisation
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


def get_last_response_legacy(survey_id):

    # initialisation
    responses = []
    timedelta_hours = 1
    time_zone = "Z"
    start_date = str(
        (datetime.datetime.utcnow() - datetime.timedelta(hours=timedelta_hours)).replace(
            microsecond=0).isoformat()) + time_zone
    end_date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat()) + time_zone

    # static parameters
    request_check_progress = 0
    progress_status = "in progress"
    base_url = "https://{0}.qualtrics.com/API/v3/responseexports/".format(data_center)
    headers = {
        "content-type": "application/json",
        "x-api-token": api_token,
    }

    # creating data export
    download_request_payload = '{"format":"' + file_format + '","surveyId":"' + survey_id + '","startDate":"' + start_date + '","endDate":"' + end_date + '"}'
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
    download_path = cwd + '/downloads'
    zipfile.ZipFile(io.BytesIO(request_download.content)).extractall(download_path)

    # get all the responses in downloaded jsons
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            with open(file) as csv_file:
                csv_reader = csv.DictReader(csv_file)
                i = 0
                for row in csv_reader:
                    if i > 1:
                        finished = row['Finished']
                        if finished == '1':
                            responses.append(row)
                    i = i + 1

    # delete downloaded files
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            os.remove(file)

    if not responses:
        return None
    else:
        return responses[-1]


def get_last_response(survey_id):

    # initialisation
    responses = []
    timedelta_hours = 1
    time_zone = "Z"
    start_date = str(
        (datetime.datetime.utcnow() - datetime.timedelta(hours=timedelta_hours)).replace(microsecond=0).isoformat()) + time_zone
    end_date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat()) + time_zone

    # static parameters
    request_check_progress = 0.0
    progress_status = "inProgress"
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(data_center, survey_id)
    headers = {
        "content-type": "application/json",
        "x-api-token": api_token,
    }

    # creating data export
    download_request_url = base_url
    download_request_payload = '{"format":"' + file_format + '","startDate":"' + start_date + '","endDate":"' + end_date + '"}'
    download_request_response = requests.request("POST", download_request_url, data=download_request_payload,
                                                 headers=headers)
    progress_id = download_request_response.json()["result"]["progressId"]

    # checking on data export progress and waiting until export is ready
    while not progress_status == "complete" and not progress_status == "failed":
        request_check_url = base_url + progress_id
        request_check_response = requests.request("GET", request_check_url, headers=headers)
        request_check_progress = request_check_response.json()["result"]["percentComplete"]
        progress_status = request_check_response.json()["result"]["status"]
        #print("Download is " + str(request_check_progress) + " complete")
        #print(request_check_response.json())

    # check for error
    if progress_status is "failed":
        raise Exception("export failed")

    file_id = request_check_response.json()["result"]["fileId"]

    # downloading file
    request_download_url = base_url + file_id + '/file'
    request_download = requests.request("GET", request_download_url, headers=headers, stream=True)

    # unzipping the file
    cwd = os.getcwd()
    download_path = cwd + '/downloads'
    zipfile.ZipFile(io.BytesIO(request_download.content)).extractall(download_path)

    # get all the responses in downloaded jsons
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            with open(file) as csv_file:
                csv_reader = csv.DictReader(csv_file)
                i = 0
                for row in csv_reader:
                    if i > 1:
                        finished = row['Finished']
                        if finished == '1':
                            responses.append(row)
                    i = i + 1

    # delete downloaded files
    for root, dirs, files in os.walk(download_path, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            os.remove(file)

    if not responses:
        return None
    else:
        return responses[-1]
