import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import trafilatura
import re

@st.cache_data(ttl=3600)
def fetch_market_watch_data(symbol: str) -> dict:
    """
    Fetch additional market data from MarketWatch
    """
    try:
        # Base URL for MarketWatch
        base_url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"

        # Enhanced headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        # Use requests first to get the raw HTML
        response = requests.get(base_url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch MarketWatch data: Status code {response.status_code}")

        # Use trafilatura to extract readable content
        content = trafilatura.extract(response.text)
        if not content:
            raise Exception("No content could be extracted from MarketWatch")

        # Extract market data using regex patterns
        market_data = {}

        # Common patterns to extract from MarketWatch
        patterns = {
            'Analyst Rating': r'Analyst Rating:\s*([\w\s]+)',
            'Price Target': r'Price Target:\s*\$?([\d.]+)',
            'Trading Volume': r'Volume:\s*([\d,]+)',
            'Forward P/E': r'Forward P/E:\s*([\d.]+)',
            'Market Cap': r'Market Cap\s*\$?([\d.]+[BMT])',
            '52 Week Range': r'52 Week Range:\s*\$?([\d.]+)\s*-\s*\$?([\d.]+)'
        }

        # Extract data with enhanced error handling
        for metric, pattern in patterns.items():
            try:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    if metric == '52 Week Range':
                        market_data[metric] = f"${match.group(1)} - ${match.group(2)}"
                    else:
                        market_data[metric] = match.group(1)
                else:
                    market_data[metric] = 'N/A'
            except Exception as e:
                st.warning(f"Error extracting {metric}: {str(e)}")
                market_data[metric] = 'N/A'

        # Add data source and timestamp
        market_data['data_source'] = 'MarketWatch'
        market_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return market_data

    except Exception as e:
        st.warning(f"Error fetching MarketWatch data: {str(e)}")
        return {
            'Analyst Rating': 'N/A',
            'Price Target': 'N/A',
            'Trading Volume': 'N/A',
            'Forward P/E': 'N/A',
            'Market Cap': 'N/A',
            '52 Week Range': 'N/A',
            'data_source': 'MarketWatch',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@st.cache_data(ttl=3600)
def get_market_watch_news(symbol: str) -> list:
    """
    Get latest news from MarketWatch
    """
    try:
        # News URL for MarketWatch
        news_url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}/news"

        # Enhanced headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Use requests to get the raw HTML
        response = requests.get(news_url, headers=headers, timeout=10)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch MarketWatch news: Status code {response.status_code}")

        # Use trafilatura for content extraction
        content = trafilatura.extract(response.text)
        if not content:
            raise Exception("No news content could be extracted")

        # Extract news headlines with improved regex
        # Look for sentences containing stock-related keywords
        news_pattern = r"(?:^|\n)([^.\n]+?(?:stock|shares|company|market|earnings|revenue)[^.\n]+\.)"
        news_matches = re.finditer(news_pattern, content, re.IGNORECASE)

        # Get up to 5 most recent news items
        news_items = []
        for match in news_matches:
            if len(news_items) >= 5:
                break
            news_items.append(match.group(1).strip())

        if not news_items:
            st.info(f"No recent news found for {symbol}")

        return news_items

    except Exception as e:
        st.warning(f"Error fetching MarketWatch news: {str(e)}")
        return []