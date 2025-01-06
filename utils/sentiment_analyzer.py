import requests
from textblob import TextBlob
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

@st.cache_data(ttl=3600)
def analyze_news_sentiment(symbol: str, days: int = 30) -> dict:
    """
    Analyze sentiment from recent news articles with timestamps
    """
    try:
        # Generate mock news data with timestamps
        news_data = fetch_mock_news(symbol, days)

        sentiment_scores = []
        positive_count = 0
        negative_count = 0

        # Process each news article
        for article in news_data:
            blob = TextBlob(article['title'])
            sentiment_score = blob.sentiment.polarity

            if sentiment_score > 0:
                positive_count += 1
            elif sentiment_score < 0:
                negative_count += 1

            sentiment_scores.append({
                'date': article['date'],
                'score': sentiment_score,
                'title': article['title']
            })

        # Calculate average sentiment
        average_sentiment = sum(s['score'] for s in sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        # Convert to DataFrame for easier plotting
        df_sentiment = pd.DataFrame(sentiment_scores)

        return {
            'score': average_sentiment,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'sentiment_data': df_sentiment,
            'recent_news': [s['title'] for s in sentiment_scores[:5]]
        }
    except Exception as e:
        return {
            'score': 0,
            'positive_count': 0,
            'negative_count': 0,
            'sentiment_data': pd.DataFrame(),
            'recent_news': []
        }

def fetch_mock_news(symbol: str, days: int) -> list:
    """
    Mock function to generate sample news data with timestamps
    In production, replace with actual NewsAPI integration
    """
    news_data = []
    end_date = datetime.now()

    # Generate mock news entries for the past n days
    for i in range(days):
        date = end_date - timedelta(days=i)
        sentiment = 'positive' if i % 3 == 0 else 'negative' if i % 3 == 1 else 'neutral'

        title = {
            'positive': f"{symbol} Reports Strong Results on {date.strftime('%Y-%m-%d')}",
            'negative': f"Market Concerns Impact {symbol} on {date.strftime('%Y-%m-%d')}",
            'neutral': f"{symbol} Maintains Stable Position on {date.strftime('%Y-%m-%d')}"
        }[sentiment]

        news_data.append({
            'date': date,
            'title': title
        })

    return news_data