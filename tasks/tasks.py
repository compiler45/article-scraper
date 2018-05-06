import requests
import celery

from celery.signals import worker_process_init
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from lxml import html
from collections import defaultdict
from celery.utils.log import get_task_logger


from .db import Base, Article, WordCount
from .celery import app

logger = get_task_logger(__name__)


@worker_process_init.connect
def create_db_connection(**kwargs):
    # unique db connection for each worker process
    engine = create_engine("postgresql://postgres:strangemountain@localhost/articles_words_db",
                           pool_pre_ping=True)
    logger.info("Database connection established")
    global db_session
    db_session = scoped_session(sessionmaker(bind=engine))
    Base.metadata.create_all(bind=engine)


@app.task
def process_article(author_name_proper, article_url):
    retrieve_text_task = retrieve_article_text.s(article_url)
    analyse_text_task = analyse_text.s()
    store_results_task = store_results.s(article_url, author_name_proper).set(link=success_handler.s(),
                                                                              link_error=error_handler.s())

    return (retrieve_text_task | analyse_text_task | store_results_task).delay()


@app.task(default_retry_delay=3)
def retrieve_article_text(article_url):
    logger.info("RETRIEVING {}".format(article_url))
    r = requests.get(article_url)
    text = r.text
    return text


@app.task(bind=True)
def analyse_text(self, text):
    html_content = html.document_fromstring(text)
    # get article name
    article_name = html_content.xpath("//header[re:match(@class, '.*article-header.*')]/"
                                      "h1[@class=\"title inf_class\"]/text()",
                                      namespaces={"re": "http://exslt.org/regular-expressions"})[0]

    # calculate word frequencies
    paragraphs = html_content.xpath("//div[@class='field-items'][1]//p/child::text()")
    word_freqs = defaultdict(int)
    # 'clean' paragraphs
    dirty_chars = ["\t", "\n", ".", "?", "!", "\"", ",", "(", ")"]
    for paragraph in paragraphs:
        clean_paragraph = paragraph.strip()
        for char in dirty_chars:
            clean_paragraph = clean_paragraph.replace(char, "")

        # store word frequencies
        paragraph_words = clean_paragraph.lower().split(" ")
        for word in paragraph_words:
            word_freqs[word] += 1

    logger.info("Word frequencies calculated for {}".format(self.request.id))

    return {"article_name": article_name.strip(), "word_freqs": word_freqs}


class RemoveSessionTask(celery.Task):

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db_session.remove()


@app.task(base=RemoveSessionTask)
def store_results(results, article_url, author_name):
    article_name = results["article_name"]
    if not article_name:
        raise Exception("No name found for article")

    logger.info("STORING RESULTS FOR {}".format(article_name))
    session = db_session()

    # store results in db
    article = Article(name=article_name, url=article_url,
                      author=author_name)
    session.add(article)
    word_freqs = results["word_freqs"]
    for word, frequency in word_freqs.items():
        wc = WordCount(word=word, frequency=frequency)
        wc.article = article
        session.add(wc)

    session.commit()

    logger.info("RESULTS STORED FOR {}".format(article_name))
    return article_name


@app.task
def success_handler(article_name):
    print("Processed '{}'".format(article_name))


@app.task
def error_handler(request, exception, traceback):
    parent_id = request.parent_id
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
        parent_id, exception, traceback))
