from sqlalchemy import create_engine, Column, BigInteger, Integer, ForeignKey, String
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Article(Base):
    __tablename__ = "article"

    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    author = Column(String, nullable=False)


class WordCount(Base):
    __tablename__ = "word_count"

    id = Column(BigInteger, primary_key=True)
    word = Column(String, nullable=False)
    frequency = Column(Integer, nullable=False)
    article_id = Column(BigInteger, ForeignKey('article.id'), nullable=False)

    article = relationship("Article", uselist=False, backref='word_counts')

