import pytest
from unittest.mock import patch, MagicMock
import os
import requests
import json
from bs4 import BeautifulSoup

from src.utils.services import Services


class TestServices:
    """Tests for the Services class"""
    
    @patch('src.utils.services.requests.get')
    @patch('src.utils.services.os.getenv')
    def test_get_weather_success(self, mock_getenv, mock_get):
        """Test get_weather with successful API response"""
        # Mock environment variable
        mock_getenv.return_value = "fake_api_key"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'main': {
                'temp': 20.5,
                'feels_like': 19.8,
                'humidity': 65
            },
            'wind': {
                'speed': 5.2
            }
        }
        mock_get.return_value = mock_response
        
        # Call the method
        result = Services.get_weather("Moscow")
        
        # Verify the API was called with correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://api.openweathermap.org/data/2.5/weather"
        assert kwargs['params']['q'] == "Moscow"
        assert kwargs['params']['appid'] == "fake_api_key"
        assert kwargs['params']['units'] == "metric"
        assert kwargs['params']['lang'] == "ru"
        
        # Check the result
        assert "Погода в Moscow" in result
        assert "Температура: 20.5°C" in result
        assert "Ощущается как: 19.8°C" in result
        assert "Влажность: 65%" in result
        assert "Ветер: 5.2 м/с" in result
    
    @patch('src.utils.services.requests.get')
    @patch('src.utils.services.os.getenv')
    def test_get_weather_error(self, mock_getenv, mock_get):
        """Test get_weather with API error"""
        # Mock environment variable
        mock_getenv.return_value = "fake_api_key"
        
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        # Call the method
        result = Services.get_weather("InvalidCity")
        
        # Check the result
        assert "Не удалось получить погоду для InvalidCity" in result
    
    @patch('src.utils.services.requests.get')
    def test_get_exchange_rates_success(self, mock_get):
        """Test get_exchange_rates with successful API responses"""
        # Mock API responses
        def mock_get_response(url, **kwargs):
            mock_response = MagicMock()
            
            if "exchangerate-api.com" in url:
                mock_response.json.return_value = {
                    'rates': {'RUB': 75.5}
                }
            elif "cryptocompare.com" in url:
                mock_response.json.return_value = {
                    'BTC': {'USD': 50000},
                    'ETH': {'USD': 3000},
                    'TON': {'USD': 5}
                }
            
            return mock_response
        
        mock_get.side_effect = mock_get_response
        
        # Call the method
        result = Services.get_exchange_rates()
        
        # Verify the APIs were called
        assert mock_get.call_count == 2
        
        # Check the result
        assert "Курсы:" in result
        assert "USD/RUB: 75.50" in result
        assert "BTC: $50000" in result
        assert "ETH: $3000" in result
        assert "TON: $5" in result
    
    @patch('src.utils.services.requests.get')
    def test_get_exchange_rates_error(self, mock_get):
        """Test get_exchange_rates with API error"""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        # Call the method
        result = Services.get_exchange_rates()
        
        # Check the result
        assert "Не удалось получить курсы валют" in result
    
    @patch('src.utils.services.requests.get')
    def test_get_horoscope_success(self, mock_get):
        """Test get_horoscope with successful API response"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.content = """
        <html>
            <main itemprop="articleBody">
                <div class="b6a5d4949c">
                    <p>Первый параграф гороскопа.</p>
                    <p>Второй параграф гороскопа.</p>
                </div>
            </main>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call the method
        result = Services.get_horoscope("овен")
        
        # Verify the API was called with correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "horo.mail.ru/prediction/aries/today/" in args[0]
        
        # Check the result
        assert "Гороскоп для овен на сегодня" in result
        assert "Первый параграф гороскопа." in result
        assert "Второй параграф гороскопа." in result
    
    @patch('src.utils.services.requests.get')
    def test_get_horoscope_no_content(self, mock_get):
        """Test get_horoscope with no content found"""
        # Mock API response with no matching content
        mock_response = MagicMock()
        mock_response.content = """
        <html>
            <main itemprop="articleBody">
                <div class="different-class">
                    <p>Какой-то текст.</p>
                </div>
            </main>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Call the method
        result = Services.get_horoscope("овен")
        
        # Check the result
        assert "Не удалось найти текст гороскопа для овен" in result
    
    @patch('src.utils.services.requests.get')
    def test_get_horoscope_error(self, mock_get):
        """Test get_horoscope with API error"""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        # Call the method
        result = Services.get_horoscope("овен")
        
        # Check the result
        assert "Не удалось получить гороскоп для овен" in result
    
    @patch('src.utils.services.random.choice')
    def test_get_daily_quote(self, mock_choice):
        """Test get_daily_quote"""
        # Mock random.choice to return a specific quote
        mock_choice.return_value = "Ваше здоровье — ваше богатство."
        
        # Call the method
        result = Services.get_daily_quote()
        
        # Check the result
        assert "Цитата дня:" in result
        assert "Ваше здоровье — ваше богатство." in result
