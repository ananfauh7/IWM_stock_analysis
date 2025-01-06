import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from utils.data_fetcher import fetch_stock_data, fetch_options_data
from utils.price_factors_analyzer import analyze_price_factors

def analyze_options_strategy(symbol: str = "IWM") -> dict:
    """
    Analyze and recommend options strategies based on technical sentiment
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

        # Get technical sentiment
        price_factors = analyze_price_factors(symbol)
        technical_sentiment = price_factors.get('technical_sentiment', 'Neutral')

        current_price = df['Close'].iloc[-1]
        volatility = df['Close'].pct_change().std() * np.sqrt(252)  # Annualized volatility

        # Generate weekly expiration dates for the next 4 weeks
        strategies = []
        for week in range(1, 5):
            expiry_date = (datetime.now() + timedelta(weeks=week)).strftime('%Y-%m-%d')

            if technical_sentiment == 'Bearish':
                # Bear Put Spread for bearish outlook
                strategy_type = 'Bear Put Spread'
                description = 'Bearish technical sentiment suggests defensive strategy'
                setup = {
                    'buy_put': {'strike': round(current_price * 1.01, 2)},
                    'sell_put': {'strike': round(current_price * 0.97, 2)}
                }
                max_profit = round((setup['buy_put']['strike'] - setup['sell_put']['strike']) * 0.8, 2)
                max_loss = round((setup['buy_put']['strike'] - setup['sell_put']['strike']) * 0.2, 2)
                prob_profit = '50-60%'
            else:
                # Bull Call Spread for bullish/neutral outlook
                strategy_type = 'Bull Call Spread'
                description = 'Bullish/Neutral technical sentiment favors upside potential'
                setup = {
                    'buy_call': {'strike': round(current_price * 0.99, 2)},
                    'sell_call': {'strike': round(current_price * 1.03, 2)}
                }
                max_profit = round((setup['sell_call']['strike'] - setup['buy_call']['strike']) * 0.8, 2)
                max_loss = round((setup['sell_call']['strike'] - setup['buy_call']['strike']) * 0.2, 2)
                prob_profit = '50-60%'

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
                }
            })

        return {
            'current_price': current_price,
            'volatility': volatility,
            'technical_sentiment': technical_sentiment,
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