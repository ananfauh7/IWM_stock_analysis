import streamlit as st
import plotly.graph_objects as go
from utils.options_analyzer import analyze_options_strategy
import pandas as pd

st.set_page_config(
    page_title="IWM Options Strategy",
    page_icon="📊",
    layout="wide"
)

st.title("📊 IWM Options Strategy Analysis")
st.markdown("Weekly options strategies based on current market conditions")

# Get options analysis
analysis = analyze_options_strategy("IWM")

# Display current market conditions
col1, col2 = st.columns(2)
with col1:
    st.metric("Current Price", f"${analysis['current_price']:.2f}")
with col2:
    st.metric("Implied Volatility", f"{analysis['volatility']*100:.1f}%")

# Display strategies for each expiration
st.subheader("🎯 Recommended Strategies")

for strategy in analysis['strategies']:
    with st.expander(f"Strategy for {strategy['expiry']} - {strategy['type']}"):
        # Strategy details
        st.write("### Setup")
        setup_df = pd.DataFrame(strategy['setup']).T
        st.dataframe(setup_df)
        
        # Risk/Reward
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Max Profit", f"${strategy['risk_reward']['max_profit']}")
        with col2:
            st.metric("Max Loss", f"${strategy['risk_reward']['max_loss']}")
        
        # Visualize strategy payoff
        strikes = []
        payoffs = []
        current_price = analysis['current_price']
        
        # Generate payoff diagram points
        for price in range(int(current_price * 0.9), int(current_price * 1.1)):
            strikes.append(price)
            if strategy['type'] == 'Iron Condor':
                payoff = min(
                    strategy['risk_reward']['max_profit'],
                    min(
                        strategy['setup']['sell_call']['strike'] - price,
                        price - strategy['setup']['sell_put']['strike']
                    )
                )
            else:  # Bull Call Spread
                payoff = min(
                    strategy['risk_reward']['max_profit'],
                    max(
                        -strategy['risk_reward']['max_loss'],
                        price - strategy['setup']['buy_call']['strike']
                    )
                )
            payoffs.append(payoff)
        
        # Create payoff diagram
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=strikes,
            y=payoffs,
            mode='lines',
            name='Payoff'
        ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_vline(x=current_price, line_dash="dash", line_color="red")
        
        fig.update_layout(
            title="Strategy Payoff Diagram",
            xaxis_title="Stock Price",
            yaxis_title="Profit/Loss",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Trading instructions
        st.write("### Trading Instructions")
        if strategy['type'] == 'Iron Condor':
            st.markdown("""
            1. Sell 1 Call at {sell_call} strike
            2. Buy 1 Call at {buy_call} strike
            3. Sell 1 Put at {sell_put} strike
            4. Buy 1 Put at {buy_put} strike
            """.format(**{k: v['strike'] for k, v in strategy['setup'].items()}))
        else:
            st.markdown("""
            1. Buy 1 Call at {buy_call} strike
            2. Sell 1 Call at {sell_call} strike
            """.format(**{k: v['strike'] for k, v in strategy['setup'].items()}))
