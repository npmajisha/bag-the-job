__author__ = 'Majisha'

import nltk
import jellyfish
import boto3
import json
import argparse
import logging
import concurrent
import csv
from logging import handlers

def setup_logging(logfile, loglevel=logging.DEBUG):
    logger = logging.getLogger('extractor')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=0)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def string_sanitizer(job_description):
    return job_description.replace("*","\n")

def getS3Object(s3client, config, key):
    return json.loads("["+str(s3client.get_object(Bucket=config.get('sourceS3Bucket'), Key=key)['Body'].read(),'utf-8')+"]")

def write_to_s3(s3client, config, fields, key, logger):
    try:
        s3client.put_object(Bucket=config.get('targetS3Bucket'), Key=key, Body=json.dumps(fields))
    except:
        logger.error("Unable to write %s to target bucket"%key)

def fuzzy_match_with_ref_list(nouns, skill_list):
    possible_skills = set()
    for noun in nouns:
        max_score = 0.00
        for skill in skill_list:
            jaro_score = jellyfish.jaro_winkler(skill, noun)
            if jaro_score > max_score:
                max_score = jaro_score
                ref_skill = skill
        if max_score >= 0.88:
            possible_skills.add(ref_skill)
    return possible_skills

def chunk_noun_extractor(text, chunk_parser,key, logger):
    jobDesc = string_sanitizer(text)
    nouns = []
    try:
        sentences = nltk.sent_tokenize(jobDesc)
        sentences = [nltk.word_tokenize(sent) for sent in sentences]
        sentences = [nltk.pos_tag(sent) for sent in sentences]

        for sent in sentences:
            for chunk in chunk_parser.parse(sent).subtrees():
                if chunk.label() == "NNP":
                    nouns.append(" ".join("%s" % tup[0].lower() for tup in chunk.leaves()))
    except:
        logger.error("Unable to extract nouns for %s"%key)
    return nouns

def skill_extractor(s3client, config, key, chunk_parser, skill_list, logger):
    print("Processing %s"%key)
    jobDetail = getS3Object(s3client,config, key)[0]
    #get all nouns
    nouns = chunk_noun_extractor(jobDetail["jobDesc"], chunk_parser, key, logger)
    #compare with reference skill list
    skills = fuzzy_match_with_ref_list(nouns, skill_list)
    #add to job details
    jobDetail["jobSkills"] = skills
    #store in s3
    write_to_s3(s3client, config, jobDetail, key, logger)
    return

def main():
    # initialize argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', help='configuration file')
    parser.add_argument('--reflist','-rl', help='reference list file')
    parser.add_argument('--logfile', '-lf', help='log file target')
    args = parser.parse_args()

    # initialize logging
    logger = setup_logging(logfile=args.logfile)

    #read configuration file
    with open(args.config) as file:
        config = json.loads(file.read())

    #read reference list from csv
    skill_list = []
    with open(args.reflist) as file:
        reader = csv.DictReader(file)
        for row in reader:
            skill_list.append(row['name'])

    if 'assumedRole' in config:
        sts_client = boto3.client('sts')
        assumed_role_object = sts_client.assume_role(RoleArn=config.get('assumedRole'),RoleSessionName='skill_extractor')
        session = boto3.session.Session(assumed_role_object.get('Credentials').get('AccessKeyId'),assumed_role_object.get('Credentials').get('SecretAccessKey'), assumed_role_object.get('Credentials').get('SessionToken'))
        s3 = session.resource('s3')
        client = session.client('s3')
    else:
        s3 = boto3.resource('s3')
        client = boto3.client('s3')

    bucket = s3.Bucket(config.get('sourceS3Bucket'))
    folder = config.get('sourceS3Folder')

    #chunking parser initializer
    grammar = r"NNP: {<NNP>+<NN>?}"
    chunk_parser = nltk.RegexpParser(grammar)

    #spawn threads to index
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = dict((executor.submit(skill_extractor, client, config, obj.key, chunk_parser,skill_list, logger), obj.key)
                           for obj in bucket.objects.filter(Prefix=folder+"/"))

            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                if future.exception() is not None:
                    logger.error('%r generated an exception: %s' % (key,
                                                                    future.exception()))
    return


if __name__ == '__main__':
    main()

