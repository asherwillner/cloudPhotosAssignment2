import json
import logging
import boto3
from urllib.parse import unquote_plus
import urllib3
import uuid

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
lex = boto3.client('lexv2-models')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):

    bucketName = event['Records'][0]['s3']['bucket']['name']
    keyName = event['Records'][0]['s3']['object']['key']
    eventTime = event['Records'][0]['eventTime']
    keyNameNoPlus = unquote_plus(keyName)
    logger.debug(event)

    rekognitionResponse = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucketName,
                'Name': keyNameNoPlus
            }
        },
        MaxLabels=50
        # MinConfidence=
    )

    logger.debug(rekognitionResponse)

    labels = rekognitionResponse['Labels']

    s3response = s3.head_object(
        Bucket=bucketName,
        Key=keyNameNoPlus
    )

    logger.debug(s3response)

    esJSON = {
        "objectKey": keyName,
        "bucket": bucketName,
        "createdTimestamp": eventTime,
        "labels": []
    }

    lexresponse = lex.describe_slot_type(
        slotTypeId='LUMFJLKRL8',
        botId='LUGWI9HTVB',
        botVersion='DRAFT',
        localeId='en_US'
    )
    training = lexresponse['slotTypeValues']

    checkNewTrain = False

    customLabelsName = "x-amz-meta-customlabels"
    if customLabelsName in s3response['ResponseMetadata']['HTTPHeaders']:
        customLabels = s3response['ResponseMetadata']['HTTPHeaders'][customLabelsName]
        customLabels = customLabels.split(",")
        for label in customLabels:
            esJSON['labels'].append(label.title())
            newTrain = {
                "sampleValue": {
                    "value": label
                }
            }
            if newTrain not in training:
                training.append(newTrain)
                checkNewTrain = True

    if checkNewTrain:
        del lexresponse['creationDateTime']
        del lexresponse['lastUpdatedDateTime']
        lexresponse['slotTypeValues'] = training
        updateSlotResponse = lex.update_slot_type(
            slotTypeId=lexresponse['slotTypeId'],
            slotTypeName=lexresponse['slotTypeName'],
            slotTypeValues=lexresponse['slotTypeValues'],
            valueSelectionSetting=lexresponse['valueSelectionSetting'],
            botId=lexresponse['botId'],
            botVersion=lexresponse['botVersion'],
            localeId=lexresponse['localeId']
        )
        logger.debug(updateSlotResponse)

        responseBuildBot = lex.build_bot_locale(
            botId='LUGWI9HTVB',
            botVersion='DRAFT',
            localeId='en_US'
        )
        logger.debug(responseBuildBot)

    for label in labels:
        esJSON['labels'].append(label['Name'])

    logger.debug(esJSON)

    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth='ajwjgd:photosCloud2!')
    headers['Content-Type'] = 'application/json'
    id = str(uuid.uuid4())
    url = 'https://search-photos-tgwt34rzcfgvceliqw2nxjf3y4.us-east-1.es.amazonaws.com/photos/_doc/' + id

    encoded_body = json.dumps(esJSON)

    r = http.request('POST', url,
                 headers=headers,
                 body=encoded_body)

    logger.debug(json.loads(r.data))

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
