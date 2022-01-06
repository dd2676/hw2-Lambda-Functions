import boto3
import json
import os, sys
import decimal
import requests
import time
from datetime import datetime
from requests_aws4auth import AWS4Auth
from requests.auth import HTTPBasicAuth

import logging
import botocore.config

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    
    print("MY NAME IS TANYA!")
    def type_converter(obj):
        if isinstance(obj, datetime):
            return obj.__str__()
    
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
    
    bucket = boto3.client('s3')

    rekog = boto3.client('rekognition')
    
    s3 = boto3.resource('s3')
    # logger.debug(event)
    # logger.debug('Time:\n{}'.format(time.ctime()))
    print("EVENT {}\n{}".format(time.ctime(),event))
    
    b = event["Records"][0]["s3"]["object"]["size"]
    bucketname = event["Records"][0]["s3"]["bucket"]["name"]
    filename = event["Records"][0]["s3"]["object"]["key"]
    
    print(b)
    print(bucketname)
    print(filename)
    
    # image = s3.Object(bucketname, filename)
    
    # print("Uploaded Image Metadata\n{}".format(image.metadata))
    
    image = bucket.get_object(Bucket=bucketname, Key=filename)
    httpHeaders = image['ResponseMetadata']['HTTPHeaders']
    customLabelsBoolean = False
    if 'x-amz-meta-customlabels' in httpHeaders:
        customlabels = image['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels']
        customlabels = [l.strip() for l in customlabels.split(', ')]
        customLabelsBoolean = True
        print(customlabels)
    else:
        print("NO CUSTOM LABELS")
        
    rekog_resp = rekog.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucketname,
                'Name': filename,
            }
        },
        MaxLabels=15,
        MinConfidence=65
    )
    
    labels = [r['Name'].lower() for r in rekog_resp['Labels']]
    print("Rekognition Labels: {}".format(labels))
    if customLabelsBoolean == True:
        for cl in customlabels:
            if cl not in labels:
                labels.append(cl.lower())
        print("FINAL Rekognition Labels + Custom Labels: {}".format(labels))
    else:
        print("FINAL Rekognition Labels: {}".format(labels))
  
    myOpenSearchUrl = "https://search-photos-no-vpc-wnawrz54b6kh4bqyav7idotsdu.us-east-1.es.amazonaws.com/"
    myOpenSearchUrl += 'hw2_photos/_doc'
    
    opensearch_obj = {
        "objectKey": filename,
        "bucket": bucketname,
        "createdTimestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "labels": [l for l in labels]
    }
    
    username = 'masterphotos2'
    password = 'Master@Photos2'
    
    print(opensearch_obj)
    results = requests.post(myOpenSearchUrl, auth=auth, json=opensearch_obj, headers=headers)
    # results = requests.post(myOpenSearchUrl, auth = HTTPBasicAuth(username, password), json=opensearch_obj, headers=headers)
    print('\n')
    print('{}'.format(results.json(), indent=2, sort_keys=False, default=type_converter))
    
    searchURL_1 = myOpenSearchUrl + "/_search?q=labels:".format(labels[0])
    search_response = requests.get(searchURL_1, auth=auth, headers=headers).json()
    
    print('\nSEARCH RESPONSE:\n{}'.format(search_response))
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
