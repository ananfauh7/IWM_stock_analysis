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

        if not hasattr(stock, 'options') or not stock.options:
            st.error(f"No options data available for {symbol}")
            return {}

        # Get next 4 expiration dates
        dates = stock.options[:4]

        for date in dates:
            try:
                opt = stock.option_chain(date)
                if hasattr(opt, 'calls') and hasattr(opt, 'puts'):
                    # Filter relevant options with stricter criteria
                    calls = opt.calls[
                        (opt.calls['volume'] > 100) & 
                        (opt.calls['lastPrice'] > 0) &
                        (opt.calls['openInterest'] > 50)
                    ]
                    puts = opt.puts[
                        (opt.puts['volume'] > 100) & 
                        (opt.puts['lastPrice'] > 0) &
                        (opt.puts['openInterest'] > 50)
                    ]

                    if not calls.empty and not puts.empty:
                        all_options[date] = {
                            'calls': calls.copy(),
                            'puts': puts.copy()
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

def validate_strike_prices(strategy: dict, current_price: float) -> bool:
    """Validate if the strike prices make sense for the strategy"""
    try:
        if strategy['type'] == 'Iron Condor':
            return (
                strategy['setup']['buy_put']['strike'] < strategy['setup']['sell_put']['strike'] < 
                current_price < 
                strategy['setup']['sell_call']['strike'] < strategy['setup']['buy_call']['strike']
            )
        else:  # Bull Call Spread
            return (
                strategy['setup']['buy_call']['strike'] < strategy['setup']['sell_call']['strike'] and
                abs(strategy['setup']['buy_call']['strike'] - current_price) / current_price < 0.1
            )
    except:
        return False

def find_nearest_strike(options_df: pd.DataFrame, target_price: float) -> float:
    """Find the nearest available strike price"""
    try:
        valid_strikes = options_df[
            (options_df['volume'] > 100) & 
            (options_df['lastPrice'] > 0) &
            (options_df['openInterest'] > 50)
        ]['strike']

        if valid_strikes.empty:
            return None

        return valid_strikes.iloc[(abs(valid_strikes - target_price)).argmin()]
    except Exception as e:
        st.error(f"Error finding nearest strike: {str(e)}")
        return None

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

                if volatility > 0.2:  # High volatility
                    # Find appropriate strikes for Iron Condor
                    sell_call_strike = find_nearest_strike(chain['calls'], current_price * 1.02)
                    buy_call_strike = find_nearest_strike(chain['calls'], current_price * 1.04)
                    sell_put_strike = find_nearest_strike(chain['puts'], current_price * 0.98)
                    buy_put_strike = find_nearest_strike(chain['puts'], current_price * 0.96)

                    # Validate all strikes are found
                    if not all([sell_call_strike, buy_call_strike, sell_put_strike, buy_put_strike]):
                        continue

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
                        }
                    }

                    # Calculate max profit and loss
                    call_spread = buy_call_strike - sell_call_strike
                    put_spread = sell_put_strike - buy_put_strike
                    strategy['risk_reward'] = {
                        'max_profit': round(min(call_spread, put_spread) * 0.15, 2),
                        'max_loss': round(max(call_spread, put_spread) * 0.85, 2),
                        'probability_of_profit': '65-70%'
                    }

                else:  # Low volatility
                    # Find appropriate strikes for Bull Call Spread
                    buy_call_strike = find_nearest_strike(chain['calls'], current_price * 0.99)
                    sell_call_strike = find_nearest_strike(chain['calls'], current_price * 1.02)

                    # Validate all strikes are found
                    if not all([buy_call_strike, sell_call_strike]):
                        continue

                    strategy = {
                        'expiry': expiry_date,
                        'days_to_expiry': days_to_expiry,
                        'type': 'Bull Call Spread',
                        'description': 'Bullish strategy for low volatility environment',
                        'setup': {
                            'buy_call': {'strike': buy_call_strike},
                            'sell_call': {'strike': sell_call_strike}
                        }
                    }

                    # Calculate max profit and loss
                    spread = sell_call_strike - buy_call_strike
                    strategy['risk_reward'] = {
                        'max_profit': round(spread * 0.6, 2),
                        'max_loss': round(spread * 0.4, 2),
                        'probability_of_profit': '55-60%'
                    }

                # Validate strategy before adding
                if validate_strike_prices(strategy, current_price):
                    strategies.append(strategy)
                    st.success(f"Successfully generated strategy for {expiry_date}")

            except Exception as e:
                st.warning(f"Error generating strategy for {expiry_date}: {str(e)}")
                continue

        if not strategies:
            st.warning("Could not generate any valid strategies with the current market conditions")
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