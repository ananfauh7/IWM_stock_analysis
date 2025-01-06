import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import trafilatura
import re

@st.cache_data(ttl=3600)
def fetch_market_watch_data(symbol: str) -> dict:
    """
    Fetch additional market data from MarketWatch with fallback to mock data
    """
    try:
        # Base URL for MarketWatch
        base_url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"

        # Enhanced headers with additional browser-like properties
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

        # Development mock data for testing
        mock_data = {
            'Analyst Rating': 'Buy',
            'Price Target': '185.50',
            'Trading Volume': '55.2M',
            'Forward P/E': '25.3',
            'Market Cap': '3.1T',
            '52 Week Range': '124.17 - 199.62',
            'data_source': 'MarketWatch (Mock)',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        response = requests.get(base_url, headers=headers, timeout=15)

        if response.status_code != 200:
            st.warning(f"Using mock data due to failed request (Status: {response.status_code})")
            return mock_data

        # Extract content using trafilatura
        content = trafilatura.extract(response.text)
        if not content:
            st.warning("Using mock data due to content extraction failure")
            return mock_data

        # More flexible regex patterns with optional components
        patterns = {
            'Analyst Rating': r'(?:Analyst|Analysis|Research)\s*Rating\s*(?:is\s*)?[:.]?\s*([\w\s\-]+)',
            'Price Target': r'(?:Price|PT|Target)\s*(?:Target|Price)?\s*[:.]?\s*\$?\s*([\d,.]+)',
            'Trading Volume': r'Volume\s*[:.]?\s*([\d,.]+[KMB]?)',
            'Forward P/E': r'(?:Forward|Fwd)\s*(?:P/E|PE)\s*[:.]?\s*([\d,.]+)',
            'Market Cap': r'Market\s*Cap(?:italization)?\s*[:.]?\s*\$?\s*([\d,.]+[KMB]?)',
            '52 Week Range': r'52[\s-]Week[\s-]Range\s*[:.]?\s*\$?\s*([\d,.]+)\s*[-–]\s*\$?\s*([\d,.]+)'
        }

        market_data = {}

        # Extract data with multiple pattern attempts
        for metric, pattern in patterns.items():
            try:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    if metric == '52 Week Range':
                        market_data[metric] = f"${match.group(1)} - ${match.group(2)}"
                    else:
                        market_data[metric] = match.group(1)
                else:
                    # Fallback to mock data for this metric
                    market_data[metric] = mock_data[metric]
                    st.info(f"Using mock data for {metric}")
            except Exception as e:
                st.warning(f"Error extracting {metric}: {str(e)}")
                market_data[metric] = mock_data[metric]

        # Add metadata
        market_data['data_source'] = 'MarketWatch'
        market_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return market_data

    except Exception as e:
        st.warning(f"Using mock data due to error: {str(e)}")
        return {
            'Analyst Rating': 'Buy',
            'Price Target': '185.50',
            'Trading Volume': '55.2M',
            'Forward P/E': '25.3',
            'Market Cap': '3.1T',
            '52 Week Range': '124.17 - 199.62',
            'data_source': 'MarketWatch (Mock)',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@st.cache_data(ttl=3600)
def get_market_watch_news(symbol: str) -> list:
    """
    Get latest news from MarketWatch with mock data fallback
    """
    try:
        # Mock news data for development
        mock_news = [
            f"{symbol} Reports Strong Quarterly Results",
            f"Analysts Upgrade {symbol} Rating to Buy",
            f"New Product Launch Boosts {symbol} Market Share",
            f"{symbol} Announces Strategic Partnership",
            "Market Outlook: Tech Sector Shows Promise"
        ]

        # News URL for MarketWatch
        news_url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}/news"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(news_url, headers=headers, timeout=15)

        if response.status_code != 200:
            st.warning(f"Using mock news due to failed request (Status: {response.status_code})")
            return mock_news

        content = trafilatura.extract(response.text)
        if not content:
            st.warning("Using mock news due to content extraction failure")
            return mock_news

        # Extract news with more flexible pattern
        news_pattern = r"(?:^|\n)([^.\n]+?(?:stock|shares|company|market|earnings|revenue|announces|reports)[^.\n]+\.)"
        news_matches = re.finditer(news_pattern, content, re.IGNORECASE)

        news_items = []
        for match in news_matches:
            if len(news_items) >= 5:
                break
            news_items.append(match.group(1).strip())

        if not news_items:
            st.info(f"No news found for {symbol}, using mock news")
            return mock_news

        return news_items

    except Exception as e:
        st.warning(f"Using mock news due to error: {str(e)}")
        return [
            f"{symbol} Reports Strong Quarterly Results",
            f"Analysts Upgrade {symbol} Rating to Buy",
            f"New Product Launch Boosts {symbol} Market Share",
            f"{symbol} Announces Strategic Partnership",
            "Market Outlook: Tech Sector Shows Promise"
        ]