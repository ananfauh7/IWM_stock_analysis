import quandl
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os

# Initialize Quandl (NASDAQ Data Link)
quandl.ApiConfig.api_key = os.environ.get('NASDAQ_API_KEY')

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol: str) -> pd.DataFrame:
    """
    Fetch historical stock data using NASDAQ Data Link (Quandl)
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Get EOD data from NASDAQ/Quandl
        try:
            df = quandl.get(f'WIKI/{symbol}', 
                           start_date=start_date.strftime('%Y-%m-%d'),
                           end_date=end_date.strftime('%Y-%m-%d'))

            st.info(f"Successfully connected to Quandl API for {symbol}")
        except Exception as api_error:
            st.warning(f"WIKI database not accessible, trying FRED database for {symbol}")
            try:
                df = quandl.get(f'FRED/{symbol}', 
                               start_date=start_date.strftime('%Y-%m-%d'),
                               end_date=end_date.strftime('%Y-%m-%d'))
            except Exception as fred_error:
                st.error(f"Error accessing FRED database: {str(fred_error)}")
                raise Exception(f"Could not fetch data from any available source: {str(api_error)}")

        if df.empty:
            raise Exception("No data found for the given symbol")

        # Ensure we have all required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            # If using FRED data, we might only have 'Close' prices
            if 'Close' in df.columns:
                df['Open'] = df['Close']
                df['High'] = df['Close']
                df['Low'] = df['Close']
                df['Volume'] = 0
            else:
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
    Fetch key financial metrics using NASDAQ Data Link
    """
    try:
        # Get latest stock data
        df = fetch_stock_data(symbol)
        if df.empty:
            raise Exception("No data available")

        # Calculate basic metrics from available data
        current_price = df['Close'].iloc[-1]
        previous_close = df['Close'].iloc[-2] if len(df) > 1 else current_price
        day_change = ((current_price - previous_close) / previous_close) * 100
        volume = df['Volume'].iloc[-1]

        # Calculate additional metrics
        fifty_two_week_high = df['High'].max()
        fifty_two_week_low = df['Low'].min()
        avg_volume = df['Volume'].mean()

        metrics = {
            'current_price': current_price,
            'day_change': day_change,
            'volume': volume,
            'Market Cap': current_price * volume,  # Simplified market cap calculation
            'P/E Ratio': 0,  # Not available without fundamental data
            'EPS': 0,  # Not available without fundamental data
            '52 Week High': fifty_two_week_high,
            '52 Week Low': fifty_two_week_low,
            'Average Volume': avg_volume
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