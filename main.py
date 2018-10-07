"""
receives data from qualtrics and process it to gc nl and add the result to gc sql

#TODO qualtrics api request to get multiple surveys and their ids, question ids, and only text answer question types
#TODO sql functions

Python version 3.6.6
"""

# import
import requests
import zipfile
import json
import io
import os

# import - flask sqlalchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# import - google cloud natural language api
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

"""
    getting the data from qualtrics
"""

# flask sqlalchemy app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# sqlalchemy database
db = SQLAlchemy(app)
class Example(db.Model):
    __tablename__ = 'example'
    id = db.Column('id', db.Integer, primary_key=True)
    data = db.Column('data', db.Unicode)
    # TODO change to actual database

# getting surveys, question ids then adding to database
#TODO use qualtrics api get survey

# qualtrics rest api user parameters
api_token = "MYAPITOKEN" #TODO change to actual value
file_format = "json"
data_center = 'ca1'
survey_id = '' #TODO change to actual value
last_response_id = None
included_question_ids = '' #TODO change to actual value

# checks the last response id from a file
cwd = os.getcwd()
files_path = cwd + '/files'
last_response_file = files_path + 'last_response.txt'
if not os.path.exists(files_path):
    os.mkdir(files_path)
if os.path.exists(last_response_file):
    file = open(last_response_file, "r")
    last_response_id = file.read().split('\n')

# qualtrics rest api static parameters
request_check_progress = 0
progress_status = "in progress"
base_url = "https://{0}.qualtrics.com/API/v3/responseexports/".format(data_center)
headers = {
    "content-type": "application/json",
    "x-api-token": api_token,
}

# creating data export, no last response id, get all responses
downloadRequest_payload = None
if last_response_id is None:
    download_request_payload = '{"format":"' + file_format + '","surveyId":"' + survey_id + '","includedQuestionIds":"' + included_question_ids + '"}'
else:
    download_request_payload = '{"format":"' + file_format + '","surveyId":"' + survey_id + '","lastResponseId":"' + last_response_id + '","includedQuestionIds":"' + included_question_ids + '"}'
download_request_url = base_url
download_request_response = requests.request("POST", download_request_url, data=download_request_payload, headers=headers)
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
download_path = cwd + '/json_downloads'
zipfile.ZipFile(io.BytesIO(request_download.content)).extractall(download_path)

# get all the responses in downloaded jsons
responses = []
for root, dirs, files in os.walk(download_path, topdown=False):
    for name in files:
        file = os.path.join(root, name)
        with open(file) as json_file:
            json_response = json.load(json_file)
            responses.append(json_response['responses'])

'''
    send the data to google cloud natural language api and send to gc sql
'''

# google cloud natural language api calls and assign all responses data to database
client = language.LanguageServiceClient()
for response in responses:
    id = response['id'] #TODO change to actual value
    text = response['text'] #TODO change to actual value
    #TODO add id and text to database

    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT,
    )

    # text sentiment analysis
    analyzed_text = client.analyze_sentiment(
        document=document,
        encoding_type='UTF32',
    )
    sentiment = analyzed_text.document_sentiment
    sentiment_score = sentiment.score
    #TODO add sentiment score to database

    # entities sentiment analysis
    analyzed_text_entities = client.analyze_entity_sentiment(
        document=document,
        encoding_type='UTF32',
    )
    entities = analyzed_text_entities.entities
    entity_name = ''
    entity_score = 0
    for i in range(0, len(entities)):
        entity_name = entities[i].name
        entity_score = entities[i].sentiment.score
        #TODO add id, entities, entitiy scores to database

# add last response id to last response file
last_response = responses[-1]
id = last_response['id'] #TODO change to actual value
file = open(last_response_file, "w")
file.write(id)

# delete downloaded files
for root, dirs, files in os.walk(download_path, topdown=False):
    for name in files:
        file = os.path.join(root, name)
        os.remove(file)

@app.route('/')
def it_works():
    """Return It works."""
    try:
        ret_str = "It works<br> \n"
        return ret_str
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.

    app.run(host='127.0.0.1', port=8080, debug=True)