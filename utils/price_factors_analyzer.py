import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from utils.data_fetcher import fetch_stock_data
from utils.sentiment_analyzer import analyze_news_sentiment

@st.cache_data(ttl=3600)
def analyze_price_factors(symbol: str = "IWM") -> dict:
    """
    Analyze various factors affecting the price of IWM
    """
    try:
        # Get historical data
        df = fetch_stock_data(symbol)
        if df.empty:
            raise Exception("No data available")

        # Calculate technical indicators
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()

        # Moving Averages
        sma_20 = df['Close'].rolling(window=20).mean()
        sma_50 = df['Close'].rolling(window=50).mean()
        sma_200 = df['Close'].rolling(window=200).mean()

        # Volume analysis
        avg_volume = df['Volume'].mean()
        volume_trend = 'Increasing' if df['Volume'].iloc[-5:].mean() > avg_volume else 'Decreasing'

        # Get sentiment data
        sentiment = analyze_news_sentiment(symbol)

        # Technical Analysis Summary
        current_price = df['Close'].iloc[-1]
        ma_signals = []
        if current_price > sma_20.iloc[-1]:
            ma_signals.append("Above 20-day MA (Bullish)")
        else:
            ma_signals.append("Below 20-day MA (Bearish)")
        
        if current_price > sma_50.iloc[-1]:
            ma_signals.append("Above 50-day MA (Bullish)")
        else:
            ma_signals.append("Below 50-day MA (Bearish)")

        if macd.iloc[-1] > signal.iloc[-1]:
            ma_signals.append("MACD Above Signal (Bullish)")
        else:
            ma_signals.append("MACD Below Signal (Bearish)")

        # Determine overall technical sentiment
        bullish_count = sum(1 for signal in ma_signals if "Bullish" in signal)
        bearish_count = sum(1 for signal in ma_signals if "Bearish" in signal)
        technical_sentiment = "Bullish" if bullish_count > bearish_count else "Bearish"

        return {
            'technical_indicators': {
                'rsi': rsi.iloc[-1],
                'macd': macd.iloc[-1],
                'macd_signal': signal.iloc[-1],
                'sma_20': sma_20.iloc[-1],
                'sma_50': sma_50.iloc[-1],
                'sma_200': sma_200.iloc[-1],
                'volume_trend': volume_trend
            },
            'price_action': {
                'current_price': current_price,
                'daily_change': ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100),
                'weekly_change': ((current_price - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100) if len(df) >= 5 else 0,
                'monthly_change': ((current_price - df['Close'].iloc[-20]) / df['Close'].iloc[-20] * 100) if len(df) >= 20 else 0
            },
            'market_signals': ma_signals,
            'technical_sentiment': technical_sentiment,
            'news_sentiment': sentiment,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        st.error(f"Error analyzing price factors: {str(e)}")
        return {}
