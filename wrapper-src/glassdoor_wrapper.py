__author__ = 'Majisha'

from bs4 import BeautifulSoup
import re
import json
import argparse
import logging
from logging import handlers
import boto3
import concurrent

def setup_logging(logfile, loglevel=logging.INFO):
    logger = logging.getLogger('wrapper')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=0)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def write_to_s3(s3client, config, fields, key):
    s3client.put_object(Bucket=config.get('targetS3Bucket'), Key=key, Body=json.dumps(fields))

def extract_fields(content, config, logger, key):
    soup = BeautifulSoup(content,"html.parser")
    jobInfoScriptTag = soup.find(text = re.compile(r"window.gdGlobals = window.gdGlobals")).parent
    jobInfoString = jobInfoScriptTag.text
    try:
        jobInfoJson = json.loads(jobInfoString[jobInfoString.find("[")+1:jobInfoString.find("];")].replace('\'','"'))
        jobDescriptionTag = soup.find("div",{"class":"jobDescriptionContent"})
        if jobDescriptionTag is not None:
            jobDescriptionText = jobDescriptionTag.findAll(text=True)
            jobInfoJson["jobDesc"] = "\n".join(jobDescriptionText)
        else:
            jobInfoJson["jobDesc"] = ""
    except ValueError:
        logger.error("Invalid json in %s",key)

    return jobInfoJson

def process_key(s3client, config, key, logger):
    fileContent = s3client.get_object(Bucket=config.get('sourceS3Bucket'), Key=key)['Body'].read()
    fields = extract_fields(fileContent, config, logger, key)
    write_to_s3(s3client, config, fields, key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', help='configuration file')
    parser.add_argument('--logfile', '-lf', help='log file target')
    args = parser.parse_args()

    # initialize logging
    logger = setup_logging(logfile=args.logfile)

    with open(args.config) as file:
        config = json.loads(file.read())

    s3 = boto3.resource('s3')
    client = boto3.client('s3')

    bucket = s3.Bucket(config.get('sourceS3Bucket'))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = dict((executor.submit(process_key, client, config, key.key, logger), key.key)
                            for key in bucket.objects.all())

        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            if future.exception() is not None:
                logger.error('%r generated an exception: %s' % (key,
                                                     future.exception()))
    return


if __name__ == '__main__':
    main()
