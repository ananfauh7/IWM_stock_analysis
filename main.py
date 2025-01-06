import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
from utils.data_fetcher import fetch_stock_data, fetch_financial_metrics
from utils.ml_predictor import predict_price_range
from utils.sentiment_analyzer import analyze_news_sentiment
from utils.google_finance import fetch_google_finance_data, get_related_stocks
from utils.market_watch import fetch_market_watch_data, get_market_watch_news

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📈 Stock Analysis Dashboard")
st.markdown("Enter a stock symbol to get comprehensive analysis including price predictions and sentiment analysis.")

# Input for stock symbol
stock_symbol = st.text_input("Enter Stock Symbol (e.g., IWM, GOOGL)", "IWM").upper()

# Error handling wrapper
def handle_stock_data():
    try:
        # Fetch stock data
        df_stock = fetch_stock_data(stock_symbol)
        metrics = fetch_financial_metrics(stock_symbol)
        google_data = fetch_google_finance_data(stock_symbol)
        market_watch_data = fetch_market_watch_data(stock_symbol)
        related_stocks = get_related_stocks(stock_symbol)

        # Display company info and current price
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Current Price", f"${metrics['current_price']:.2f}")
        with col2:
            st.metric("Day Change", f"{metrics['day_change']:.2f}%")
        with col3:
            st.metric("Beta", google_data['Beta'])
        with col4:
            st.metric("Dividend Yield", google_data['Dividend yield'])
        with col5:
            st.metric("Analyst Rating", market_watch_data['Analyst Rating'])

        # Fetch sentiment data
        sentiment = analyze_news_sentiment(stock_symbol)

        # Create subplot with secondary y-axis
        st.subheader("Stock Price & Sentiment Analysis")
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_stock.index,
                open=df_stock['Open'],
                high=df_stock['High'],
                low=df_stock['Low'],
                close=df_stock['Close'],
                name='Stock Price'
            ),
            secondary_y=False
        )

        # Add sentiment overlay if data is available
        if not sentiment['sentiment_data'].empty:
            sentiment_df = sentiment['sentiment_data']
            fig.add_trace(
                go.Scatter(
                    x=sentiment_df['date'],
                    y=sentiment_df['score'],
                    name='Sentiment Score',
                    line=dict(color='purple', width=2),
                    mode='lines+markers'
                ),
                secondary_y=True
            )

        # Update layout
        fig.update_layout(
            title=f"{stock_symbol} Stock Price with Sentiment Overlay",
            yaxis_title="Price (USD)",
            yaxis2_title="Sentiment Score",
            xaxis_title="Date",
            template="plotly_white"
        )

        # Set y-axes ranges
        fig.update_yaxes(title_text="Price", secondary_y=False)
        fig.update_yaxes(title_text="Sentiment Score", secondary_y=True, range=[-1, 1])

        st.plotly_chart(fig, use_container_width=True)

        # Financial metrics table
        st.subheader("Key Financial Metrics")

        # Combine metrics from all sources
        combined_metrics = {
            **metrics,
            'Beta': google_data['Beta'],
            'Dividend Yield': google_data['Dividend yield'],
            'Google Finance Market Cap': google_data['Market cap'],
            'MarketWatch Price Target': market_watch_data['Price Target'],
            'MarketWatch Forward P/E': market_watch_data['Forward P/E'],
            'MarketWatch Market Cap': market_watch_data['Market Cap'],
            'MarketWatch 52 Week Range': market_watch_data['52 Week Range']
        }

        metrics_df = pd.DataFrame([combined_metrics])
        st.table(metrics_df.T)

        # Download button for CSV
        csv = df_stock.to_csv(index=True)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{stock_symbol}_stock_data.csv">Download Stock Data CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

        # Price prediction
        st.subheader("Price Prediction (Next Day)")
        predicted_range = predict_price_range(df_stock)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Predicted Low", f"${predicted_range['low']:.2f}")
        with col2:
            st.metric("Predicted High", f"${predicted_range['high']:.2f}")

        # Display news from both sources
        st.subheader("Market News")

        # Create tabs for different news sources
        news_tab1, news_tab2 = st.tabs(["Sentiment Analysis", "MarketWatch News"])

        with news_tab1:
            if sentiment['recent_news']:
                for news in sentiment['recent_news']:
                    st.write(f"• {news}")

        with news_tab2:
            market_watch_news = get_market_watch_news(stock_symbol)
            if market_watch_news:
                for news in market_watch_news:
                    st.write(f"• {news}")

        # Display related stocks
        if related_stocks:
            st.subheader("Related Stocks")
            for related in related_stocks:
                st.write(f"• {related}")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Please enter a valid stock symbol and try again.")

if stock_symbol:
    handle_stock_data()