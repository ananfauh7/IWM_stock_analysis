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
        
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Use trafilatura to fetch and extract content
        downloaded = trafilatura.fetch_url(base_url)
        if not downloaded:
            raise Exception("Failed to fetch MarketWatch data")
            
        content = trafilatura.extract(downloaded)
        
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
            except:
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
        
        # Fetch news content
        downloaded = trafilatura.fetch_url(news_url)
        if not downloaded:
            raise Exception("Failed to fetch MarketWatch news")
            
        content = trafilatura.extract(downloaded)
        
        # Extract news headlines using regex
        news_pattern = r"(?:^|\n)([^.\n]+?(?:stock|shares|company|market|earnings|revenue)[^.\n]+\.)"
        news_matches = re.finditer(news_pattern, content, re.IGNORECASE)
        
        # Get up to 5 most recent news items
        news_items = []
        for match in news_matches:
            if len(news_items) >= 5:
                break
            news_items.append(match.group(1).strip())
        
        return news_items
        
    except Exception as e:
        st.warning(f"Error fetching MarketWatch news: {str(e)}")
        return []
