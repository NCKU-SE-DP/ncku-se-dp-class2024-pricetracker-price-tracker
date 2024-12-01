class CrawlerException(Exception):
    """爬蟲基礎例外類別"""
    pass

class ParseError(CrawlerException):
    """解析錯誤"""
    pass

class NetworkError(CrawlerException):
    """網路連線錯誤"""
    pass
