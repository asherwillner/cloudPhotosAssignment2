import json
import logging
import boto3
import urllib3
# from opensearchpy import OpenSearch

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
lex = boto3.client('lexv2-runtime')
s3 = boto3.client('s3')

def badSearch():
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps(["badKeyword"])
    }

def lambda_handler(event, context):
    logger.debug("here")
    searchText = event["queryStringParameters"]["q"]

    response = lex.recognize_text(
        botId='LUGWI9HTVB',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId='28',
        text=searchText,
        sessionState={})

    keywords = []

    if 'keyword' not in response['sessionState']['intent']['slots']:
        return badSearch()

    keywordsResponse = response['sessionState']['intent']['slots']['keyword']['values']
    for key in keywordsResponse:
        keywords.append(key['value']['interpretedValue'])

    logger.debug(keywords)

    returnPictures = []

    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth='ajwjgd:photosCloud2!')
    for keyword in keywords:
        url = 'https://search-photos-tgwt34rzcfgvceliqw2nxjf3y4.us-east-1.es.amazonaws.com/photos/_search?q={}&pretty=true'.format(keyword)
        response = http.request('GET',
                                url,
                                headers=headers,
                                retries = False)
        logger.debug(json.loads(response.data))
        hits = json.loads(response.data)['hits']['hits']
        for hit in hits:
            details = hit['_source']
            objectKey = details['objectKey']
            photoURL = 'https://photos-cloudhw2.s3.amazonaws.com/{}'.format(objectKey)
            if photoURL not in returnPictures:
                returnPictures.append(photoURL)


    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps(returnPictures)
    }
