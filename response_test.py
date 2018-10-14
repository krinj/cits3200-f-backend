from response import *
import time

survey_name = "sentiment analytics"
survey_id = get_survey_id(survey_name)
print(survey_id)
text_questions = get_text_questions(survey_id)
print(text_questions)
start_date = "2018-08-09T08:08:00Z"
response = get_response(survey_id, start_date)
print(response)
