import requests
from textblob import TextBlob
import streamlit as st
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def analyze_news_sentiment(symbol: str) -> dict:
    """
    Analyze sentiment from recent news articles
    """
    try:
        # Use NewsAPI to fetch recent news
        # Note: In a production environment, you would use an actual API key
        news_articles = fetch_mock_news(symbol)
        
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        recent_news = []
        
        for article in news_articles:
            blob = TextBlob(article['title'])
            sentiment_score = blob.sentiment.polarity
            
            if sentiment_score > 0:
                positive_count += 1
            elif sentiment_score < 0:
                negative_count += 1
                
            sentiment_scores.append(sentiment_score)
            recent_news.append(article['title'])
        
        average_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        return {
            'score': average_sentiment,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'recent_news': recent_news[:5]  # Return only top 5 news
        }
    except Exception as e:
        return {
            'score': 0,
            'positive_count': 0,
            'negative_count': 0,
            'recent_news': []
        }

def fetch_mock_news(symbol: str) -> list:
    """
    Mock function to generate sample news data
    In production, replace with actual NewsAPI integration
    """
    return [
        {'title': f"{symbol} Reports Strong Quarterly Results"},
        {'title': f"Analysts Upgrade {symbol} Stock Rating"},
        {'title': f"Market Concerns Impact {symbol} Trading"},
        {'title': f"New Product Launch Boosts {symbol} Outlook"},
        {'title': f"{symbol} Announces Strategic Partnership"}
    ]
