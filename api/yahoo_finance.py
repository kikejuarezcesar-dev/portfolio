import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os
import numpy as np
from scipy import stats

class YahooFinanceAPI:

    def __init__(self):
        self.cache_dir = "price_cache"
        self.cache_duration = 300
        self.usd_mxn_rate = None
        self.usd_mxn_cache_time = None
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Crea el directorio de cache si no existe"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, symbol):
        """Obtiene la ruta del archivo de cache para un símbolo"""
        return os.path.join(self.cache_dir, f"{symbol}.json")
    
    def _is_cache_valid(self, cache_path):
        """Verifica si el cache es válido"""
        if not os.path.exists(cache_path):
            return False
        
        file_time = os.path.getmtime(cache_path)
        current_time = time.time()
        return (current_time - file_time) < self.cache_duration
    
    def get_usd_mxn_rate(self, force_update=False):
        """
        Obtener tipo de cambio USD/MXN con cache
        """
        current_time = time.time()
        
        if (self.usd_mxn_rate is not None and 
            self.usd_mxn_cache_time is not None and
            (current_time - self.usd_mxn_cache_time) < self.cache_duration and
            not force_update):
            return self.usd_mxn_rate
        
        try:
            ticker = yf.Ticker("USDMXN=X")
            info = ticker.info
            
            current_rate = (info.get('currentPrice') or 
                           info.get('regularMarketPrice') or 
                           info.get('ask') or 
                           info.get('bid') or 
                           0)
            
            if current_rate == 0:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_rate = hist['Close'].iloc[-1]
            
            self.usd_mxn_rate = current_rate
            self.usd_mxn_cache_time = current_time
            
            print(f"💰 Tipo de cambio USD/MXN actualizado: {current_rate:.2f}")
            return current_rate
            
        except Exception as e:
            print(f"Error obteniendo tipo de cambio USD/MXN: {e}")
            return 17.0  # Valor por defecto
    
    def get_current_price(self, symbol, currency="USD"):
        """
        Obtener precio en la moneda especificada
        """
        cache_path = self._get_cache_path(symbol)
        
        # Verificar cache primero
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    usd_price = data['price']
            except:
                usd_price = None
        else:
            usd_price = None
        
        if usd_price is None:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                current_price = (info.get('currentPrice') or 
                               info.get('regularMarketPrice') or 
                               info.get('ask') or 
                               info.get('bid') or 
                               0)
                
                if current_price == 0:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                
                # Guardar en cache
                cache_data = {
                    'price': current_price,
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol
                }
                
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f)
                
                usd_price = current_price
                
            except Exception as e:
                print(f"Error obteniendo precio de {symbol}: {e}")
                return None
        
        # Convertir a MXN si se solicita
        if currency.upper() == "MXN":
            exchange_rate = self.get_usd_mxn_rate()
            return usd_price * exchange_rate
        
        return usd_price
    
    def get_historical_prices(self, symbol, period="1mo"):
        """
        Obtiene precios históricos
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist
        except Exception as e:
            print(f"Error obteniendo histórico de {symbol}: {e}")
            return None
    
    def get_multiple_prices(self, symbols, currency="USD"):
        """
        Obtener precios en la moneda especificada
        """
        prices = {}
        exchange_rate = self.get_usd_mxn_rate() if currency.upper() == "MXN" else 1.0
        
        for symbol in symbols:
            price = self.get_current_price(symbol, "USD")  # Siempre obtener en USD primero
            if price is not None:
                prices[symbol] = price * exchange_rate
            time.sleep(0.1)
        
        return prices
    
    def validate_symbol(self, symbol):
        """Verifica si un símbolo es válido en Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info is not None and len(info) > 0
        except:
            return False
        
def get_historical_data(symbol, period="6mo"):
    """Obtener datos históricos para análisis técnico"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        # Verificar que tenemos datos
        if hist.empty:
            print(f"Warning: No hay datos históricos para {symbol}")
            return None
        print(f"Datos históricos obtenidos para {symbol}: {len(hist)} registros")
        return hist
        
    except Exception as e:
        print(f"Error obteniendo histórico de {symbol}: {e}")
        return None

def get_multiple_historical_data(symbols, period="6mo"):
    """Obtener datos históricos para múltiples símbolos"""
    historical_data = {}
    for symbol in symbols:
        data = get_historical_data(symbol, period)
        if data is not None:
            historical_data[symbol] = data
        time.sleep(0.3)  # Evitar rate limiting de Yahoo Finance
    return historical_data
    
def get_intraday_data(symbol, interval="15m", period="1d"):
    """
    Obtener datos intradía para análisis de corto plazo
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        return hist
    except Exception as e:
        print(f"Error obteniendo datos intradía de {symbol}: {e}")
        return None
    
def get_detailed_info(symbol):
    """Obtener información detallada de un símbolo"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info
    except Exception as e:
        print(f"Error obteniendo info de {symbol}: {e}")
        return None

def calculate_confidence_interval(prices, window=60, confidence=0.90):
    """
    Calcular intervalo de confianza para media móvil
    Returns: (media_movil, lower_band, upper_band)
    """
    try:
        moving_avg = prices.rolling(window=window).mean()
        moving_std = prices.rolling(window=window).std()
        
        # Calcular z-score para el nivel de confianza
        z_score = stats.norm.ppf((1 + confidence) / 2)
        
        # Calcular bandas de confianza
        margin_error = z_score * (moving_std / np.sqrt(window))
        lower_band = moving_avg - margin_error
        upper_band = moving_avg + margin_error
        
        return moving_avg, lower_band, upper_band
        
    except Exception as e:
        print(f"Error calculando intervalo de confianza: {e}")
        return None, None, None

def get_alert_conditions(symbol, window=60, confidence=0.90):
    """
    Obtener condiciones para alertas basadas en intervalo de confianza
    Returns: dict con current_price, moving_avg, lower_band, upper_band, alert_message
    """
    try:
        # Obtener datos históricos
        historical_data = get_historical_data(symbol, "6mo")
        if historical_data is None or historical_data.empty:
            return None
        
        # Calcular intervalo de confianza
        moving_avg, lower_band, upper_band = calculate_confidence_interval(
            historical_data['Close'], window, confidence
        )
        
        # Obtener precio actual
        current_price = get_current_price(symbol)
        if current_price is None:
            return None
        
        # Verificar si hay suficientes datos
        if len(moving_avg) < window or pd.isna(lower_band.iloc[-1]):
            return None
        
        # Determinar alerta
        alert_message = None
        alert_type = None
        
        if current_price < lower_band.iloc[-1]:
            deviation_pct = ((lower_band.iloc[-1] - current_price) / lower_band.iloc[-1]) * 100
            alert_message = (f"🔻 {symbol} está {deviation_pct:.1f}% POR DEBAJO del intervalo inferior")
            alert_type = "buy_opportunity"
        elif current_price > (lower_band.iloc[-1] * 1.05):
            deviation_pct = ((current_price - (lower_band.iloc[-1] * 1.05)) / (lower_band.iloc[-1] * 1.05)) * 100
            alert_message = f"🚀 {symbol} está {deviation_pct:.1f}% POR ENCIMA del intervalo inferior"
            alert_type = "overbought"
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'moving_avg': moving_avg.iloc[-1],
            'lower_band': lower_band.iloc[-1],
            'upper_band': upper_band.iloc[-1],
            'alert_message': alert_message,
            'alert_type': alert_type,
            'window': window,
            'confidence': confidence
        }
        
    except Exception as e:
        print(f"Error obteniendo condiciones de alerta para {symbol}: {e}")
        return None

def get_usd_mxn_rate():
    """
    Obtener el tipo de cambio USD/MXN actual de Yahoo Finance
    """
    try:
        # USDMXN=X es el símbolo para USD/MXN en Yahoo Finance
        ticker = yf.Ticker("USDMXN=X")
        info = ticker.info
        
        # Intentar diferentes campos para el precio
        current_rate = (info.get('currentPrice') or 
                       info.get('regularMarketPrice') or 
                       info.get('ask') or 
                       info.get('bid') or 
                       0)
        
        if current_rate == 0:
            # Fallback: obtener del historial del día
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_rate = hist['Close'].iloc[-1]
        
        print(f"💰 Tipo de cambio USD/MXN obtenido: {current_rate}")
        return current_rate
        
    except Exception as e:
        print(f"Error obteniendo tipo de cambio USD/MXN: {e}")
        return 17.0  # Valor por defecto en caso de error

def get_current_price_mxn(symbol):
    """
    Obtener precio en MXN de un símbolo
    """
    usd_price = get_current_price(symbol)
    if usd_price is None:
        return None
    
    exchange_rate = get_usd_mxn_rate()
    return usd_price * exchange_rate

def get_multiple_prices_mxn(symbols):
    """
    Obtener precios en MXN de múltiples símbolos
    """
    usd_prices = get_multiple_prices(symbols)
    exchange_rate = get_usd_mxn_rate()
    
    mxn_prices = {}
    for symbol, usd_price in usd_prices.items():
        mxn_prices[symbol] = usd_price * exchange_rate
    
    return mxn_prices

def get_historical_data_mxn(symbol, period="6mo"):
    """
    Obtener datos históricos en MXN
    """
    historical_data = get_historical_data(symbol, period)
    if historical_data is None:
        return None
    
    # Obtener tipo de cambio histórico USD/MXN
    usdmxn_data = get_historical_data("USDMXN=X", period)
    
    if usdmxn_data is None:
        print("Warning: No se pudieron obtener datos históricos de USD/MXN")
        return historical_data
    
    # Convertir precios a MXN
    # Alinear los índices de fechas
    aligned_data = historical_data.copy()
    
    for column in ['Open', 'High', 'Low', 'Close']:
        if column in historical_data.columns:
            # Convertir usando el tipo de cambio del mismo día
            aligned_data[column] = historical_data[column] * usdmxn_data['Close']
    
    # Convertir volumen si existe
    if 'Volume' in historical_data.columns:
        aligned_data['Volume'] = historical_data['Volume']
    
    return aligned_data
    
# Instancia global para usar en la aplicación
yahoo_api = YahooFinanceAPI()

# Funciones de conveniencia
def get_current_price(symbol):
    return yahoo_api.get_current_price(symbol)

def get_multiple_prices(symbols):
    return yahoo_api.get_multiple_prices(symbols)

def validate_symbol(symbol):
    return yahoo_api.validate_symbol(symbol)