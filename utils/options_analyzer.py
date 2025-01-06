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
        st.info(f"Fetching options data for {symbol}...")
        stock = yf.Ticker(symbol)
        all_options = {}

        # Get available expiration dates
        if not hasattr(stock, 'options') or not stock.options:
            st.error(f"No options data available for {symbol}")
            return {}

        # Get next 4 expiration dates
        dates = stock.options[:4]

        for date in dates:
            try:
                opt = stock.option_chain(date)
                if hasattr(opt, 'calls') and hasattr(opt, 'puts'):
                    # Filter out options with zero volume
                    calls = opt.calls[opt.calls['volume'] > 0]
                    puts = opt.puts[opt.puts['volume'] > 0]

                    if not calls.empty and not puts.empty:
                        all_options[date] = {
                            'calls': calls,
                            'puts': puts
                        }
                        st.success(f"Successfully fetched options for {date}")
            except Exception as e:
                st.warning(f"Error fetching options for date {date}: {str(e)}")
                continue

        if not all_options:
            st.error("Could not fetch any valid options data")
            return {}

        return all_options
    except Exception as e:
        st.error(f"Error in get_options_chain: {str(e)}")
        return {}

def find_nearest_strike(options_df: pd.DataFrame, target_price: float) -> float:
    """Find the nearest available strike price"""
    return options_df.loc[abs(options_df['strike'] - target_price).idxmin()]['strike']

def analyze_options_strategy(symbol: str = "IWM") -> dict:
    """
    Analyze and recommend options strategies for the next 4 weeks
    """
    try:
        st.info(f"Analyzing options strategies for {symbol}...")
        stock = yf.Ticker(symbol)

        # Get current price and calculate volatility
        hist = stock.history(period="1mo")
        if hist.empty:
            st.error(f"No historical data available for {symbol}")
            return {'error': 'No historical data available'}

        current_price = hist['Close'].iloc[-1]
        volatility = hist['Close'].pct_change().std() * np.sqrt(252)

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
            try:
                # Convert expiry_date to datetime
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
                days_to_expiry = (expiry - datetime.now()).days

                calls = chain['calls']
                puts = chain['puts']

                if volatility > 0.2:  # High volatility
                    # Find appropriate strikes for Iron Condor
                    sell_call_target = current_price * 1.02
                    buy_call_target = current_price * 1.04
                    sell_put_target = current_price * 0.98
                    buy_put_target = current_price * 0.96

                    # Find nearest available strikes
                    sell_call_strike = find_nearest_strike(calls, sell_call_target)
                    buy_call_strike = find_nearest_strike(calls, buy_call_target)
                    sell_put_strike = find_nearest_strike(puts, sell_put_target)
                    buy_put_strike = find_nearest_strike(puts, buy_put_target)

                    strategy = {
                        'expiry': expiry_date,
                        'days_to_expiry': days_to_expiry,
                        'type': 'Iron Condor',
                        'description': 'High volatility strategy to collect premium',
                        'setup': {
                            'sell_call': {'strike': sell_call_strike},
                            'buy_call': {'strike': buy_call_strike},
                            'sell_put': {'strike': sell_put_strike},
                            'buy_put': {'strike': buy_put_strike}
                        },
                        'risk_reward': {
                            'max_profit': round(min(buy_call_strike - sell_call_strike, sell_put_strike - buy_put_strike) * 0.15, 2),
                            'max_loss': round(max(buy_call_strike - sell_call_strike, sell_put_strike - buy_put_strike) * 0.85, 2),
                            'probability_of_profit': '65-70%'
                        }
                    }
                else:  # Low volatility
                    # Find appropriate strikes for Bull Call Spread
                    buy_call_target = current_price * 0.99
                    sell_call_target = current_price * 1.02

                    # Find nearest available strikes
                    buy_call_strike = find_nearest_strike(calls, buy_call_target)
                    sell_call_strike = find_nearest_strike(calls, sell_call_target)

                    strategy = {
                        'expiry': expiry_date,
                        'days_to_expiry': days_to_expiry,
                        'type': 'Bull Call Spread',
                        'description': 'Bullish strategy for low volatility environment',
                        'setup': {
                            'buy_call': {'strike': buy_call_strike},
                            'sell_call': {'strike': sell_call_strike}
                        },
                        'risk_reward': {
                            'max_profit': round((sell_call_strike - buy_call_strike) * 0.6, 2),
                            'max_loss': round((sell_call_strike - buy_call_strike) * 0.4, 2),
                            'probability_of_profit': '55-60%'
                        }
                    }

                strategies.append(strategy)
                st.success(f"Successfully generated strategy for {expiry_date}")
            except Exception as e:
                st.warning(f"Error generating strategy for {expiry_date}: {str(e)}")
                continue

        if not strategies:
            st.error("Could not generate any valid strategies")
            return {
                'error': 'No valid strategies could be generated',
                'current_price': current_price,
                'volatility': volatility,
                'strategies': []
            }

        return {
            'current_price': current_price,
            'volatility': volatility,
            'strategies': sorted(strategies, key=lambda x: x['days_to_expiry'])
        }
    except Exception as e:
        st.error(f"Error analyzing options strategies: {str(e)}")
        return {
            'error': str(e),
            'current_price': 0,
            'volatility': 0,
            'strategies': []
        }