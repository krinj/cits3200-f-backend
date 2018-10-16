# -*- coding: utf-8 -*-

"""
<ENTER DESCRIPTION HERE>
"""
import time

from response import get_survey_info_dict, get_qname_qid_dict, get_last_response_dict
from response_data import ResponseData

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


TAG_YEAR_OF_BIRTH = "YOB"
TAG_ORGANIZATION = "ORG"
TAG_GENDER = "GEN"
TAG_EMPLOYMENT_STATUS = "EMP"
TAG_NLP_RESPONSE = "NLP"


def handle_survey_response(survey_id: str, token: str, data_center: str="ca1"):

    # dictionaries
    survey_info_dict = get_survey_info_dict(survey_id, token, data_center)
    if survey_info_dict is None:
        raise Exception("Handle survey response error, survey info data not found")
        return None
    qname_qid_dict = get_qname_qid_dict(survey_info_dict)
    response_dict = get_last_response_dict(survey_id, token, data_center)
    if response_dict is None:
        raise Exception("Handle survey response error, last response data not found")
        return None

    # qids
    gender_qid = qname_qid_dict[TAG_GENDER]
    employment_status_qid = qname_qid_dict[TAG_EMPLOYMENT_STATUS]

    responses = []

    # r_data assignment
    for q_name, q_id in qname_qid_dict.items():
        if q_name[:len(TAG_NLP_RESPONSE)] != TAG_NLP_RESPONSE:
            continue

        r_data = ResponseData()
        r_data.year_of_birth = int(response_dict[TAG_YEAR_OF_BIRTH])
        r_data.organization = response_dict[TAG_ORGANIZATION]
        r_data.question_name = ((survey_info_dict['questions'])[q_id])['questionText']
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
