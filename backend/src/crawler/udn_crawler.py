"""
UDN News Scraper Module

This module provides the UDNCrawler class for fetching, parsing, and saving news articles from the UDN website.
The class extends the NewsCrawlerBase and includes functionalities to search for news articles based on a search term,
parse the details of individual articles, and save them to a database using SQLAlchemy ORM.

Classes:
    UDNCrawler: A class to scrape news from UDN.

Exceptions:
    DomainMismatchException: Raised when the URL domain does not match the expected domain for the crawler.

Usage Example:
    crawler = UDNCrawler(timeout=10)
    headlines = crawler.startup("technology")
    for headline in headlines:
        news = crawler.parse(headline.url)
        crawler.save(news, db_session)

UDNCrawler Methods:
    __init__(self, timeout: int = 5): Initializes the crawler with a default timeout for HTTP requests.
    startup(self, search_term: str) -> list[Headline]: Fetches news headlines for a given search term across multiple pages.
    get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]: Fetches news headlines for specified pages.
    _fetch_news(self, page: int, search_term: str) -> list[Headline]: Helper method to fetch news headlines for a specific page.
    _create_search_params(self, page: int, search_term: str): Creates the parameters for the search request.
    _perform_request(self, params: dict): Performs the HTTP request to fetch news data.
    _parse_headlines(response): Parses the response to extract headlines.
    parse(self, url: str) -> News: Parses a news article from a given URL.
    _extract_news(soup, url: str) -> News: Extracts news details from the BeautifulSoup object.
    save(self, news: News, db: Session): Saves a news article to the database.
    _commit_changes(db: Session): Commits the changes to the database with error handling.
"""

from requests import Response
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from .crawler_base import NewsCrawlerBase, Headline, News, NewsWithSummary
from ..config import INITIAL_FETCH_PAGE_RANGE
from urllib.parse import quote
import requests

class UDNCrawler(NewsCrawlerBase):
    CHANNEL_ID = 2

    def __init__(self, timeout: int = 5) -> None:
        self.news_website_url = "https://udn.com/api/more"
        self.timeout = timeout

    def startup(self, search_term: str) -> list[Headline]:
        """
        Initializes the application by fetching news headlines for a given search term across multiple pages.
        This method is typically called at the beginning of the program when there is no data available,
        hence it fetches headlines from the first 10 pages.

        :param search_term: The term to search for in news headlines.
        :return: A list of Headline namedtuples containing the title and URL of news articles.
        :rtype: list[Headline]
        """
        return self.get_headline(search_term, page=(1, 10))

    def get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]:
        page_range = range(*page) if isinstance(page, tuple) else [page]
        headlines = []
        for p in page_range:
            headlines.extend(self._fetch_news(p, search_term))
        return headlines

    def _fetch_news(self, page: int, search_term: str) -> list[Headline]:
        params = self._create_search_params(page, search_term)
        response = self._perform_request(params=params)
        return self._parse_headlines(response)

    def _create_search_params(self, page: int, search_term: str) -> dict:
        return {
            "page": page,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> Response:
        base_url = "https://udn.com/api/more"
        try:
            response = requests.get(url or base_url, params=params, timeout=self.timeout)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
            return response
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch news data: {e}")

    @staticmethod
    def _parse_headlines(response: Response) -> list[Headline]:
        try:
            data = response.json()
            headlines = [
                Headline(url=item["titleLink"], title=item["title"], time=item["time"])
                for item in data.get("lists", [])
            ]
            return headlines
        except (ValueError, KeyError) as e:
            raise RuntimeError(f"Failed to parse headlines: {e}")

    def parse(self, url: str) -> News:
        response = self._perform_request(url=url)
        soup = BeautifulSoup(response.text, "html.parser")
        return self._extract_news(soup, url)

    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        title = soup.find("h1", class_="article-content__title").text.strip()
        time = soup.find("time", class_="article-content__time").text.strip()
        content_section = soup.find("section", class_="article-content__editor")
        paragraphs = [
            p.text.strip() for p in content_section.find_all("p")
            if p.text.strip() and "▪" not in p.text
        ]   
        return News(url=url, title=title, time=time, content=paragraphs)

    def save(self, news: NewsWithSummary, db: Session):
        db.add(news)
        self._commit_changes(db)

    @staticmethod
    def _commit_changes(db: Session):
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to commit changes to the database: {e}")
        
## Unit Test