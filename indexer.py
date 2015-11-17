__author__ = 'Majisha'

import boto3
import json
import argparse
import logging
import concurrent
import pysolr
from logging import handlers

def setup_logging(logfile, loglevel=logging.DEBUG):
    logger = logging.getLogger('indexer')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=0)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def getS3Object(s3client, s3bucket, key):
    return json.loads("["+str(s3client.get_object(Bucket=s3bucket, Key=key)['Body'].read())+"]")

def index_into_solr(solr_url, s3client, config, key, logger):
    solr = pysolr.Solr(solr_url, timeout=10)
    try:
        payload = json.loads("["+str(s3client.get_object(Bucket=config.get('sourceS3Bucket'), Key=key)['Body'].read(),'utf-8')+"]")
        solr.add(payload,commit=True)
        logger.info("Indexed %s"%key)
    except pysolr.SolrError as err:
        logger.warn("Indexing failed for key %s with error %s" % (key,err))

def main():
    # initialize argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', help='configuration file')
    parser.add_argument('--logfile', '-lf', help='log file target')
    args = parser.parse_args()

    # initialize logging
    logger = setup_logging(logfile=args.logfile)

    #read configuration file
    with open(args.config) as file:
        config = json.loads(file.read())

    if 'assumedRole' in config:
        sts_client = boto3.client('sts')
        assumed_role_object = sts_client.assume_role(RoleArn=config.get('assumedRole'),RoleSessionName='solr_indexer')
        session = boto3.session.Session(assumed_role_object.get('Credentials').get('AccessKeyId'),assumed_role_object.get('Credentials').get('SecretAccessKey'), assumed_role_object.get('Credentials').get('SessionToken'))
        s3 = session.resource('s3')
        client = session.client('s3')
    else:
        s3 = boto3.resource('s3')
        client = boto3.client('s3')

    bucket = s3.Bucket(config.get('sourceS3Bucket'))
    folder = config.get('sourceS3Folder')

    solr_url = "http://"+ config.get('solrServerPort') + "/solr/" +config.get('solrCoreName')

    #spawn threads to index
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = dict((executor.submit(index_into_solr, solr_url, client, config, obj.key, logger), obj.key)
                           for obj in bucket.objects.filter(Prefix=folder+"/"))
    
            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                if future.exception() is not None:
                    logger.error('%r generated an exception: %s' % (key,
                                                                    future.exception()))
    return


if __name__ == '__main__':
    main()
