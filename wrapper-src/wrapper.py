__author__ = 'akhil'

import argparse
import json
import boto3
import re
import concurrent.futures
import logging
import logging.handlers
from HTMLParser import HTMLParser


def setup_logging(logfile, loglevel=logging.INFO):
    logger = logging.getLogger('wrapper')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=0)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def apply_filter(htmlParser, filter):
    if 'type' in filter and filter['type'] == 'href':
        content = htmlParser.getHrefFromTags((filter['tag'], filter['attribute'], filter['value']))[0]
    else:
        content = htmlParser.getContentFromTags([(filter['tag'], filter['attribute'], filter['value'])])[0]
    return content


def apply_regex(content, filter):
    match = re.match(filter['regex'], content)
    if match is None or match.group(int(filter['group'])) == '':
        raise RuntimeError('regex mismatch')
    content = match.group(int(filter['group']))
    return content


def extract_fields(content, config, logger, key):
    response = {}
    htmlParser = HTMLParser(content)
    for filter in config.get('content_filter_params'):
        try:
            content = apply_filter(htmlParser, filter)
        except IndexError:
            response[filter['target']] = ''
            logger.warn('%s missing for record %s' % (filter['target'], key))
            continue

        if 'regex' in filter:
            try:
                content = apply_regex(content, filter)
            except (IndexError, RuntimeError):
                logger.warn("regex '%s' failed on content '%s' for record '%s'" % (filter['regex'], content, key))

        response[filter['target']] = content
    return response


def process_key(s3client, config, key, logger):
    fileContent = s3client.get_object(Bucket=config.get('sourceS3Bucket'), Key=key)['Body'].read()
    fields = extract_fields(fileContent, config, logger, key)
    write_to_s3(s3client, config, fields, key)


def write_to_s3(s3client, config, fields, key):
    s3client.put_object(Bucket=config.get('targetS3Bucket'), Key=key, Body=json.dumps(fields))


if __name__ == "__main__":
    # initialize argument parser
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