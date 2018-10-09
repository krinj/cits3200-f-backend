import requests
import json
import io
import os

"""
    initialization
"""
api_token = "2uru8E7EJNNE7EwylDz5ca4ZUOeFo4ceb3TMG8oY"
data_center = "ca1"
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
    list_survey_request_payload = '{"offset":"' + str(offset) + '"}'
    requests_json = requests.get(baseUrl, data=list_survey_request_payload, headers=headers)
    print(requests_json.text)
    surveys_json = json.loads(requests_json.text)
    result = surveys_json['result']
    meta = surveys_json['meta']
    elements = result['elements']
    if elements:
        for element in elements:
            surveys.append(element)
    if result['nextPage'] is None:
        break
    else:
        print('test')
    offset = offset + 1

"""
    list survey info
"""
for survey in surveys:
    surveyId = survey['id']

    # setting user parameters
    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}".format(data_center, surveyId)
    headers = {
    "x-api-token": api_token,
    }

    # adding survey info to the survey_info list
    #survey_info.append(requests.get(baseUrl, headers=headers))
    test = requests.get(baseUrl, headers=headers)
    print(test.text)

print(survey_info)