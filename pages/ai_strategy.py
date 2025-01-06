import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from utils.ai_strategy_analyzer import generate_trading_strategy, get_strategy_confidence_score

st.set_page_config(
    page_title="AI Trading Strategy",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI-Powered Trading Strategy")
st.markdown("""
This page provides AI-generated trading strategy recommendations with detailed explanations
of the underlying factors and confidence metrics.
""")

# Generate AI strategy recommendations
analysis = generate_trading_strategy("IWM")

if 'error' in analysis:
    st.error(f"Error: {analysis['error']}")
else:
    # Calculate strategy confidence score
    confidence_score = get_strategy_confidence_score(analysis)
    
    # Display main metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${analysis['market_data']['current_price']:.2f}")
    with col2:
        st.metric("Daily Return", 
                 f"{analysis['market_data']['daily_return']:.2f}%",
                 delta_color="normal" if analysis['market_data']['daily_return'] > 0 else "inverse")
    with col3:
        st.metric("Strategy Confidence", 
                 f"{confidence_score:.1f}%",
                 delta_color="normal" if confidence_score > 50 else "inverse")

    # AI Strategy Recommendation
    st.header("📊 Strategy Recommendation")
    
    # Create an expander for detailed strategy
    with st.expander("View Detailed Strategy Analysis", expanded=True):
        # Strategy overview
        st.subheader("Strategy Overview")
        strategy_color = {
            'Bullish': 'green',
            'Bearish': 'red',
            'Neutral': 'blue'
        }.get(analysis['ai_recommendation']['strategy'], 'black')
        
        st.markdown(f"""
        **Overall Strategy:** <span style='color:{strategy_color}'>{analysis['ai_recommendation']['strategy']}</span>
        """, unsafe_allow_html=True)
        
        # Primary reasons
        st.subheader("Primary Reasons")
        for idx, reason in enumerate(analysis['ai_recommendation']['reasons'], 1):
            st.markdown(f"{idx}. {reason}")
        
        # Risk factors
        st.subheader("⚠️ Risk Factors")
        for idx, risk in enumerate(analysis['ai_recommendation']['risks'], 1):
            st.markdown(f"{idx}. {risk}")
        
        # Entry and exit points
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Entry Points")
            for entry in analysis['ai_recommendation']['entry_points']:
                st.markdown(f"• {entry}")
        
        with col2:
            st.subheader("📉 Exit Points")
            for exit_point in analysis['ai_recommendation']['exit_points']:
                st.markdown(f"• {exit_point}")
    
    # Supporting Data
    st.header("📑 Supporting Analysis")
    
    # Technical Signals
    st.subheader("Technical Signals")
    for signal in analysis['technical_signals']:
        signal_color = 'green' if 'Bullish' in signal else 'red' if 'Bearish' in signal else 'gray'
        st.markdown(f"• <span style='color:{signal_color}'>{signal}</span>", unsafe_allow_html=True)
    
    # Recent News Impact
    st.subheader("Recent News")
    for news in analysis['recent_news']:
        st.markdown(f"• {news}")
    
    # Position Sizing Recommendation
    st.header("💰 Position Sizing")
    st.markdown(f"**Recommended Position Size:** {analysis['ai_recommendation']['position_size']}")
    
    # Last Updated
    st.sidebar.info(f"Last Updated: {analysis['timestamp']}")
    
    # Refresh button
    if st.button("🔄 Refresh Analysis"):
        st.experimental_rerun()
