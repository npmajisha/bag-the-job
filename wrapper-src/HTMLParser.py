__author__ = 'akhil'

from bs4 import BeautifulSoup

class HTMLParser:

    def __init__(self, content):
        self.content = content

    def setContent(self, content):
        self._content = content

    def getContent(self):
        return self._content

    def getContentFromTags(self, tags):
        soup = BeautifulSoup(self.content, 'html.parser')
        tagContent = []
        for tag in tags:
            try:
                tagContent.append(soup.find(tag[0], {tag[1]: tag[2]}).get_text())
            except AttributeError:
                continue
        return tagContent

    def getHrefFromTags(self, tag):
        soup = BeautifulSoup(self.content, 'html.parser')
        links = []
        for div in soup.findAll(tag[0], {tag[1]: tag[2]}):
            for a in div.findAll('a'):
                links.append(a.attrs['href'])
        return links

    content = property(getContent, setContent)