# article-scraper

Takes a name in the format firstname_lastname (e.g. John Gray would be given as john_gray), and triggers asynchronous tasks for retrieving all the word counts for an author's first page of articles.

Requires Redis as the results backend, RabbitMQ as the message broker.
