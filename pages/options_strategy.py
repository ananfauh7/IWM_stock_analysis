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
This page provides weekly options strategies based on current market conditions and technical sentiment.
Each strategy is tailored to the market's volatility and price action.
""")

# Get options analysis
analysis = analyze_options_strategy("IWM")

if 'error' in analysis:
    st.error(analysis['error'])
else:
    # Display current market conditions
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${analysis['current_price']:.2f}")
    with col2:
        st.metric("Implied Volatility", f"{analysis['volatility']*100:.1f}%")
    with col3:
        sentiment_color = "red" if analysis['technical_sentiment'] == "Bearish" else "green"
        st.markdown(f"**Technical Sentiment:** <span style='color:{sentiment_color}'>{analysis['technical_sentiment']}</span>", unsafe_allow_html=True)

    # Display strategies for each expiration
    st.subheader("🎯 Weekly Strategy Recommendations")

    for idx, strategy in enumerate(analysis['strategies']):
        with st.expander(f"Strategy for {strategy['expiry']} ({strategy['days_to_expiry']} days) - {strategy['type']}"):
            # Strategy description
            st.markdown(f"""
            ### Strategy Overview
            **Type:** {strategy['type']}  
            **Description:** {strategy['description']}  
            **Days to Expiry:** {strategy['days_to_expiry']}
            """)

            # Strategy details
            st.write("### Option Strikes")
            setup_df = pd.DataFrame(strategy['setup']).T
            st.dataframe(setup_df, key=f'setup_df_{idx}')

            # Risk/Reward metrics
            st.write("### Risk/Reward Profile")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Max Profit_{idx}", f"${strategy['risk_reward']['max_profit']}")
            with col2:
                st.metric(f"Max Loss_{idx}", f"${strategy['risk_reward']['max_loss']}")
            with col3:
                st.metric(f"Probability of Profit_{idx}", strategy['risk_reward']['probability_of_profit'])

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
            st.plotly_chart(fig, use_container_width=True, key=f'payoff_chart_{idx}')

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