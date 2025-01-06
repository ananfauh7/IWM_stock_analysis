import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from utils.data_fetcher import fetch_stock_data, fetch_financial_metrics
from utils.price_factors_analyzer import analyze_price_factors
from utils.sentiment_analyzer import analyze_news_sentiment
from utils.market_watch import fetch_market_watch_data
import openai
import os

@st.cache_data(ttl=3600)
def generate_trading_strategy(symbol: str = "IWM") -> dict:
    """
    Generate AI-powered trading strategy recommendations with explanations
    """
    try:
        # Collect all available data
        stock_data = fetch_stock_data(symbol)
        price_factors = analyze_price_factors(symbol)
        sentiment_data = analyze_news_sentiment(symbol)
        market_data = fetch_market_watch_data(symbol)
        
        # Prepare market context
        current_price = stock_data['Close'].iloc[-1]
        daily_return = ((current_price - stock_data['Close'].iloc[-2]) / stock_data['Close'].iloc[-2]) * 100
        
        # Generate market summary for AI context
        market_summary = f"""
        Symbol: {symbol}
        Current Price: ${current_price:.2f}
        Daily Change: {daily_return:.2f}%
        Technical Sentiment: {price_factors['technical_sentiment']}
        RSI: {price_factors['technical_indicators']['rsi']:.2f}
        MACD: {price_factors['technical_indicators']['macd']:.2f}
        News Sentiment Score: {sentiment_data['score']:.2f}
        Analyst Rating: {market_data['Analyst Rating']}
        """
        
        # Generate AI insights using OpenAI
        client = openai.OpenAI()
        prompt = f"""
        Based on the following market data for {symbol}, provide a detailed trading strategy recommendation:
        
        {market_summary}
        
        Please provide:
        1. Overall Strategy (Bullish, Bearish, or Neutral)
        2. Primary Reasons for the Strategy
        3. Risk Factors to Consider
        4. Suggested Position Sizes
        5. Entry and Exit Points
        
        Format the response as a JSON object with these keys: strategy, reasons, risks, position_size, entry_points, exit_points
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional trading strategy analyst."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse AI response
        ai_insights = eval(response.choices[0].message.content)
        
        # Combine all insights
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_data': {
                'current_price': current_price,
                'daily_return': daily_return,
                'technical_indicators': price_factors['technical_indicators'],
                'sentiment_score': sentiment_data['score'],
                'analyst_rating': market_data['Analyst Rating']
            },
            'ai_recommendation': ai_insights,
            'technical_signals': price_factors['market_signals'],
            'recent_news': sentiment_data['recent_news']
        }
        
    except Exception as e:
        st.error(f"Error generating AI strategy: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def get_strategy_confidence_score(market_data: dict) -> float:
    """
    Calculate a confidence score for the AI strategy based on signal alignment
    """
    try:
        score = 0.0
        factors = 0
        
        # Technical indicators alignment
        if market_data['technical_indicators']['rsi'] > 70:
            score += 1 if market_data['ai_recommendation']['strategy'] == 'Bearish' else -1
        elif market_data['technical_indicators']['rsi'] < 30:
            score += 1 if market_data['ai_recommendation']['strategy'] == 'Bullish' else -1
        factors += 1
        
        # Sentiment alignment
        if market_data['sentiment_score'] > 0:
            score += 1 if market_data['ai_recommendation']['strategy'] == 'Bullish' else -1
        elif market_data['sentiment_score'] < 0:
            score += 1 if market_data['ai_recommendation']['strategy'] == 'Bearish' else -1
        factors += 1
        
        # Analyst rating alignment
        if 'Buy' in market_data['analyst_rating']:
            score += 1 if market_data['ai_recommendation']['strategy'] == 'Bullish' else -1
        elif 'Sell' in market_data['analyst_rating']:
            score += 1 if market_data['ai_recommendation']['strategy'] == 'Bearish' else -1
        factors += 1
        
        # Normalize score to 0-100%
        confidence_score = ((score / factors) + 1) * 50
        return min(max(confidence_score, 0), 100)
        
    except Exception as e:
        st.warning(f"Error calculating confidence score: {str(e)}")
        return 50.0  # Return neutral score on error
