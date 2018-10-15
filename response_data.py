# -*- coding: utf-8 -*-

"""
Contains a data structure to help format the rows for pushing
into BigQuery.
"""

import time
import uuid
from typing import List

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


# ===================================================================================================
# Table Keys: Check that these names match the field names on big table.
# ===================================================================================================

K_KEY: str = "key"
K_ORGANIZATION: str = "organization"
K_GENDER: str = "gender"
K_TIMESTAMP: str = "timestamp"
K_YEAR_OF_BIRTH: str = "year_of_birth"
K_EMPLOYMENT_STATUS: str = "employment_status"
K_SUBMISSION_ID: str = "submission_id"
K_SURVEY_ID: str = "survey_id"
K_SURVEY_NAME: str = "survey_name"
K_QUESTION_ID: str = "question_id"
K_QUESTION_NAME: str = "question_name"
K_RESPONSE: str = "response"
K_OVERALL_SENTIMENT: str = "overall_sentiment"
K_ENTITY: str = "entity"
K_ENTITY_NAME: str = "name"
K_ENTITY_SCORE: str = "score"

# ===================================================================================================
# Data Structure.
# ===================================================================================================


class Entity:
    def __init__(self, name: str = "Entity Name", score: float = 0.5):
        self.name: str = name
        self.score: float = score

    def data(self):
        return {
            K_ENTITY_NAME: self.name,
            K_ENTITY_SCORE: self.score
        }


class ResponseData:
    def __init__(self):
        timestamp = int(time.time())
        self.uid = uuid.uuid4().hex
        self.organization: str = "organization"
        self.key: str = f"{self.organization}_{timestamp}_{self.uid}"
        self.gender: str = "male"
        self.timestamp: int = timestamp
        self.year_of_birth: int = 1990
        self.employment_status: str = "full_time"
        self.submission_id: str = self.uid
        self.survey_id: str = self.uid
        self.survey_name: str = "Survey Name"
        self.question_id: str = "QuestionID"
        self.question_name: str = "Question Name"
        self.response: str = "Response"
        self.overall_sentiment: float = 0.5
        self.entity: List[Entity] = []

    def __repr__(self):
        data = self.export_as_json()
        return str(data)

    def generate_key(self):
        self.key = f"{self.organization.lower()}_{self.timestamp}_{self.uid}"

    def add_entity(self, name: str, score: float):
        self.entity.append(Entity(name, score))

    @property
    def _entity_as_data(self):
        """ Get all the entities in this object as a JSON object. """
        return [e.data() for e in self.entity]

    def export_as_json(self):
        """ Return this entire response as a JSON data object. """
        self.generate_key()
        data = {
            K_KEY: self.key,
            K_ORGANIZATION: self.organization,
            K_GENDER: self.gender,
            K_TIMESTAMP: self.timestamp,
            K_YEAR_OF_BIRTH: self.year_of_birth,
            K_EMPLOYMENT_STATUS: self.employment_status,
            K_SUBMISSION_ID: self.submission_id,
            K_SURVEY_ID: self.survey_id,
            K_SURVEY_NAME: self.survey_name,
            K_QUESTION_ID: self.question_id,
            K_QUESTION_NAME: self.question_name,
            K_RESPONSE: self.response,
            K_OVERALL_SENTIMENT: self.overall_sentiment,
            K_ENTITY: self._entity_as_data
        }
        return data
