import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from utils.data_fetcher import fetch_stock_data
from utils.sentiment_analyzer import analyze_news_sentiment

def get_black_swan_events() -> list:
    """
    Returns a list of significant market events that affected IWM
    """
    return [
        {
            'event': 'COVID-19 Market Crash',
            'date': '2020-03-23',
            'price_impact': -41.2,  # Percentage decline from peak
            'volatility_impact': 78.4,  # VIX peak
            'recovery_days': 145,
            'description': 'Global pandemic caused unprecedented market volatility'
        },
        {
            'event': '2008 Financial Crisis',
            'date': '2008-10-10',
            'price_impact': -59.7,
            'volatility_impact': 89.5,
            'recovery_days': 755,
            'description': 'Banking system collapse led to prolonged bear market'
        },
        {
            'event': 'Flash Crash',
            'date': '2010-05-06',
            'price_impact': -8.9,
            'volatility_impact': 42.1,
            'recovery_days': 4,
            'description': 'Algorithmic trading caused brief market dislocation'
        },
        {
            'event': 'Brexit Vote',
            'date': '2016-06-24',
            'price_impact': -12.4,
            'volatility_impact': 25.8,
            'recovery_days': 51,
            'description': 'UK vote to leave EU sparked global uncertainty'
        },
        {
            'event': 'US Credit Downgrade',
            'date': '2011-08-05',
            'price_impact': -18.2,
            'volatility_impact': 48.0,
            'recovery_days': 157,
            'description': 'S&P downgraded US credit rating from AAA'
        }
    ]

def analyze_current_volatility_regime(df: pd.DataFrame) -> dict:
    """
    Analyze current market conditions compared to historical black swan events
    """
    try:
        # Calculate current volatility metrics
        current_volatility = df['Close'].pct_change().std() * np.sqrt(252)
        rolling_vol = df['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)

        # Get maximum drawdown
        rolling_max = df['Close'].rolling(window=252, min_periods=1).max()
        drawdown = (df['Close'] - rolling_max) / rolling_max
        current_drawdown = drawdown.iloc[-1]

        # Compare with black swan events
        events = get_black_swan_events()
        avg_black_swan_vol = np.mean([event['volatility_impact'] for event in events]) / 100
        avg_price_impact = np.mean([event['price_impact'] for event in events])

        # Determine current regime
        vol_percentile = (current_volatility - rolling_vol.min()) / (rolling_vol.max() - rolling_vol.min())
        regime = 'High Volatility' if vol_percentile > 0.7 else 'Low Volatility' if vol_percentile < 0.3 else 'Normal'

        return {
            'current_volatility': current_volatility,
            'historical_avg_volatility': rolling_vol.mean(),
            'current_drawdown': current_drawdown * 100,  # Convert to percentage
            'volatility_regime': regime,
            'comparison_to_black_swans': {
                'current_vol_vs_avg_black_swan': (current_volatility / avg_black_swan_vol) * 100,
                'current_drawdown_vs_avg_impact': (abs(current_drawdown * 100) / abs(avg_price_impact)) * 100
            },
            'black_swan_events': events,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        st.error(f"Error analyzing volatility regime: {str(e)}")
        return {}

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

        # Get volatility regime analysis
        volatility_analysis = analyze_current_volatility_regime(df)

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
            'volatility_analysis': volatility_analysis,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        st.error(f"Error analyzing price factors: {str(e)}")
        return {}