from abc import ABC, abstractmethod

class BaseCrawler(ABC):
    @abstractmethod
    def get_news_list(self, search_term: str, is_initial: bool = False) -> list:
        pass
        
    @abstractmethod
    def get_article_content(self, url: str) -> tuple:
        pass
