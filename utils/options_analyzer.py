import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

@st.cache_data(ttl=3600)
def get_options_chain(symbol: str = "IWM") -> dict:
    """
    Fetch options chain data for the specified symbol
    """
    try:
        stock = yf.Ticker(symbol)
        all_options = {}

        # Get next 4 expiration dates
        dates = stock.options[:4] if stock.options else []

        for date in dates:
            opt = stock.option_chain(date)
            if hasattr(opt, 'calls') and hasattr(opt, 'puts'):
                all_options[date] = {
                    'calls': opt.calls,
                    'puts': opt.puts
                }

        return all_options
    except Exception as e:
        st.error(f"Error fetching options chain: {str(e)}")
        return {}

def analyze_options_strategy(symbol: str = "IWM") -> dict:
    """
    Analyze and recommend options strategies for the next 4 weeks
    """
    try:
        stock = yf.Ticker(symbol)
        current_price = stock.history(period="1d")['Close'].iloc[-1]
        volatility = stock.history(period="1mo")['Close'].pct_change().std() * np.sqrt(252)

        # Get options chain
        options = get_options_chain(symbol)
        if not options:
            return {
                'error': 'No options data available',
                'current_price': current_price,
                'volatility': volatility,
                'strategies': []
            }

        strategies = []
        for expiry_date, chain in options.items():
            # Convert expiry_date to datetime
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            days_to_expiry = (expiry - datetime.now()).days

            # Filter relevant options
            calls = chain['calls']
            puts = chain['puts']

            # Find ATM options
            atm_call = calls[abs(calls['strike'] - current_price).idxmin()]
            atm_put = puts[abs(puts['strike'] - current_price).idxmin()]

            # Strategy selection based on market conditions
            if volatility > 0.2:  # High volatility
                strategy = {
                    'expiry': expiry_date,
                    'days_to_expiry': days_to_expiry,
                    'type': 'Iron Condor',
                    'description': 'High volatility strategy to collect premium',
                    'setup': {
                        'sell_call': {'strike': round(current_price * 1.02, 2)},
                        'buy_call': {'strike': round(current_price * 1.04, 2)},
                        'sell_put': {'strike': round(current_price * 0.98, 2)},
                        'buy_put': {'strike': round(current_price * 0.96, 2)}
                    },
                    'risk_reward': {
                        'max_profit': round(atm_call['impliedVolatility'] * current_price * 0.1, 2),
                        'max_loss': round(current_price * 0.02, 2),
                        'probability_of_profit': '65-70%'
                    }
                }
            else:  # Low volatility
                strategy = {
                    'expiry': expiry_date,
                    'days_to_expiry': days_to_expiry,
                    'type': 'Bull Call Spread',
                    'description': 'Bullish strategy for low volatility environment',
                    'setup': {
                        'buy_call': {'strike': round(current_price * 0.99, 2)},
                        'sell_call': {'strike': round(current_price * 1.02, 2)}
                    },
                    'risk_reward': {
                        'max_profit': round(current_price * 0.03, 2),
                        'max_loss': round(atm_call['lastPrice'], 2),
                        'probability_of_profit': '55-60%'
                    }
                }

            strategies.append(strategy)

        return {
            'current_price': current_price,
            'volatility': volatility,
            'strategies': sorted(strategies, key=lambda x: x['days_to_expiry'])
        }
    except Exception as e:
        st.error(f"Error analyzing options strategies: {str(e)}")
        return {
            'current_price': 0,
            'volatility': 0,
            'strategies': []
        }