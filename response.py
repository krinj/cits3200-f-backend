# -*- coding: utf-8 -*-

"""
response and survey data extraction using Qualtrics API
"""

import io
import time
import datetime
import requests
import zipfile
import json
import csv

from response_data import ResponseData

__author__ = "Archy Nayoan"


# settings
MINUTES_INTERVAL = 10  # The time range of responses in minutes to get the last response

# global variables
K_HTTP_SUCCESS_OK = "200 - OK"  # The http status code for success OK
K_FILE_FORMAT = "csv"  # The format of the downloaded file

# question tags
TAG_YEAR_OF_BIRTH = "YOB"
TAG_ORGANIZATION = "ORG"
TAG_ABN = "ABN"
TAG_GENDER = "GEN"
TAG_EMPLOYMENT_STATUS = "EMP"
TAG_NLP_RESPONSE = "NLP"

# modes
MODE_LAST_RESPONSE = "LAST_RESPONSE"  # Get only the latest response.
MODE_ALL_RESPONSE = "ALL_RESPONSES"  # Get all the responses (as many as we can).
MODE_HOUR_RESPONSE = "HOUR_RESPONSE"  # Get the all the responses in the last hour.


def get_survey_responses(
        mode: str,
        survey_id: str,
        token: str,
        data_center: str="ca1",):
    """
    get responses of a single survey (given survey id)
    modes: get latest response, get all responses, get last hour response

    :param mode:
    :param survey_id:
    :param token:
    :param data_center:
    :return:
    """

    # initialisation
    responses = []  # all the responses in form of ResponseData data structure

    # extracting data from Qualtrics
    survey_info_dict = get_survey_info_dict(survey_id, token, data_center)
    if survey_info_dict is None:
        raise Exception("Get survey responses error, survey info data not found")
    qname_qid_dict = get_qname_qid_dict(survey_info_dict)
    response_dict_list = get_response_dict_list(mode, survey_id, token, data_center)
    if response_dict_list is None:
        raise Exception("Get survey responses error, responses data not found")

    # qids
    gender_qid = qname_qid_dict[TAG_GENDER]
    employment_status_qid = qname_qid_dict[TAG_EMPLOYMENT_STATUS]

    # from all dictionaries of responses convert to ResponseData data structure
    for response_dict in response_dict_list:

        # from all responses get different NLP responses
        for q_name, q_id in qname_qid_dict.items():
            if q_name[:len(TAG_NLP_RESPONSE)] != TAG_NLP_RESPONSE:
                continue

            if q_name not in response_dict:
                continue

            r_data = ResponseData()
            r_data.year_of_birth = int(response_dict[TAG_YEAR_OF_BIRTH])
            r_data.organization = response_dict[TAG_ORGANIZATION]
            r_data.question_name = ((survey_info_dict['questions'])[q_id])['questionText']
            r_data.abn = response_dict[TAG_ABN]
            r_data.question_id = q_name
            r_data.gender = \
                ((((survey_info_dict['questions'])[gender_qid])['choices'])[response_dict[TAG_GENDER]])['choiceText']
            r_data.timestamp = int(time.time())
            r_data.employment_status = \
                ((((survey_info_dict['questions'])[employment_status_qid])['choices'])[response_dict[
                    TAG_EMPLOYMENT_STATUS]])['choiceText']
            r_data.response = response_dict[q_name]
            r_data.survey_id = survey_id
            r_data.submission_id = response_dict['ResponseId']
            r_data.survey_name = survey_info_dict['name']

            responses.append(r_data)

    return responses


def get_survey_info_dict(survey_id: str, api_token: str, data_center: str):
    """

    :param survey_id:
    :param api_token:
    :param data_center:
    :return:
    """

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(data_center, survey_id)
    headers = {
        "x-api-token": api_token,
    }

    # survey info request
    survey_info_request_json = requests.get(base_url, headers=headers)
    survey_info_json = json.loads(survey_info_request_json.text)
    meta = survey_info_json['meta']

    # error checking
    if meta['httpStatus'] != K_HTTP_SUCCESS_OK:
        raise Exception("Qualtrics surveys API error.", meta['httpStatus'])

    result = survey_info_json['result']
    return result


def get_qname_qid_dict(survey_info_dict: dict):
    """

    :param survey_info_dict:
    :return:
    """

    # initialisation
    q_dict = {}

    for qid in (survey_info_dict['questions']).keys():
        question_name = ((survey_info_dict['questions'])[qid])['questionName']
        q_dict[question_name] = qid

    if not q_dict:
        return None
    else:
        return q_dict


def get_response_dict_list(mode: str, survey_id: str, api_token: str, data_center: str):
    """

    :param mode:
    :param survey_id:
    :param api_token:
    :param data_center:
    :return:
    """

    # initialisation
    responses_dict_list = []
    global request_check_response
    global download_request_payload

    # static parameters
    progress_status = "inProgress"
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(data_center, survey_id)
    headers = {
        "content-type": "application/json",
        "x-api-token": api_token,
    }

    # adjust download request payload according to mode
    if mode == MODE_LAST_RESPONSE:
        current_utc_datetime = datetime.datetime.utcnow()
        utc_time_zone = "Z"  # The UTC time zone in ISO 8601 format
        start_date = str((current_utc_datetime - datetime.timedelta(minutes=MINUTES_INTERVAL)).replace(
            microsecond=0).isoformat()) + utc_time_zone
        end_date = str(current_utc_datetime.replace(microsecond=0).isoformat()) + utc_time_zone
        download_request_payload = '{"format":"' + K_FILE_FORMAT + '","startDate":"' + start_date + '","endDate":"' + \
                                   end_date + '"}'

    elif mode == MODE_ALL_RESPONSE:
        download_request_payload = '{"format":"' + K_FILE_FORMAT + '"}'

    elif mode == MODE_HOUR_RESPONSE:
        current_utc_datetime = datetime.datetime.utcnow()
        utc_time_zone = "Z"  # The UTC time zone in ISO 8601 format
        start_date = str(
            (current_utc_datetime - datetime.timedelta(hours=1)).replace(microsecond=0).isoformat()) + utc_time_zone
        end_date = str(current_utc_datetime.replace(microsecond=0).isoformat()) + utc_time_zone
        download_request_payload = '{"format":"' + K_FILE_FORMAT + '","startDate":"' + start_date + '","endDate":"' + \
                                   end_date + '"}'

    # creating data export
    download_request_url = base_url
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
        raise Exception("Qualtrics API error, export failed")

    file_id = request_check_response.json()["result"]["fileId"]

    # downloading file
    request_download_url = base_url + file_id + '/file'
    request_download = requests.request("GET", request_download_url, headers=headers, stream=True)
    input_zip = zipfile.ZipFile(io.BytesIO(request_download.content))

    # converting files into bytestrings and read csv using dictreader
    for name in input_zip.namelist():
        byte_file = input_zip.read(name)
        fake_file = io.StringIO(byte_file.decode('utf8'))
        csv_reader = csv.DictReader(fake_file)
        dict_list = list(csv_reader)
        for dict_ in dict_list[2:]:

            # add only if response is finished
            finished = dict_['Finished']
            if finished == '1':
                responses_dict_list.append(dict_)

    # return list of dictionaries according to mode
    if mode == MODE_LAST_RESPONSE:
        return responses_dict_list[-1:]

    elif mode == MODE_ALL_RESPONSE:
        return responses_dict_list

    elif mode == MODE_HOUR_RESPONSE:
        return responses_dict_list
