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

# parameters
K_API_TOKEN = os.environ["QUALTRICS_API_TOKEN"]
K_DATA_CENTER = os.environ["QUALTRICS_DATA_CENTER"]
K_FILE_FORMAT = "csv"
K_SUCCESS_OK = "200 - OK"
K_HOUR_INTERVAL = 1
K_TIME_ZONE = "Z"


def get_survey_info_dict(survey_id):
    """

    :param survey_id: the survey id of a survey
    :return: dictionary of the json request
    """

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(K_DATA_CENTER, survey_id)
    headers = {
        "x-api-token": K_API_TOKEN,
    }

    # survey info
    survey_info_request_json = requests.get(base_url, headers=headers)
    survey_info_json = json.loads(survey_info_request_json.text)
    meta = survey_info_json['meta']
    if meta['httpStatus'] != K_SUCCESS_OK:
        raise Exception("Qualtrics surveys API error.", meta['httpStatus'])
    else:
        result = survey_info_json['result']
        return result


def get_qname_qid_dict(survey_info_dict):
    """

    :param survey_info_dict:
    :return:
    """

    # initialisation
    q_dict = {}

    # mapping dictionary
    for qid in (survey_info_dict['questions']).keys():
        question_name = ((survey_info_dict['questions'])[qid])['questionName']
        q_dict[question_name] = qid

    if not q_dict:
        return None
    else:
        return q_dict


def get_last_response_dict(survey_id):
    """
    to get the latest response from a survey within the current time and the last 1 hour

    :param survey_id: the id of the survey
    :return: dictionary of a response
    """

    # initialisation
    responses = []
    start_date = str(
        (datetime.datetime.utcnow() - datetime.timedelta(hours=K_HOUR_INTERVAL)).replace(microsecond=0).isoformat()) + \
                 K_TIME_ZONE
    end_date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat()) + K_TIME_ZONE

    # static parameters
    progress_status = "inProgress"
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(K_DATA_CENTER, survey_id)
    headers = {
        "content-type": "application/json",
        "x-api-token": K_API_TOKEN,
    }

    # creating data export
    download_request_url = base_url
    download_request_payload = '{"format":"' + K_FILE_FORMAT + '","startDate":"' + start_date + '","endDate":"' + \
                               end_date + '"}'
    download_request_response = requests.request("POST", download_request_url, data=download_request_payload,
                                                 headers=headers)
    progress_id = download_request_response.json()["result"]["progressId"]

    # checking on data export progress and waiting until export is ready
    while not progress_status == "complete" and not progress_status == "failed":
        request_check_url = base_url + progress_id
        request_check_response = requests.request("GET", request_check_url, headers=headers)
        progress_status = request_check_response.json()["result"]["status"]

    # check for error
    if progress_status is "failed":
        raise Exception("Qualtrics API export responses failed")

    file_id = request_check_response.json()["result"]["fileId"]

    # downloading file
    request_download_url = base_url + file_id + '/file'
    request_download = requests.request("GET", request_download_url, headers=headers, stream=True)

    # unzipping the file
    cwd = os.getcwd()
    download_path = cwd + '/downloads'
    zipfile.ZipFile(io.BytesIO(request_download.content)).extractall(download_path)

    # get all the responses in downloaded csvs
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


# not needed, use sid from survey flow instead
def get_survey_id(survey_name):
    """
    get the survey id of a survey given its name

    :param survey_name: the name of the survey in Qualtrics
    :return: the survey id of that survey name
    """

    # initialisation
    surveys = []

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys".format(K_DATA_CENTER)
    headers = {
        "x-api-token": K_API_TOKEN,
    }

    # adding surveys to the surveys list
    offset = 0
    while True:
        surveys_request_payload = '{"offset":"' + str(offset) + '"}'
        surveys_request_json = requests.get(base_url, data=surveys_request_payload, headers=headers)
        surveys_json = json.loads(surveys_request_json.text)
        meta = surveys_json['meta']
        if meta['httpStatus'] != K_SUCCESS_OK:
            raise Exception("Qualtrics surveys API error.", meta['httpStatus'])
        else:
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


# not used
def get_questions(survey_id):
    """

    :param survey_id:
    :return:
    """

    # initialisation
    question_names = []

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(K_DATA_CENTER, survey_id)
    headers = {
        "x-api-token": K_API_TOKEN,
    }

    survey_info_request_json = requests.get(base_url, headers=headers)
    survey_info_json = json.loads(survey_info_request_json.text)
    meta = survey_info_json['meta']
    if meta['httpStatus'] != K_SUCCESS_OK:
        raise Exception("Qualtrics surveys API error.", meta['httpStatus'])
    else:
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


# not used
def get_text_questions(survey_id):
    """

    :param survey_id:
    :return:
    """

    # initialisation
    text_question_names = []

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(K_DATA_CENTER, survey_id)
    headers = {
        "x-api-token": K_API_TOKEN,
    }

    survey_info_request_json = requests.get(base_url, headers=headers)
    survey_info_json = json.loads(survey_info_request_json.text)
    meta = survey_info_json['meta']
    if meta['httpStatus'] != K_SUCCESS_OK:
        raise Exception("Qualtrics surveys API error.", meta['httpStatus'])
    else:
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


# not used, using legacy Qualtrics API
def get_last_response_dict_legacy(survey_id):
    """

    :param survey_id:
    :return:
    """

    # initialisation
    responses = []
    start_date = str(
        (datetime.datetime.utcnow() - datetime.timedelta(hours=K_HOUR_INTERVAL)).replace(
            microsecond=0).isoformat()) + K_TIME_ZONE
    end_date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat()) + K_TIME_ZONE

    # static parameters
    request_check_progress = 0
    progress_status = "in progress"
    base_url = "https://{0}.qualtrics.com/API/v3/responseexports/".format(K_DATA_CENTER)
    headers = {
        "content-type": "application/json",
        "x-api-token": K_API_TOKEN,
    }

    # creating data export
    download_request_payload = '{"format":"' + K_FILE_FORMAT + '","surveyId":"' + survey_id + '","startDate":"' + \
                               start_date + '","endDate":"' + end_date + '"}'
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

    # get all the responses in downloaded csvs
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
