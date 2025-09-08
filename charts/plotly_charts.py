import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class TechnicalCharts:
    def __init__(self):
        self.chart_dir = "charts_output"
        os.makedirs(self.chart_dir, exist_ok=True)
    
    def create_portfolio_performance_chart(self, historical_data):
        """Gráfico de evolución del portafolio"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical_data['date'],
            y=historical_data['value'],
            mode='lines',
            name='Valor Portafolio',
            line=dict(color='#00c853', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 200, 83, 0.1)'
        ))
        
        fig.update_layout(
            title='Evolución del Portafolio',
            xaxis_title='Fecha',
            yaxis_title='Valor ($)',
            template='plotly_dark',
            hovermode='x unified',
            showlegend=True,
            height=500
        )
        
        return fig
    
    def create_asset_allocation_chart(self, portfolio_data):
        """Gráfico de torta - Distribución de activos"""
        symbols = [asset['symbol'] for asset in portfolio_data]
        values = [asset['current_value'] for asset in portfolio_data]
        
        fig = go.Figure(data=[go.Pie(
            labels=symbols,
            values=values,
            hole=.3,
            marker_colors=px.colors.qualitative.Set3
        )])
        
        fig.update_layout(
            title='Distribución de Activos',
            template='plotly_dark',
            height=400
        )
        
        return fig
    
    def create_technical_chart(self, symbol, historical_prices):
        """Gráfico técnico completo con indicadores"""
        # Crear subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(f'{symbol} - Precio', 'Volumen', 'RSI', 'MACD'),
            row_width=[0.4, 0.2, 0.2, 0.2]
        )
        
        # Gráfico de velas (Candlestick)
        fig.add_trace(go.Candlestick(
            x=historical_prices.index,
            open=historical_prices['Open'],
            high=historical_prices['High'],
            low=historical_prices['Low'],
            close=historical_prices['Close'],
            name='Precio'
        ), row=1, col=1)
        
        # Volumen
        fig.add_trace(go.Bar(
            x=historical_prices.index,
            y=historical_prices['Volume'],
            name='Volumen',
            marker_color='#1f77b4'
        ), row=2, col=1)
        
        # RSI
        rsi = self.calculate_rsi(historical_prices['Close'])
        fig.add_trace(go.Scatter(
            x=historical_prices.index,
            y=rsi,
            name='RSI',
            line=dict(color='#ff6b00', width=2)
        ), row=3, col=1)
        
        # Líneas de sobrecompra/sobreventa RSI
        fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="red")
        fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="green")
        
        # MACD
        macd, signal, histogram = self.calculate_macd(historical_prices['Close'])
        fig.add_trace(go.Scatter(
            x=historical_prices.index,
            y=macd,
            name='MACD',
            line=dict(color='#00b0ff', width=2)
        ), row=4, col=1)
        
        fig.add_trace(go.Scatter(
            x=historical_prices.index,
            y=signal,
            name='Señal',
            line=dict(color='#ff4081', width=2)
        ), row=4, col=1)
        
        fig.add_trace(go.Bar(
            x=historical_prices.index,
            y=histogram,
            name='Histograma',
            marker_color=np.where(histogram < 0, 'red', 'green')
        ), row=4, col=1)
        
        fig.update_layout(
            title=f'Análisis Técnico - {symbol}',
            template='plotly_dark',
            height=800,
            showlegend=True
        )
        
        # Ocultar rangeselector en subplots
        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
        fig.update_xaxes(rangeslider_visible=False, row=2, col=1)
        fig.update_xaxes(rangeslider_visible=False, row=3, col=1)
        fig.update_xaxes(rangeslider_visible=False, row=4, col=1)
        
        return fig
    
    def calculate_rsi(self, prices, period=14):
        """Calcular RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcular MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        return macd, macd_signal, macd_histogram
    
    def save_chart(self, fig, filename):
        """Guardar gráfico como imagen"""
        path = os.path.join(self.chart_dir, filename)
        fig.write_image(path, width=1200, height=800)
        return path
    
    def show_chart(self, fig):
        """Mostrar gráfico en navegador"""
        fig.show()

# Instancia global
tech_charts = TechnicalCharts()