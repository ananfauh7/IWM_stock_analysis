import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

def predict_price_range(df: pd.DataFrame) -> dict:
    """
    Predict next day's price range using Random Forest
    """
    try:
        # Feature engineering
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['Daily_Return'] = df['Close'].pct_change()
        df['Volatility'] = df['Daily_Return'].rolling(window=20).std()
        
        # Drop NaN values
        df = df.dropna()
        
        # Create features
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_5', 'SMA_20', 'Volatility']
        X = df[features].values
        y_low = df['Low'].values
        y_high = df['High'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train models
        model_low = RandomForestRegressor(n_estimators=100, random_state=42)
        model_high = RandomForestRegressor(n_estimators=100, random_state=42)
        
        model_low.fit(X_scaled[:-1], y_low[1:])
        model_high.fit(X_scaled[:-1], y_high[1:])
        
        # Make predictions
        last_data = X_scaled[-1:]
        predicted_low = model_low.predict(last_data)[0]
        predicted_high = model_high.predict(last_data)[0]
        
        return {
            'low': predicted_low,
            'high': predicted_high
        }
    except Exception as e:
        return {
            'low': df['Low'].iloc[-1],
            'high': df['High'].iloc[-1]
        }
