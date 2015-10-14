__author__ = 'akhil'

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.conf import settings
import json
import hashlib
import boto3
import re
import htmlparser

class GenCrawler(CrawlSpider):
    name = settings.get('BOT_NAME')

    def __init__(self, config='mooc-config.json', *args, **kwargs):

        self.config = json.load(open(config))
        self.allowed_domains = self.config.get('allowed_domains')
        self.start_urls = self.config.get('start_urls')

        self.rules = []
        if 'follow_urls' in self.config and len(self.config.get('follow_urls')) != 0:
            self.rules.append(Rule(LinkExtractor(allow=self.config.get('follow_urls')), follow=True))
        if 'save_urls' in self.config and len(self.config.get('save_urls')) != 0:
            self.rules.append(Rule(LinkExtractor(allow=self.config.get('save_urls')), callback='save_page'))
        if 'follow_save_urls' in self.config and len(self.config.get('follow_save_urls')) != 0:
            self.rules.append(Rule(LinkExtractor(allow=self.config.get('follow_save_urls')), follow=True, callback='save_page'))

        super(GenCrawler, self).__init__(*args, **kwargs)

    def save_page(self, response):
        item = {}
        item['response'] = response.body

        if self.do_any_filter(response.body, self.config) and self.do_all_filter(response.body, self.config):
            s3client = boto3.client('s3')
            s3client.put_object(Bucket=self.config.get('s3bucket'),
                                Key=self.config.get('s3folder') + '/' + hashlib.sha224(str(response)).hexdigest(),
                                Body=response.body)

        return item

    def do_any_filter(self, content, config):
        if 'any_filters' not in config.get('content_filter_params'):
            return True

        for filter in config.get('content_filter_params').get('any_filters'):
            filter_pattern = re.compile(filter.get('content'))
            tagContent = htmlparser.getContentFromTags(content, [(filter.get('tag'), filter.get('attribute'), filter.get('value'))])
            if len(tagContent) > 0 and filter_pattern.match(tagContent[0]):
                return True

        return False

    def do_all_filter(self, content, config):
        if 'all_filters' not in config.get('content_filter_params'):
            return True

        for filter in config.get('content_filter_params').get('all_filters'):
            filter_pattern = re.compile(filter.get('content'))
            tagContent = htmlparser.getContentFromTags(content, [(filter.get('tag'), filter.get('attribute'), filter.get('value'))])
            if len(tagContent) > 0 and not filter_pattern.match(tagContent[0]):
                return False

        return True