import streamlit as st
import base64
import json
from datetime import datetime
import plotly.graph_objects as go

class ShareManager:
    @staticmethod
    def save_annotation(fig: go.Figure, annotation_text: str, x_pos: str, y_pos: float) -> go.Figure:
        """
        Add annotation to the chart
        """
        fig.add_annotation(
            x=x_pos,
            y=y_pos,
            text=annotation_text,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        )
        return fig
    
    @staticmethod
    def generate_share_link(symbol: str, annotations: list, metrics: dict) -> str:
        """
        Generate a shareable link with stock insights
        """
        share_data = {
            'symbol': symbol,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'annotations': annotations,
            'key_metrics': {
                'price': metrics.get('current_price', 0),
                'day_change': metrics.get('day_change', 0),
                'sentiment_score': metrics.get('sentiment_score', 0)
            }
        }
        
        # Convert to base64 for URL-safe sharing
        share_json = json.dumps(share_data)
        share_code = base64.urlsafe_b64encode(share_json.encode()).decode()
        return share_code
    
    @staticmethod
    def decode_share_link(share_code: str) -> dict:
        """
        Decode a shared link back into data
        """
        try:
            share_json = base64.urlsafe_b64decode(share_code.encode()).decode()
            return json.loads(share_json)
        except:
            return None
