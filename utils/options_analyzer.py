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

        # Get technical sentiment, news sentiment, and volatility analysis
        price_factors = analyze_price_factors(symbol)
        technical_sentiment = price_factors.get('technical_sentiment', 'Neutral')
        volatility_analysis = price_factors.get('volatility_analysis', {})

        # Get news sentiment data
        sentiment_data = analyze_news_sentiment(symbol)
        sentiment_score = sentiment_data.get('score', 0)
        recent_news = sentiment_data.get('recent_news', [])

        # Enhanced sentiment analysis with weighted components
        technical_weight = 0.4  # Technical analysis weight
        news_weight = 0.3      # News sentiment weight
        volatility_weight = 0.3 # Volatility impact weight

        # Calculate sentiment scores
        technical_score = 1 if technical_sentiment == 'Bullish' else -1 if technical_sentiment == 'Bearish' else 0
        news_impact = sentiment_score  # Already between -1 and 1

        # Enhanced volatility impact analysis
        volatility = df['Close'].pct_change().std() * np.sqrt(252)
        vol_regime = volatility_analysis.get('volatility_regime', 'Normal')
        black_swan_comparison = volatility_analysis.get('comparison_to_black_swans', {})

        # Adjust volatility impact based on black swan comparison
        vol_impact = 0
        if vol_regime == 'High Volatility':
            vol_impact = -1 if black_swan_comparison.get('current_vol_vs_avg_black_swan', 0) > 50 else -0.5
        elif vol_regime == 'Low Volatility':
            vol_impact = 0.5

        # Combined weighted score with black swan consideration
        total_score = (technical_score * technical_weight + 
                      news_impact * news_weight + 
                      vol_impact * volatility_weight)

        # Determine overall sentiment with more granular categories
        if total_score > 0.3:
            overall_sentiment = 'Strong Bullish'
        elif total_score > 0.1:
            overall_sentiment = 'Moderately Bullish'
        elif total_score < -0.3:
            overall_sentiment = 'Strong Bearish'
        elif total_score < -0.1:
            overall_sentiment = 'Moderately Bearish'
        else:
            overall_sentiment = 'Neutral'

        current_price = df['Close'].iloc[-1]

        # Generate weekly expiration dates for the next 4 weeks
        strategies = []
        for week in range(1, 5):
            expiry_date = (datetime.now() + timedelta(weeks=week)).strftime('%Y-%m-%d')

            # Adjust strategy based on volatility regime
            if vol_regime == 'High Volatility':
                # Use wider spreads in high volatility
                spread_width = 0.05
                # Reduce position size recommendation
                position_size = "Consider reducing position size due to elevated volatility"
            else:
                spread_width = 0.03
                position_size = "Standard position sizing recommended"

            # Strategy selection based on overall sentiment
            if 'Bearish' in overall_sentiment:
                # Bear Put Spread for bearish outlook
                strategy_type = 'Bear Put Spread'
                # Adjust strikes based on sentiment strength and volatility
                strike_multiplier = 1.02 if 'Strong' in overall_sentiment else 1.01

                setup = {
                    'buy_put': {'strike': round(current_price * strike_multiplier, 2)},
                    'sell_put': {'strike': round(current_price * (strike_multiplier - spread_width), 2)}
                }

                max_profit = round((setup['buy_put']['strike'] - setup['sell_put']['strike']) * 0.8, 2)
                max_loss = round((setup['buy_put']['strike'] - setup['sell_put']['strike']) * 0.2, 2)

                # Adjust probability based on sentiment strength and historical patterns
                base_prob = 60 if 'Strong' in overall_sentiment else 55
                news_adj = 10 if sentiment_score < -0.5 else 5 if sentiment_score < -0.2 else 0
                # Reduce probability if in high volatility regime
                vol_adj = -5 if vol_regime == 'High Volatility' else 0
                final_prob = base_prob + news_adj + vol_adj
                prob_profit = f'{final_prob}-{final_prob + 10}%'

            else:
                # Bull Call Spread for bullish/neutral outlook
                strategy_type = 'Bull Call Spread'
                # Adjust strikes based on sentiment strength and volatility
                strike_multiplier = 0.98 if 'Strong' in overall_sentiment else 0.99

                setup = {
                    'buy_call': {'strike': round(current_price * strike_multiplier, 2)},
                    'sell_call': {'strike': round(current_price * (strike_multiplier + spread_width), 2)}
                }

                max_profit = round((setup['sell_call']['strike'] - setup['buy_call']['strike']) * 0.8, 2)
                max_loss = round((setup['sell_call']['strike'] - setup['buy_call']['strike']) * 0.2, 2)

                # Adjust probability based on sentiment strength and historical patterns
                base_prob = 60 if 'Strong' in overall_sentiment else 55 if 'Moderately' in overall_sentiment else 50
                news_adj = 10 if sentiment_score > 0.5 else 5 if sentiment_score > 0.2 else 0
                # Reduce probability if in high volatility regime
                vol_adj = -5 if vol_regime == 'High Volatility' else 0
                final_prob = base_prob + news_adj + vol_adj
                prob_profit = f'{final_prob}-{final_prob + 10}%'

            # Enhanced strategy description with black swan context
            description = (
                f"{overall_sentiment} outlook based on:\n"
                f"• Technical Analysis ({technical_sentiment})\n"
                f"• News Sentiment (Score: {sentiment_score:.2f})\n"
                f"• Volatility Regime: {vol_regime}\n"
                f"• Black Swan Comparison: "
                f"{black_swan_comparison.get('current_vol_vs_avg_black_swan', 0):.1f}% "
                f"of historical black swan levels\n"
                f"• Position Sizing: {position_size}"
            )

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
                        'recent_news': recent_news[:3]
                    },
                    'volatility_regime': vol_regime,
                    'black_swan_comparison': black_swan_comparison
                }
            })

        return {
            'current_price': current_price,
            'volatility': volatility,
            'volatility_regime': vol_regime,
            'black_swan_comparison': black_swan_comparison,
            'technical_sentiment': technical_sentiment,
            'news_sentiment': sentiment_score,
            'overall_sentiment': overall_sentiment,
            'sentiment_weights': {
                'technical': technical_weight,
                'news': news_weight,
                'volatility': volatility_weight
            },
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