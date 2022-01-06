import boto3
import os, sys
import json
import decimal
import requests
import time
from datetime import datetime
from requests_aws4auth import AWS4Auth
from requests.auth import HTTPBasicAuth
from collections import defaultdict
import logging
import botocore.config
import inflection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    # TODO implement
    bucketname_cloudformation = os.environ['HW2_PHOTOS_BUCKETNAME']
    def type_converter(obj):
        if isinstance(obj, datetime):
            return obj.__str__()
    # print(time.ctime(), event.keys(), "\nEVENT:\n", event)
    # print("-"*50)
    query = event['params']['querystring']['q']
    print(query)
    credentials = boto3.Session().get_credentials()
    
    auth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        'us-east-1',
        'es',
        session_token=credentials.token)
        
    headers = {
        "Content-Type": "application/json"
    }
    
    lex = boto3.client('lex-runtime')
    
    bucket = boto3.client('s3')
    
    s3 = boto3.resource('s3')
    userId = 'user' # str(uuid.uuid4())
    user_message = query # event['key1']
    print("User Message: {}".format(user_message))
    print(lex)
    
    response = lex.post_text(botName='PhotoSearchBot',
                                  botAlias='keywordbot',
                                  userId = userId, # str(userId),
                                  inputText=user_message)
    print(response)
    slots =  response['slots']
    keywords = list()
    for key, word in slots.items():
        if 'keyword' in key and word != None:
            print(word)
            keywords.append(inflection.singularize(word))
    print("-----------")
    print(keywords)
    myOpenSearchUrl = "https://search-photos-no-vpc-wnawrz54b6kh4bqyav7idotsdu.us-east-1.es.amazonaws.com/"
    myOpenSearchUrl += 'hw2_photos/_doc'
    
    URL_end = ''
    for w in keywords:
        URL_end += 'q=labels:{}&'.format(w)
    URL_end = URL_end[:-1]
    
    searchURL = myOpenSearchUrl + "/_search?" + URL_end
    search_response = requests.get(searchURL, auth=auth, headers=headers).json()
    
    images = defaultdict()
    
    for s in search_response['hits']['hits']:
        if s['_source']['objectKey'] not in images:
            images[s['_source']['objectKey']]=s['_source']['labels']
    
    result = {"results":list()}
    
    bucketname = bucketname_cloudformation # 'deepak-assignment-02-photos'
    for im, lb in images.items():
        url = "https://{}.s3.amazonaws.com/{}".format(bucketname, im)        
        labels = ''
        # for l in lb:
        #     labels += l + ', '
        result["results"].append({"url":url, "labels":[lb]})
    
    print('\n', result, '\n')
    
    return {
        'statusCode': 200,
        'body': result
    }