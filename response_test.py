import os

# init
os.environ["QUALTRICS_API_TOKEN"] = "c4JmqD2ohMRIbRNXTqd6YQmHlvxIBiVvV2eekgqo"
os.environ["QUALTRICS_DATA_CENTER"] = "ca1"

# testing
from response import *

survey_id = "SV_6z1si0Nf0fgGHUF"

questions = get_questions(survey_id)
print(questions)

text_questions = get_text_questions(survey_id)
print(text_questions)

# note that this will get surveys from current time until last 1 hour, make sure to do a survey response for the survey
response = get_last_response(survey_id)
print(response)
