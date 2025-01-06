import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import json

@st.cache_data(ttl=3600)
def fetch_google_finance_data(symbol: str) -> dict:
    """
    Fetch additional market data from Google Finance
    """
    try:
        # Base URL for Google Finance
        base_url = f"https://www.google.com/finance/quote/{symbol}:NYSE"
        
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(base_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception("Failed to fetch Google Finance data")

        # Extract relevant information using string parsing
        # Note: This is a simplified version, in production you might want to use proper HTML parsing
        html_content = response.text
        
        # Extract market data
        market_data = {}
        
        # Extract common metrics
        metrics_to_extract = {
            'Beta': r'Beta</div><div class="P6K39c">([0-9.]+)',
            'Dividend yield': r'Dividend yield</div><div class="P6K39c">([0-9.]+)%',
            'Market cap': r'Market cap</div><div class="P6K39c">([\d.]+[BMT])',
        }
        
        for metric, pattern in metrics_to_extract.items():
            try:
                import re
                match = re.search(pattern, html_content)
                if match:
                    market_data[metric] = match.group(1)
                else:
                    market_data[metric] = 'N/A'
            except:
                market_data[metric] = 'N/A'
        
        # Add additional context
        market_data['data_source'] = 'Google Finance'
        market_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return market_data
        
    except Exception as e:
        st.warning(f"Error fetching Google Finance data: {str(e)}")
        return {
            'Beta': 'N/A',
            'Dividend yield': 'N/A',
            'Market cap': 'N/A',
            'data_source': 'Google Finance',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

@st.cache_data(ttl=3600)
def get_related_stocks(symbol: str) -> list:
    """
    Get related stocks from Google Finance
    """
    try:
        # Base URL for Google Finance
        base_url = f"https://www.google.com/finance/quote/{symbol}:NYSE"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(base_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception("Failed to fetch related stocks")

        # Extract related stocks from the HTML
        # This is a simplified version
        related_stocks = []
        
        # Parse HTML to find related stock symbols
        import re
        matches = re.findall(r'NYSE:([A-Z]+)', response.text)
        
        # Remove duplicates and the original symbol
        related_stocks = list(set([m for m in matches if m != symbol]))[:5]
        
        return related_stocks
        
    except Exception as e:
        st.warning(f"Error fetching related stocks: {str(e)}")
        return []
