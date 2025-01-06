import streamlit as st
import plotly.graph_objects as go
from utils.options_analyzer import analyze_options_strategy
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="IWM Options Strategy",
    page_icon="📊",
    layout="wide"
)

st.title("📊 IWM Options Strategy Analysis")
st.markdown("""
This page provides weekly options strategies based on current market conditions, technical analysis, and news sentiment.
Each strategy is tailored to the market's volatility, price action, and market sentiment.
""")

# Get options analysis
analysis = analyze_options_strategy("IWM")

if 'error' in analysis:
    st.error(analysis['error'])
else:
    # Display current market conditions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${analysis['current_price']:.2f}")
    with col2:
        st.metric("Implied Volatility", f"{analysis['volatility']*100:.1f}%")
    with col3:
        sentiment_color = "red" if analysis['technical_sentiment'] == "Bearish" else "green"
        st.markdown(f"**Technical Sentiment:** <span style='color:{sentiment_color}'>{analysis['technical_sentiment']}</span>", unsafe_allow_html=True)
    with col4:
        sentiment_color = "red" if analysis['news_sentiment'] < -0.2 else "green" if analysis['news_sentiment'] > 0.2 else "blue"
        st.markdown(f"**News Sentiment Score:** <span style='color:{sentiment_color}'>{analysis['news_sentiment']:.2f}</span>", unsafe_allow_html=True)

    # Display volatility regime and black swan comparison
    st.subheader("📊 Volatility Analysis")
    col1, col2 = st.columns(2)

    with col1:
        regime_color = {
            'High Volatility': 'red',
            'Normal': 'blue',
            'Low Volatility': 'green'
        }.get(analysis['volatility_regime'], 'blue')

        st.markdown(f"""
        **Current Volatility Regime:** 
        <span style='color:{regime_color}'>{analysis['volatility_regime']}</span>
        """, unsafe_allow_html=True)

        black_swan_pct = analysis['black_swan_comparison'].get('current_vol_vs_avg_black_swan', 0)
        st.metric(
            "Comparison to Historical Black Swans",
            f"{black_swan_pct:.1f}%",
            delta="High Risk" if black_swan_pct > 50 else "Normal",
            delta_color="inverse" if black_swan_pct > 50 else "normal"
        )

    with col2:
        st.markdown("### Historical Black Swan Events")
        events_df = pd.DataFrame(analysis.get('black_swan_events', []))
        if not events_df.empty:
            st.dataframe(
                events_df[['event', 'date', 'price_impact', 'recovery_days']],
                hide_index=True,
                column_config={
                    'price_impact': st.column_config.NumberColumn(
                        'Impact (%)',
                        format="%.1f%%"
                    ),
                    'recovery_days': st.column_config.NumberColumn(
                        'Recovery (Days)'
                    )
                }
            )

    # Overall Sentiment
    st.subheader("Overall Market Sentiment")
    overall_color = "red" if analysis['overall_sentiment'] == "Bearish" else "green" if analysis['overall_sentiment'] == "Bullish" else "blue"
    st.markdown(f"<h3 style='color:{overall_color}'>{analysis['overall_sentiment']}</h3>", unsafe_allow_html=True)

    # Display strategies for each expiration
    st.subheader("🎯 Weekly Strategy Recommendations")

    for idx, strategy in enumerate(analysis['strategies']):
        with st.expander(f"Strategy for {strategy['expiry']} ({strategy['days_to_expiry']} days) - {strategy['type']}", expanded=idx==0):
            # Strategy description
            st.markdown(f"""
            ### Strategy Overview
            **Type:** {strategy['type']}  
            **Description:** {strategy['description']}  
            **Days to Expiry:** {strategy['days_to_expiry']}
            """)

            # Sentiment Analysis
            st.write("### Sentiment Analysis")
            col1, col2 = st.columns(2)
            with col1:
                tech_color = "green" if strategy['sentiment_data']['technical'] == "Bullish" else "red" if strategy['sentiment_data']['technical'] == "Bearish" else "blue"
                st.markdown(f"**Technical Sentiment:** <span style='color:{tech_color}'>{strategy['sentiment_data']['technical']}</span>", unsafe_allow_html=True)
            with col2:
                news_score = strategy['sentiment_data']['news']['score']
                news_color = "green" if news_score > 0.2 else "red" if news_score < -0.2 else "blue"
                st.markdown(f"**News Sentiment Score:** <span style='color:{news_color}'>{news_score:.2f}</span>", unsafe_allow_html=True)

            # Recent News
            st.write("### Recent News Impact")
            for news in strategy['sentiment_data']['news']['recent_news']:
                st.markdown(f"• {news}")

            # Strategy details
            st.write("### Option Strikes")
            setup_df = pd.DataFrame(strategy['setup']).T
            st.dataframe(setup_df)

            # Risk/Reward metrics
            st.write("### Risk/Reward Profile")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Max Profit", f"${strategy['risk_reward']['max_profit']}")
            with col2:
                st.metric("Max Loss", f"${strategy['risk_reward']['max_loss']}")
            with col3:
                st.metric("Probability of Profit", strategy['risk_reward']['probability_of_profit'])

            # Generate payoff diagram
            st.write("### Strategy Payoff Diagram")
            price_range = np.linspace(
                analysis['current_price'] * 0.9,
                analysis['current_price'] * 1.1,
                100
            )

            # Calculate payoff for each price point
            payoffs = []
            for price in price_range:
                if strategy['type'] == 'Bear Put Spread':
                    # Bear Put Spread payoff calculation
                    buy_strike = strategy['setup']['buy_put']['strike']
                    sell_strike = strategy['setup']['sell_put']['strike']
                    max_profit = strategy['risk_reward']['max_profit']
                    max_loss = strategy['risk_reward']['max_loss']

                    if price >= buy_strike:
                        payoff = -max_loss
                    elif price >= sell_strike:
                        payoff = -max_loss + (buy_strike - price)
                    else:
                        payoff = max_profit
                else:
                    # Bull Call Spread payoff calculation
                    buy_strike = strategy['setup']['buy_call']['strike']
                    sell_strike = strategy['setup']['sell_call']['strike']
                    max_profit = strategy['risk_reward']['max_profit']
                    max_loss = strategy['risk_reward']['max_loss']

                    if price <= buy_strike:
                        payoff = -max_loss
                    elif price <= sell_strike:
                        payoff = -max_loss + (price - buy_strike)
                    else:
                        payoff = max_profit

                payoffs.append(payoff)

            # Create payoff diagram
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=price_range,
                y=payoffs,
                mode='lines',
                name='Payoff',
                line=dict(color='blue', width=2)
            ))

            # Add reference lines
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.add_vline(x=analysis['current_price'], line_dash="dash", line_color="red")

            fig.update_layout(
                title="Profit/Loss at Expiration",
                xaxis_title="Stock Price",
                yaxis_title="Profit/Loss ($)",
                showlegend=True,
                template="plotly_white",
                height=500,
                annotations=[
                    dict(
                        x=analysis['current_price'],
                        y=max(payoffs),
                        text="Current Price",
                        showarrow=True,
                        arrowhead=1
                    )
                ]
            )

            # Add unique key for each plotly chart
            st.plotly_chart(fig, use_container_width=True, key=f'payoff_chart_{strategy["expiry"]}')

            # Trading instructions
            st.write("### Trading Instructions")
            if strategy['type'] == 'Bear Put Spread':
                st.markdown(f"""
                1. Buy 1 Put at ${strategy['setup']['buy_put']['strike']}
                2. Sell 1 Put at ${strategy['setup']['sell_put']['strike']}
                """)
            else:
                st.markdown(f"""
                1. Buy 1 Call at ${strategy['setup']['buy_call']['strike']}
                2. Sell 1 Call at ${strategy['setup']['sell_call']['strike']}
                """)