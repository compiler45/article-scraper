"""Simple application for retrieving New Statesman articles
   , building their word count, and inserting it into a database"""

import sys
import requests
from lxml import html

from tasks.tasks import process_article, success_handler, error_handler


NEW_STATESMAN_BASE_URL = "https://www.newstatesman.com"
WRITERS_BASE_URL = "{}/writers".format(NEW_STATESMAN_BASE_URL)


def retrieve_article_links(author_url):
    req = requests.get(author_url)
    if req.status_code == 400:
        raise Exception('Wrong url?')
    elif not req.status_code == 200:
        raise Exception('Something has gone wrong here.')
    else:
        page_content = req.content
        html_doc = html.document_fromstring(page_content)
        article_links = html_doc.xpath("//div[@class='article-category']/following-sibling::*[1]/a/@href")

    return (NEW_STATESMAN_BASE_URL + l for l in article_links)


if __name__ == "__main__":
    # identify author's page, retrieve and process each article link
    author_name = sys.argv[1]
    article_list_url = "{}/{}".format(WRITERS_BASE_URL, author_name)
    links = retrieve_article_links(article_list_url)
    author_name_proper = author_name.replace("_", " ").title()
    for link in links:
        process_article.apply_async((author_name_proper, link))
