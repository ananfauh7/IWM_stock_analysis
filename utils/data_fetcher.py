import nasdaqdatalink
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os

# Initialize NASDAQ Data Link
nasdaqdatalink.ApiConfig.api_key = os.environ.get('NASDAQ_API_KEY')

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol: str) -> pd.DataFrame:
    """
    Fetch historical stock data using NASDAQ Data Link
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Get EOD data from NASDAQ
        df = nasdaqdatalink.get(f'EOD/{symbol}', 
                                start_date=start_date.strftime('%Y-%m-%d'),
                                end_date=end_date.strftime('%Y-%m-%d'))

        if df.empty:
            raise Exception("No data found for the given symbol")

        # Rename columns to match our application's expected format
        df = df.rename(columns={
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume',
            'Adj_Close': 'Adj Close'
        })

        # Sort by date ascending
        df = df.sort_index()

        return df
    except Exception as e:
        raise Exception(f"Error fetching stock data: {str(e)}")

@st.cache_data(ttl=3600)
def fetch_financial_metrics(symbol: str) -> dict:
    """
    Fetch key financial metrics using NASDAQ Data Link
    """
    try:
        # Get latest EOD data
        latest_data = nasdaqdatalink.get(f'EOD/{symbol}', rows=1)

        # Get additional metrics from NASDAQ Fundamentals dataset if available
        try:
            fundamentals = nasdaqdatalink.get(f'SHARADAR/SF1/{symbol}', rows=1)
            market_cap = fundamentals.get('marketcap', 0)
            pe_ratio = fundamentals.get('pe', 0)
            eps = fundamentals.get('eps', 0)
        except:
            market_cap = latest_data['Close'] * latest_data['Volume']
            pe_ratio = 0
            eps = 0

        # Calculate metrics
        current_price = latest_data['Close'].iloc[-1]
        previous_close = nasdaqdatalink.get(f'EOD/{symbol}', rows=2)['Close'].iloc[0]
        day_change = ((current_price - previous_close) / previous_close) * 100

        metrics = {
            'current_price': current_price,
            'day_change': day_change,
            'volume': latest_data['Volume'].iloc[-1],
            'Market Cap': market_cap,
            'P/E Ratio': pe_ratio,
            'EPS': eps,
            '52 Week High': latest_data['High'].iloc[-1],
            '52 Week Low': latest_data['Low'].iloc[-1],
            'Average Volume': latest_data['Volume'].iloc[-1]
        }

        return metrics
    except Exception as e:
        raise Exception(f"Error fetching financial metrics: {str(e)}")

@st.cache_data(ttl=3600)
def fetch_options_data(symbol: str) -> dict:
    """
    Fetch options data if available through NASDAQ Data Link
    Note: This is a placeholder as options data might require additional data sources
    """
    try:
        # This is a placeholder for options data
        # In production, you would need to subscribe to NASDAQ's options data feed
        return {}
    except Exception as e:
        st.warning("Options data not available through current data source")
        return {}