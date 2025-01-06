# IWM Stock Analysis Platform

An advanced AI-powered stock analysis platform specializing in intelligent predictive analytics for the Russell 2000 ETF (IWM), with enhanced market insights and sophisticated options trading capabilities.

## Features

- **Real-time Stock Analysis**
  - Live price tracking and technical indicators
  - Historical data visualization with interactive charts
  - Advanced price prediction using machine learning models

- **Market Sentiment Analysis**
  - Real-time news sentiment analysis
  - Integration with multiple data sources (Yahoo Finance, Google Finance, MarketWatch)
  - Sentiment impact on price movement analysis

- **Options Strategy Recommendations**
  - Weekly options strategies based on market conditions
  - Technical and sentiment-based strategy selection
  - Risk/reward analysis with probability calculations
  - Historical black swan event analysis

- **Price Factors Analysis**
  - Comprehensive technical indicators
  - Volatility regime analysis
  - Black swan event impact assessment
  - Market sentiment integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/IWM_stock_analysis.git
cd IWM_stock_analysis
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your API keys:
```env
NASDAQ_API_KEY=your_api_key_here
```

## Usage

Run the Streamlit application:
```bash
streamlit run main.py
```

Access the application through your web browser at: `http://localhost:5000`

## Dependencies

- Python 3.11+
- Streamlit
- Pandas
- NumPy
- Plotly
- yfinance
- scikit-learn
- TextBlob
- Trafilatura

## Features Documentation

### Stock Analysis Dashboard
- Real-time price tracking
- Technical indicators visualization
- Historical data analysis
- Price prediction using machine learning

### Price Factors Analysis
- Technical indicator analysis
- Market sentiment integration
- Volatility regime assessment
- Black swan event comparison

### Options Strategy
- Weekly strategy recommendations
- Risk/reward analysis
- Sentiment-based adjustments
- Historical volatility impact

## Configuration

The application can be configured through `.streamlit/config.toml`:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
