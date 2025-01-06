import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from utils.data_fetcher import fetch_stock_data, fetch_financial_metrics
from utils.price_factors_analyzer import analyze_price_factors
from utils.sentiment_analyzer import analyze_news_sentiment
from utils.market_watch import fetch_market_watch_data, get_market_watch_news
import openai
import os
import json

@st.cache_data(ttl=3600)
def analyze_weekly_sentiment(symbol: str) -> dict:
    """
    Analyze sentiment trends over the past week
    """
    try:
        sentiment_data = analyze_news_sentiment(symbol, days=7)
        market_news = get_market_watch_news(symbol)

        # Combine news from both sources
        all_news = sentiment_data.get('recent_news', []) + market_news

        # Calculate weekly sentiment metrics
        return {
            'weekly_score': sentiment_data.get('score', 0),
            'positive_ratio': sentiment_data.get('positive_count', 0) / 
                            (sentiment_data.get('positive_count', 0) + sentiment_data.get('negative_count', 1)),
            'news_volume': len(all_news),
            'key_headlines': all_news[:5]  # Most recent 5 headlines
        }
    except Exception as e:
        st.warning(f"Error analyzing weekly sentiment: {str(e)}")
        return {
            'weekly_score': 0,
            'positive_ratio': 0.5,
            'news_volume': 0,
            'key_headlines': []
        }

@st.cache_data(ttl=3600)
def generate_trading_strategy(symbol: str = "IWM") -> dict:
    """
    Generate AI-powered trading strategy recommendations with explanations
    """
    try:
        # Check if OpenAI API key is available
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return {
                'error': 'OpenAI API key is not configured. Please provide the API key to enable AI-powered recommendations.',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        # Initialize OpenAI client with the API key
        client = openai.OpenAI(api_key=api_key)

        # Collect all available data
        stock_data = fetch_stock_data(symbol)
        if stock_data.empty:
            return {
                'error': 'No stock data available',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        # Get all required data with error handling
        try:
            price_factors = analyze_price_factors(symbol)
            weekly_sentiment = analyze_weekly_sentiment(symbol)
            market_data = fetch_market_watch_data(symbol)
        except Exception as e:
            st.warning(f"Some data sources unavailable: {str(e)}")
            return {
                'error': 'Unable to fetch all required data for analysis',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        # Generate market summary for AI context
        market_summary = f"""
        Symbol: {symbol}
        Current Price: ${stock_data['Close'].iloc[-1]:.2f}
        Daily Change: {((stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2]) / stock_data['Close'].iloc[-2] * 100):.2f}%
        Technical Sentiment: {price_factors.get('technical_sentiment', 'Neutral')}
        RSI: {price_factors.get('technical_indicators', {}).get('rsi', 0):.2f}
        MACD: {price_factors.get('technical_indicators', {}).get('macd', 0):.2f}

        Weekly News Sentiment Analysis:
        - Overall Sentiment Score: {weekly_sentiment['weekly_score']:.2f}
        - Positive News Ratio: {weekly_sentiment['positive_ratio']*100:.1f}%
        - News Volume: {weekly_sentiment['news_volume']} articles
        - Key Headlines: {', '.join(weekly_sentiment['key_headlines'][:3])}

        Market Analysis:
        - Analyst Rating: {market_data.get('Analyst Rating', 'N/A')}
        - Price Target: {market_data.get('Price Target', 'N/A')}
        """

        # Generate AI insights using OpenAI with enhanced prompt
        prompt = f"""
        Based on the following market data for {symbol}, provide a detailed weekly trading strategy recommendation:

        {market_summary}

        Consider the following aspects in your analysis:
        1. News Sentiment Trends (emphasize recent news impact)
        2. Technical Indicators
        3. Market Analyst Views
        4. Risk Assessment

        Please provide:
        1. Overall Strategy (Bullish, Bearish, or Neutral)
        2. Primary Reasons (list 3-4 key points, emphasizing news impact)
        3. Risk Factors (list 2-3 main risks)
        4. Suggested Position Sizes (as percentage of portfolio)
        5. Entry and Exit Points (price levels)

        Format the response as a JSON object with these keys: 
        {{
            "strategy": "Bullish/Bearish/Neutral",
            "reasons": ["reason1", "reason2", "reason3"],
            "risks": ["risk1", "risk2"],
            "position_size": "10-15% of portfolio",
            "entry_points": ["point1", "point2"],
            "exit_points": ["point1", "point2"]
        }}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # Updated to use the latest model
                messages=[
                    {"role": "system", "content": "You are a professional trading strategy analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            # Parse AI response with proper JSON parsing
            try:
                ai_insights = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                st.error(f"Error parsing AI response: {str(e)}")
                ai_insights = {
                    "strategy": "Neutral",
                    "reasons": ["Data parsing error - defaulting to neutral stance"],
                    "risks": ["Unable to assess risks due to parsing error"],
                    "position_size": "Consider minimal position size",
                    "entry_points": ["Wait for clear signals"],
                    "exit_points": ["Maintain stop losses"]
                }

            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user

            # Combine all insights with safe dictionary access
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'market_data': {
                    'current_price': stock_data['Close'].iloc[-1],
                    'daily_return': ((stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2]) / stock_data['Close'].iloc[-2] * 100),
                    'technical_indicators': price_factors.get('technical_indicators', {}),
                    'weekly_sentiment': weekly_sentiment,
                    'analyst_rating': market_data.get('Analyst Rating', 'N/A')
                },
                'ai_recommendation': ai_insights,
                'technical_signals': price_factors.get('market_signals', []),
                'recent_news': weekly_sentiment['key_headlines']
            }

        except Exception as e:
            st.error(f"Error generating AI insights: {str(e)}")
            return {
                'error': f"Failed to generate AI insights: {str(e)}",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    except Exception as e:
        st.error(f"Error in strategy generation: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def get_strategy_confidence_score(market_data: dict) -> float:
    """
    Calculate a confidence score for the AI strategy based on signal alignment
    with increased weight on news sentiment
    """
    try:
        if not market_data or 'error' in market_data:
            return 50.0  # Return neutral score if there's an error

        # Safely get required data with defaults
        technical_indicators = market_data.get('technical_indicators', {})
        weekly_sentiment = market_data.get('weekly_sentiment', {})
        analyst_rating = market_data.get('analyst_rating', '')
        ai_recommendation = market_data.get('ai_recommendation', {})

        if not ai_recommendation:
            return 50.0  # Return neutral score if no AI recommendation

        score = 0.0
        weights = {
            'technical': 0.3,
            'sentiment': 0.4,  # Increased weight for sentiment
            'analyst': 0.3
        }

        # Technical indicators alignment (30% weight)
        rsi = technical_indicators.get('rsi', 50)
        if rsi > 70:
            score += weights['technical'] * (-1 if ai_recommendation.get('strategy') == 'Bullish' else 1)
        elif rsi < 30:
            score += weights['technical'] * (1 if ai_recommendation.get('strategy') == 'Bullish' else -1)

        # Sentiment alignment (40% weight)
        sentiment_score = weekly_sentiment.get('weekly_score', 0)
        positive_ratio = weekly_sentiment.get('positive_ratio', 0.5)

        if sentiment_score > 0 or positive_ratio > 0.6:
            score += weights['sentiment'] * (1 if ai_recommendation.get('strategy') == 'Bullish' else -1)
        elif sentiment_score < 0 or positive_ratio < 0.4:
            score += weights['sentiment'] * (-1 if ai_recommendation.get('strategy') == 'Bullish' else 1)

        # Analyst rating alignment (30% weight)
        if 'Buy' in analyst_rating:
            score += weights['analyst'] * (1 if ai_recommendation.get('strategy') == 'Bullish' else -1)
        elif 'Sell' in analyst_rating:
            score += weights['analyst'] * (-1 if ai_recommendation.get('strategy') == 'Bullish' else 1)

        # Normalize score to 0-100%
        confidence_score = (score + 1) * 50
        return min(max(confidence_score, 0), 100)

    except Exception as e:
        st.warning(f"Error calculating confidence score: {str(e)}")
        return 50.0  # Return neutral score on error