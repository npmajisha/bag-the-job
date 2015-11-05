__author__ = 'Majisha'

import boto3
import json
import argparse

def main():

    # initialize argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', help='configuration file')
    parser.add_argument('--logfile', '-lf', help='log file target')
    args = parser.parse_args()


    with open(args.config) as file:
        config = json.loads(file.read())

    s3 = boto3.resource('s3')
    client = boto3.client('s3')

    bucket = s3.Bucket(config.get('sourceS3Bucket'))

    return


if __name__ == '__main__':
    main()
