__author__ = 'akhil'

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.conf import settings
import json
import hashlib

class GenCrawler(CrawlSpider):
    name = settings.get('BOT_NAME')

    def __init__(self, config='config.json', *args, **kwargs):

        config = json.load(open(config))

        self.allowed_domains = config.get('allowed_domains')
        self.start_urls = config.get('start_urls')

        self.rules = []
        if 'follow_urls' in config and len(config.get('follow_urls')) != 0:
            self.rules.append(Rule(LinkExtractor(allow=config.get('follow_urls')), follow=True))
        if 'save_urls' in config and len(config.get('save_urls')) != 0:
            self.rules.append(Rule(LinkExtractor(allow=config.get('save_urls')), callback='save_page'))
        if 'follow_save_urls' in config and len(config.get('follow_save_urls')) != 0:
            self.rules.append(Rule(LinkExtractor(allow=config.get('follow_save_urls')), follow=True, callback='save_page'))

        super(GenCrawler, self).__init__(*args, **kwargs)

    def save_page(self, response):
        item = {}
        # hxs = HtmlXPathSelector(response)
        # item = GlassdoorItem()
        # # Extract title
        # item['title'] = hxs.select('//header/h1/text()').extract() # XPath selector for title
        self.logger.info('got response' + str(response)[0:10])
        item['response'] = response.body

        path = settings.get('OUTPUT_PATH')
        file = open(path + hashlib.sha224(str(response)).hexdigest(), 'w')
        file.write(item['response'])
        file.close()

        return item