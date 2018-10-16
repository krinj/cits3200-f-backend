# -*- coding: utf-8 -*-

"""
response and survey data extraction using Qualtrics API
"""

import io
import datetime
import requests
import zipfile
import json
import csv

__author__ = "Archy Nayoan"


# parameters
FILE_FORMAT = "csv"
HOUR_INTERVAL = 1
TIME_ZONE = "Z"
HTTP_SUCCESS_OK = "200 - OK"


def get_survey_info_dict(survey_id, api_token: str, data_center: str):
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
    if meta['httpStatus'] != HTTP_SUCCESS_OK:
        raise Exception("Qualtrics surveys API error.", meta['httpStatus'])
        return None

    result = survey_info_json['result']
    return result


def get_qname_qid_dict(survey_info_dict):
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


def get_last_response_dict(survey_id, api_token: str, data_center: str):
    """

    :param survey_id:
    :param api_token:
    :param data_center:
    :return:
    """

    # initialisation
    responses = []
    start_date = str(
        (datetime.datetime.utcnow() - datetime.timedelta(hours=HOUR_INTERVAL)).replace(microsecond=0).isoformat()) + \
                 TIME_ZONE
    end_date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat()) + TIME_ZONE

    # static parameters
    progress_status = "inProgress"
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(data_center, survey_id)
    headers = {
        "content-type": "application/json",
        "x-api-token": api_token,
    }

    # creating data export
    download_request_url = base_url
    download_request_payload = '{"format":"' + FILE_FORMAT + '","startDate":"' + start_date + '","endDate":"' + \
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
        raise Exception("Qualtrics API error, export failed")
        return None

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
        i = 0
        for row in csv_reader:
            if i > 1:
                finished = row['Finished']
                if finished == '1':
                    responses.append(row)
            i = i + 1

    return responses[-1]
