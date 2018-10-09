# -*- coding: utf-8 -*-

"""
Use this helper script to generate a random ResponseData object.
"""

import random
import time
import uuid
from response_data import ResponseData


def generate_random_response() -> ResponseData:
    response_data = ResponseData()
    response_data.year_of_birth = random.randint(1960, 1995)
    response_data.organization = random.choice(["Google", "Apple", "IBM"])
    response_data.question_name = "Random Question Template?"
    response_data.question_id = "nlp_random_question"
    response_data.gender = random.choice(["male", "female", "unspecified"])
    response_data.timestamp = int(time.time())
    response_data.employment_status = random.choice(["part_time", "full_time", "unspecified"])
    response_data.response = "This is a random response!"
    response_data.survey_id = uuid.uuid4().hex
    response_data.submission_id = uuid.uuid4().hex
    response_data.survey_name = "random_survey"
    return response_data
