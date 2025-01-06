import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
from utils.data_fetcher import fetch_stock_data, fetch_financial_metrics
from utils.ml_predictor import predict_price_range
from utils.sentiment_analyzer import analyze_news_sentiment
from utils.share_manager import ShareManager
import json

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

        # Display company info and current price
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${metrics['current_price']:.2f}")
        with col2:
            st.metric("Day Change", f"{metrics['day_change']:.2f}%")
        with col3:
            st.metric("Volume", f"{metrics['volume']:,}")

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

        # Annotation and Sharing Section
        st.subheader("📝 Add Insights & Share")

        # Initialize session state for annotations
        if 'annotations' not in st.session_state:
            st.session_state.annotations = []

        # Add new annotation
        with st.expander("Add Annotation"):
            col1, col2 = st.columns([3, 1])
            with col1:
                annotation_text = st.text_area("Enter your insight", key="new_annotation")
            with col2:
                annotation_date = st.date_input("Date", key="annotation_date")

            if st.button("Add Annotation"):
                if annotation_text:
                    # Add annotation to the chart
                    selected_date = annotation_date.strftime('%Y-%m-%d')
                    price_at_date = df_stock.loc[df_stock.index == selected_date]['Close'].iloc[0] if selected_date in df_stock.index.strftime('%Y-%m-%d').tolist() else df_stock['Close'].iloc[-1]

                    fig = ShareManager.save_annotation(fig, annotation_text, selected_date, price_at_date)
                    st.session_state.annotations.append({
                        'text': annotation_text,
                        'date': selected_date,
                        'price': price_at_date
                    })
                    st.experimental_rerun()

        # Display and Share Insights
        if st.session_state.annotations:
            st.subheader("📊 Your Insights")
            for idx, annotation in enumerate(st.session_state.annotations):
                st.write(f"• {annotation['date']}: {annotation['text']}")

            # Generate share link
            if st.button("Generate Share Link"):
                share_code = ShareManager.generate_share_link(
                    stock_symbol,
                    st.session_state.annotations,
                    {**metrics, 'sentiment_score': sentiment['score']}
                )
                st.code(f"Share Code: {share_code}", language="text")
                st.markdown(f"Anyone can use this code to view your annotated insights!")

        # Import shared insights
        with st.expander("Import Shared Insights"):
            shared_code = st.text_input("Enter Share Code")
            if shared_code and st.button("Import"):
                shared_data = ShareManager.decode_share_link(shared_code)
                if shared_data:
                    st.write("Shared Insights:")
                    st.json(shared_data)

                    # Apply shared annotations to the chart
                    for annotation in shared_data['annotations']:
                        fig = ShareManager.save_annotation(
                            fig,
                            annotation['text'],
                            annotation['date'],
                            annotation['price']
                        )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Invalid share code")

        # Financial metrics table
        st.subheader("Key Financial Metrics")
        metrics_df = pd.DataFrame([metrics])
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

        # Sentiment Analysis Details
        st.subheader("Market Sentiment Analysis")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sentiment Score", f"{sentiment['score']:.2f}")
        with col2:
            st.metric("Positive News", sentiment['positive_count'])
        with col3:
            st.metric("Negative News", sentiment['negative_count'])

        # Display recent news
        if sentiment['recent_news']:
            st.subheader("Recent News Headlines")
            for news in sentiment['recent_news']:
                st.write(f"• {news}")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Please enter a valid stock symbol and try again.")

if stock_symbol:
    handle_stock_data()