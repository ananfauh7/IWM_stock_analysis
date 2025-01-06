import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from utils.data_fetcher import fetch_stock_data, fetch_options_data
from utils.price_factors_analyzer import analyze_price_factors
from utils.sentiment_analyzer import analyze_news_sentiment

def analyze_options_strategy(symbol: str = "IWM") -> dict:
    """
    Analyze and recommend options strategies based on technical sentiment and news sentiment
    """
    try:
        # Get historical data for volatility calculation
        df = fetch_stock_data(symbol)
        if df.empty:
            return {
                'error': 'No historical data available',
                'current_price': 0,
                'volatility': 0,
                'strategies': []
            }

        # Get technical sentiment and news sentiment
        price_factors = analyze_price_factors(symbol)
        technical_sentiment = price_factors.get('technical_sentiment', 'Neutral')

        # Get news sentiment data
        sentiment_data = analyze_news_sentiment(symbol)
        sentiment_score = sentiment_data.get('score', 0)
        recent_news = sentiment_data.get('recent_news', [])

        # Combine technical and news sentiment for overall strategy
        # Weight: 60% technical, 40% news sentiment
        bullish_signals = 0
        total_signals = 2

        if technical_sentiment == 'Bullish':
            bullish_signals += 0.6
        elif technical_sentiment == 'Bearish':
            bullish_signals -= 0.6

        if sentiment_score > 0.2:  # Strong positive sentiment
            bullish_signals += 0.4
        elif sentiment_score < -0.2:  # Strong negative sentiment
            bullish_signals -= 0.4
        else:  # Neutral sentiment adds half weight
            bullish_signals += 0.2 * (1 if sentiment_score > 0 else -1)

        # Determine overall sentiment
        overall_sentiment = 'Bullish' if bullish_signals > 0.3 else 'Bearish' if bullish_signals < -0.3 else 'Neutral'

        current_price = df['Close'].iloc[-1]
        volatility = df['Close'].pct_change().std() * np.sqrt(252)  # Annualized volatility

        # Generate weekly expiration dates for the next 4 weeks
        strategies = []
        for week in range(1, 5):
            expiry_date = (datetime.now() + timedelta(weeks=week)).strftime('%Y-%m-%d')

            if overall_sentiment == 'Bearish':
                # Bear Put Spread for bearish outlook
                strategy_type = 'Bear Put Spread'
                description = f'Bearish sentiment based on technical indicators ({technical_sentiment}) and news sentiment (score: {sentiment_score:.2f})'
                setup = {
                    'buy_put': {'strike': round(current_price * 1.01, 2)},
                    'sell_put': {'strike': round(current_price * 0.97, 2)}
                }
                max_profit = round((setup['buy_put']['strike'] - setup['sell_put']['strike']) * 0.8, 2)
                max_loss = round((setup['buy_put']['strike'] - setup['sell_put']['strike']) * 0.2, 2)
                prob_profit = '60-70%' if sentiment_score < -0.5 else '50-60%'
            else:
                # Bull Call Spread for bullish/neutral outlook
                strategy_type = 'Bull Call Spread'
                description = f'Bullish/Neutral sentiment based on technical indicators ({technical_sentiment}) and news sentiment (score: {sentiment_score:.2f})'
                setup = {
                    'buy_call': {'strike': round(current_price * 0.99, 2)},
                    'sell_call': {'strike': round(current_price * 1.03, 2)}
                }
                max_profit = round((setup['sell_call']['strike'] - setup['buy_call']['strike']) * 0.8, 2)
                max_loss = round((setup['sell_call']['strike'] - setup['buy_call']['strike']) * 0.2, 2)
                prob_profit = '60-70%' if sentiment_score > 0.5 else '50-60%'

            strategies.append({
                'type': strategy_type,
                'description': description,
                'expiry': expiry_date,
                'days_to_expiry': week * 7,
                'setup': setup,
                'risk_reward': {
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'probability_of_profit': prob_profit
                },
                'sentiment_data': {
                    'technical': technical_sentiment,
                    'news': {
                        'score': sentiment_score,
                        'recent_news': recent_news[:3]  # Include top 3 recent news items
                    }
                }
            })

        return {
            'current_price': current_price,
            'volatility': volatility,
            'technical_sentiment': technical_sentiment,
            'news_sentiment': sentiment_score,
            'overall_sentiment': overall_sentiment,
            'strategies': strategies
        }

    except Exception as e:
        st.error(f"Error analyzing options strategies: {str(e)}")
        return {
            'error': str(e),
            'current_price': 0,
            'volatility': 0,
            'strategies': []
        }