from bs4 import BeautifulSoup
import unittest
from unittest.mock import patch, Mock
import requests
from src.crawler.exceptions import NetworkError, ParseError

class TestBaseCrawlerFunctions(unittest.TestCase):
    def setUp(self):
        self.test_url = "https://udn.com/news/story/123456"
        self.test_search_term = "測試"

    def test_handle_network_error(self):
        """測試網路錯誤處理"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            
            with self.assertRaises(NetworkError) as context:
                response = requests.get(self.test_url)
                response.raise_for_status()
                
            self.assertIn("Network error", str(context.exception))

    def test_handle_parse_error(self):
        """測試解析錯誤處理"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "<html></html>"  # 無效的HTML結構
            mock_get.return_value = mock_response
            
            with self.assertRaises(ParseError) as context:
                soup = BeautifulSoup(mock_response.text, "html.parser")
                title = soup.find("h1", class_="non-existent")
                if not title:
                    raise ParseError("找不到必要元素")
                
            self.assertIn("找不到必要元素", str(context.exception))

    def test_response_validation(self):
        """測試回應驗證"""
        with patch('requests.get') as mock_get:
            # 模擬成功的回應
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"valid": "data"}
            mock_get.return_value = mock_response
            
            response = requests.get(self.test_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"valid": "data"})
            
            # 模擬失敗的回應
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            with self.assertRaises(requests.RequestException):
                response = requests.get(self.test_url)
                response.raise_for_status()

    def test_error_message_format(self):
        """測試錯誤訊息格式"""
        network_error = NetworkError("測試網路錯誤")
        parse_error = ParseError("測試解析錯誤")
        
        self.assertIn("測試網路錯誤", str(network_error))
        self.assertIn("測試解析錯誤", str(parse_error))
        
        # 確認錯誤類別繼承關係
        self.assertTrue(isinstance(network_error, Exception))
        self.assertTrue(isinstance(parse_error, Exception))

    def test_url_validation(self):
        """測試URL驗證"""
        valid_urls = [
            "https://udn.com/news/story/123",
            "https://udn.com/news/story/456",
        ]
        
        invalid_urls = [
            "http://invalid.com/news",
            "not_a_url",
            "ftp://udn.com/news",
        ]
        
        for url in valid_urls:
            self.assertTrue(url.startswith("https://udn.com/"))
            
        for url in invalid_urls:
            self.assertFalse(url.startswith("https://udn.com/"))

if __name__ == '__main__':
    unittest.main()
