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

file_format = "csv"


def get_survey_info(survey_id, api_token: str, data_center: str):

    # static parameters
    base_url = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(data_center, survey_id)
    headers = {
        "x-api-token": api_token,
    }

    # survey info
    survey_info_request_json = requests.get(base_url, headers=headers)
    survey_info_json = json.loads(survey_info_request_json.text)
    meta = survey_info_json['meta']

    # TODO error check
    result = survey_info_json['result']
    return result


def get_qname_qid_dict(questions_info):

    # initialisation
    q_dict = {}

    for qid in questions_info.keys():
        question_info = questions_info[qid]
        question_name = question_info['questionName']
        q_dict[question_name] = qid

    if not q_dict:
        return None
    else:
        return q_dict


def get_last_response(survey_id, api_token: str, data_center: str):

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
    input_zip = zipfile.ZipFile(io.BytesIO(request_download.content))

    for name in input_zip.namelist():

        # We cannot save CSV files in GAE, so I must convert to ByteString and read it.
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
