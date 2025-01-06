import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.price_factors_analyzer import analyze_price_factors
import pandas as pd

st.set_page_config(
    page_title="IWM Price Factors Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("📊 IWM Price Factors Analysis")
st.markdown("""
This page analyzes various factors affecting IWM's price movement, including:
- Technical Indicators
- Market Sentiment
- Price Action Analysis
- News Impact
""")

# Get price factors analysis
analysis = analyze_price_factors("IWM")

if analysis:
    # Technical Analysis Section
    st.header("Technical Analysis")

    # Create three columns for technical indicators
    col1, col2, col3 = st.columns(3)

    with col1:
        rsi_value = analysis['technical_indicators']['rsi']
        st.metric("RSI (14)", f"{rsi_value:.2f}", 
                 delta="Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral",
                 delta_color="inverse" if rsi_value > 70 else "normal" if rsi_value < 30 else "off")

    with col2:
        macd = analysis['technical_indicators']['macd']
        macd_signal = analysis['technical_indicators']['macd_signal']
        st.metric("MACD", f"{macd:.2f}", 
                 delta=f"Signal: {macd_signal:.2f}",
                 delta_color="normal" if macd > macd_signal else "inverse")

    with col3:
        volume_trend = analysis['technical_indicators']['volume_trend']
        st.metric("Volume Trend", volume_trend,
                 delta="Above Average" if volume_trend == "Increasing" else "Below Average",
                 delta_color="normal" if volume_trend == "Increasing" else "inverse")

    # Moving Averages
    st.subheader("Moving Averages")
    ma_df = pd.DataFrame({
        'Indicator': ['20-day MA', '50-day MA', '200-day MA'],
        'Value': [
            analysis['technical_indicators']['sma_20'],
            analysis['technical_indicators']['sma_50'],
            analysis['technical_indicators']['sma_200']
        ]
    })
    st.dataframe(ma_df)

    # Market Signals
    st.header("Market Signals")
    for signal in analysis['market_signals']:
        st.write(f"• {signal}")

    # Overall Technical Sentiment
    st.subheader("Technical Sentiment")
    sentiment_color = "#00FF00" if analysis['technical_sentiment'] == "Bullish" else "#FF0000"
    st.markdown(f"<h3 style='color: {sentiment_color};'>{analysis['technical_sentiment']}</h3>", 
               unsafe_allow_html=True)

    # News Sentiment Analysis
    st.header("News Sentiment")

    # Create columns for sentiment metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        sentiment_score = analysis['news_sentiment']['score']
        st.metric("Sentiment Score", f"{sentiment_score:.2f}",
                 delta="Positive" if sentiment_score > 0 else "Negative",
                 delta_color="normal" if sentiment_score > 0 else "inverse")
    with col2:
        st.metric("Positive News Count", analysis['news_sentiment']['positive_count'])
    with col3:
        st.metric("Negative News Count", analysis['news_sentiment']['negative_count'])

    # Recent News
    st.subheader("Recent News Impact")
    news_items = analysis['news_sentiment']['recent_news']
    for news in news_items:
        st.write(f"• {news}")

    # Price Action
    st.header("Price Action")
    price_data = analysis['price_action']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Daily Change", f"{price_data['daily_change']:.2f}%",
                 delta_color="normal" if price_data['daily_change'] > 0 else "inverse")
    with col2:
        st.metric("Weekly Change", f"{price_data['weekly_change']:.2f}%",
                 delta_color="normal" if price_data['weekly_change'] > 0 else "inverse")
    with col3:
        st.metric("Monthly Change", f"{price_data['monthly_change']:.2f}%",
                 delta_color="normal" if price_data['monthly_change'] > 0 else "inverse")

    # Last Updated
    st.sidebar.info(f"Last Updated: {analysis['last_updated']}")

else:
    st.error("Unable to fetch price factors analysis. Please try again later.")