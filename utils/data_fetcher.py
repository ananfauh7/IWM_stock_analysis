import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol: str) -> pd.DataFrame:
    """
    Fetch historical stock data using yfinance
    """
    try:
        stock = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            raise Exception("No data found for the given symbol")
            
        return df
    except Exception as e:
        raise Exception(f"Error fetching stock data: {str(e)}")

@st.cache_data(ttl=3600)
def fetch_financial_metrics(symbol: str) -> dict:
    """
    Fetch key financial metrics for the stock
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        metrics = {
            'current_price': info.get('currentPrice', 0),
            'day_change': info.get('regularMarketChangePercent', 0),
            'volume': info.get('volume', 0),
            'Market Cap': info.get('marketCap', 0),
            'P/E Ratio': info.get('trailingPE', 0),
            'EPS': info.get('trailingEps', 0),
            '52 Week High': info.get('fiftyTwoWeekHigh', 0),
            '52 Week Low': info.get('fiftyTwoWeekLow', 0),
            'Average Volume': info.get('averageVolume', 0)
        }
        
        return metrics
    except Exception as e:
        raise Exception(f"Error fetching financial metrics: {str(e)}")
