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
This page provides weekly options strategies based on current market conditions.
Each strategy is tailored to the market's volatility and price action.

### Iron Condor Strategy
An Iron Condor is a neutral options strategy that profits when the stock trades in a range:
- Sells a call spread (bear call spread)
- Sells a put spread (bull put spread)
- Maximum profit achieved when stock price stays between short strikes
- Limited risk due to protective long options
""")

# Get options analysis
analysis = analyze_options_strategy("IWM")

if 'error' in analysis:
    st.error(analysis['error'])
else:
    # Display current market conditions
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Price", f"${analysis['current_price']:.2f}")
    with col2:
        st.metric("Implied Volatility", f"{analysis['volatility']*100:.1f}%")

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

            {'#### Iron Condor Details' if strategy['type'] == 'Iron Condor' else ''}
            {'''
            - Profit Zone: Between short call and short put strikes
            - Maximum Profit: Achieved when stock expires between short strikes
            - Risk Management: Protected by long options on both sides
            - Best For: High volatility environments expecting range-bound price action
            ''' if strategy['type'] == 'Iron Condor' else ''}
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
                if strategy['type'] == 'Iron Condor':
                    # Iron Condor payoff calculation
                    max_profit = strategy['risk_reward']['max_profit']
                    max_loss = strategy['risk_reward']['max_loss']
                    sell_call_strike = strategy['setup']['sell_call']['strike']
                    buy_call_strike = strategy['setup']['buy_call']['strike']
                    sell_put_strike = strategy['setup']['sell_put']['strike']
                    buy_put_strike = strategy['setup']['buy_put']['strike']

                    if price <= buy_put_strike:
                        payoff = -max_loss
                    elif price <= sell_put_strike:
                        payoff = -max_loss + (price - buy_put_strike)
                    elif price <= sell_call_strike:
                        payoff = max_profit
                    elif price <= buy_call_strike:
                        payoff = max_profit - (price - sell_call_strike)
                    else:
                        payoff = -max_loss
                else:  # Bull Call Spread
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

            # Add breakeven lines
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.add_vline(x=analysis['current_price'], line_dash="dash", line_color="red")

            # For Iron Condor, add vertical lines at option strikes
            if strategy['type'] == 'Iron Condor':
                fig.add_vline(x=strategy['setup']['sell_put']['strike'], 
                            line_dash="dot", line_color="green",
                            annotation_text="Short Put")
                fig.add_vline(x=strategy['setup']['sell_call']['strike'], 
                            line_dash="dot", line_color="green",
                            annotation_text="Short Call")
                fig.add_vline(x=strategy['setup']['buy_put']['strike'], 
                            line_dash="dot", line_color="orange",
                            annotation_text="Long Put")
                fig.add_vline(x=strategy['setup']['buy_call']['strike'], 
                            line_dash="dot", line_color="orange",
                            annotation_text="Long Call")

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
            if strategy['type'] == 'Iron Condor':
                st.markdown(f"""
                **Iron Condor Setup:**
                1. Sell 1 Call at ${strategy['setup']['sell_call']['strike']} (Short Call)
                2. Buy 1 Call at ${strategy['setup']['buy_call']['strike']} (Long Call - Protection)
                3. Sell 1 Put at ${strategy['setup']['sell_put']['strike']} (Short Put)
                4. Buy 1 Put at ${strategy['setup']['buy_put']['strike']} (Long Put - Protection)

                **Risk Management:**
                - Maximum Loss: ${strategy['risk_reward']['max_loss']}
                - Consider closing the position if the stock price moves close to either short strike
                - Target 50% of maximum profit for early exit
                """)
            else:
                st.markdown(f"""
                1. Buy 1 Call at ${strategy['setup']['buy_call']['strike']}
                2. Sell 1 Call at ${strategy['setup']['sell_call']['strike']}
                """)