import boto3
import argparse
import concurrent.futures
import json
import logging
import logging.handlers
from model import Tag
from peewee import IntegrityError


def setup_logging(logfile, loglevel=logging.INFO):
    logger = logging.getLogger('tag-extractor')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=0)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def save_data(s3client, field, bucket, key):
    for data in read_fields(s3client, field, bucket, key):
        tag = Tag()
        tag.name = data.strip()
        try:
            tag.save(force_insert=True)
        except IntegrityError:
            pass


def read_fields(s3client, field, bucket, key):
    return list(json.loads(s3client.get_object(Bucket=bucket, Key=key)['Body'].read().decode("utf-8")).get(field))


def main():
    # initialize argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', help='configuration file')
    args = parser.parse_args()

    # initialize logging
    logger = setup_logging(logfile='extractor.log')

    # initialize config
    config = json.loads(open('config.json').read())

    # initialize aws parameters
    s3 = boto3.resource('s3')
    client = boto3.client('s3')
    bucket = s3.Bucket(config.get('s3bucket'))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = dict(
            (executor.submit(save_data, client, config.get('field'), config.get('s3bucket'), key.key), key.key)
            for key in bucket.objects.all().filter(Prefix=config.get('s3prefix') + '/'))

        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            if future.exception() is not None:
                logger.error('%r generated an exception: %s' % (key,
                                                                future.exception()))


if __name__ == "__main__":
    main()
