__author__ = 'Majisha'

import boto3
import json
import argparse
import logging
import requests
from logging import handlers
import concurrent

def setup_logging(logfile, loglevel=logging.INFO):
    logger = logging.getLogger('indexer')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=0)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def index_into_solr(s3client, config, key, logger):
    if key!=config.get('sourceS3Folder'):
        solr_url = "http://"+config.get('solrServerPort')+"/solr/"+config.get('solrCoreName')+"/update?commit=true"
        payload = json.loads("["+str(s3client.get_object(Bucket=config.get('sourceS3Bucket'), Key=key)['Body'].read(),'utf-8')+"]")
        headers = {'content-type': 'application/json'}
        r = requests.get(solr_url, data=json.dumps(payload), headers=headers)
        if r.status_code != requests.codes.ok:
            logger.warn("Indexing failed for key %s with content %s" % (key, payload))

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

    #initialize s3 resources
    s3 = boto3.resource('s3')
    client = boto3.client('s3')

    bucket = s3.Bucket(config.get('sourceS3Bucket'))
    folder = config.get('sourceS3Folder')

    #spawn threads to index
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = dict((executor.submit(index_into_solr, client, config, obj.key, logger), obj.key)
                           for obj in bucket.objects.filter(Prefix=folder))
    
            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                if future.exception() is not None:
                    logger.error('%r generated an exception: %s' % (key,
                                                                    future.exception()))

    return


if __name__ == '__main__':
    main()
