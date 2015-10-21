__author__ = 'akhil'

from bs4 import BeautifulSoup

def getContentFromTags(content, tags):
    soup = BeautifulSoup(content, 'html.parser')
    tagContent = []
    for tag in tags:
        try:
            tagContent.append(soup.find(tag[0], {tag[1]: tag[2]}).get_text())
        except AttributeError:
            continue
    return tagContent