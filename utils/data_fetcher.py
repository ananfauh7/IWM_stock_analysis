import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol: str) -> pd.DataFrame:
    """
    Fetch historical stock data using Yahoo Finance
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Get data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            raise Exception("No data found for the given symbol")

        # Ensure we have all required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            raise Exception("Required price columns not available in the data")

        # Sort by date ascending
        df = df.sort_index()
        return df

    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        # Return empty DataFrame with correct columns for graceful failure
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])

@st.cache_data(ttl=3600)
def fetch_financial_metrics(symbol: str) -> dict:
    """
    Fetch key financial metrics using Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Get latest stock data
        df = fetch_stock_data(symbol)
        if df.empty:
            raise Exception("No data available")

        # Calculate basic metrics
        current_price = df['Close'].iloc[-1]
        previous_close = df['Close'].iloc[-2] if len(df) > 1 else current_price
        day_change = ((current_price - previous_close) / previous_close) * 100
        volume = df['Volume'].iloc[-1]

        # Get additional metrics from Yahoo Finance
        market_cap = info.get('marketCap', current_price * volume)
        pe_ratio = info.get('trailingPE', 0)
        eps = info.get('trailingEps', 0)

        metrics = {
            'current_price': current_price,
            'day_change': day_change,
            'volume': volume,
            'Market Cap': market_cap,
            'P/E Ratio': pe_ratio,
            'EPS': eps,
            '52 Week High': df['High'].max(),
            '52 Week Low': df['Low'].min(),
            'Average Volume': df['Volume'].mean()
        }

        return metrics
    except Exception as e:
        st.error(f"Error fetching financial metrics: {str(e)}")
        return {
            'current_price': 0,
            'day_change': 0,
            'volume': 0,
            'Market Cap': 0,
            'P/E Ratio': 0,
            'EPS': 0,
            '52 Week High': 0,
            '52 Week Low': 0,
            'Average Volume': 0
        }

@st.cache_data(ttl=3600)
def fetch_options_data(symbol: str) -> dict:
    """
    Fetch options data from Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        # Get options data
        options = ticker.options

        if options:
            # Get the nearest expiration date's options chain
            chain = ticker.option_chain(options[0])
            return {
                'calls': chain.calls.to_dict('records'),
                'puts': chain.puts.to_dict('records'),
                'expiration_dates': options
            }
        return {}
    except Exception as e:
        st.warning("Options data not available")
        return {}