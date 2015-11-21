__author__ = 'akhil'

import argparse
import json
import boto3
import nltk
import concurrent
import logging
from concurrent import futures
from logging import handlers
import os
import re

def setup_logging(logfile, loglevel=logging.DEBUG):
    # create log directory
    directory = os.path.dirname(logfile)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # setup logger
    logger = logging.getLogger('extractor')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=0)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def add_to_candidate_lists(candidate_list, candidate_lists):
    if len(candidate_list) >= 2:
        candidate_lists.append(candidate_list)


def get_filtered_text(text):
    textlist = nltk.sent_tokenize(text)
    return list(filter(lambda line: re.match('^[\W\s]+', line), textlist))


def has_valid_predecessor(index, chunks):
    valid_predecessors = [',', 'or', 'and']
    try:
        pred = chunks[index - 1][0]
        if pred in valid_predecessors:
            return True
    except IndexError:
        return False


def extract_terms(line, parser, candidate_lists):
    nnps = []
    tokens = nltk.pos_tag(nltk.word_tokenize(line))
    chunks = list(parser.parse(tokens).subtrees())[0]
    for chunk in chunks:
        if type(chunk).__name__ == 'Tree' and chunk.label() == 'NNP':
            nnp = " ".join("%s" % tup[0].lower() for tup in chunk.leaves())
            if has_valid_predecessor(chunks.index(chunk), chunks):
                nnps.append(nnp)
            else:
                add_to_candidate_lists(nnps, candidate_lists)
                nnps = [nnp]
    add_to_candidate_lists(nnps, candidate_lists)


def get_s3_object(s3client, config, key):
    return json.loads(
        str(s3client.get_object(Bucket=config.get('sourceS3Bucket'), Key=key)['Body'].read(), 'utf-8'))


def extract_candidate_lists(client, config, key, parser, candidate_lists, logger):
    job_posting = get_s3_object(client, config, key)
    job_desc = job_posting["jobDesc"]

    filtered_text = get_filtered_text(job_desc)
    if len(filtered_text) == 0:
        logger.warn("Empty filtered text for %s" % key)

    for line in filtered_text:
        extract_terms(line, parser, candidate_lists)


def main():
    # initialize argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', help='configuration file')
    parser.add_argument('--logfile', '-lf', help='log file target')
    args = parser.parse_args()

    # initialize logging
    logger = setup_logging(logfile=args.logfile)

    # read configuration file
    with open(args.config) as file:
        config = json.loads(file.read())

    # initialize aws resources
    if 'assumedRole' in config:
        sts_client = boto3.client('sts')
        assumed_role_object = sts_client.assume_role(RoleArn=config.get('assumedRole'),
                                                     RoleSessionName='skill_extractor')
        session = boto3.session.Session(assumed_role_object.get('Credentials').get('AccessKeyId'),
                                        assumed_role_object.get('Credentials').get('SecretAccessKey'),
                                        assumed_role_object.get('Credentials').get('SessionToken'))
        s3 = session.resource('s3')
        client = session.client('s3')
    else:
        s3 = boto3.resource('s3')
        client = boto3.client('s3')

    bucket = s3.Bucket(config.get('sourceS3Bucket'))
    folder = config.get('sourceS3Folder')

    grammar = r"NNP: {<NNP>+<NN>?}"
    parser = nltk.RegexpParser(grammar)
    candidate_lists = []

    # spawn threads to extract
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = dict(
            (
                executor.submit(extract_candidate_lists, client, config, obj.key, parser,
                                candidate_lists, logger),
                obj.key)
            for obj in bucket.objects.filter(Prefix=folder + "/"))

        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            if future.exception() is not None:
                logger.error('%r generated an exception: %s' % (key,
                                                                future.exception()))

    print(candidate_lists)


if __name__ == "__main__":
    main()
