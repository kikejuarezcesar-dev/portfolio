import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ForecastModel:
    """Clase base para todos los modelos de pronóstico"""
    
    def __init__(self):
        self.model = None
        self.model_name = "Base"
        self.last_date = None
        self.data_index = None
    
    def train(self, data):
        """Método para entrenar el modelo"""
        self.data_index = data.index
        self.last_date = data.index[-1]
        raise NotImplementedError("Método train debe ser implementado")
    
    def predict(self, steps=30):
        """Método para hacer predicciones"""
        raise NotImplementedError("Método predict debe ser implementado")
    
    def _create_future_dates(self, steps):
        """Crear fechas futuras para el pronóstico"""
        if isinstance(self.last_date, pd.Timestamp):
            # Si es una serie temporal con fechas
            if pd.infer_freq(self.data_index):  # Si tiene frecuencia definida
                future_dates = pd.date_range(
                    start=self.last_date + pd.Timedelta(days=1),
                    periods=steps,
                    freq=pd.infer_freq(self.data_index)
                )
            else:
                # Frecuencia diaria por defecto
                future_dates = pd.date_range(
                    start=self.last_date + timedelta(days=1),
                    periods=steps,
                    freq='D'
                )
            return future_dates
        else:
            # Si es índice numérico, devolver números consecutivos
            last_idx = self.data_index[-1] if hasattr(self.data_index[-1], 'real') else len(self.data_index)
            return range(last_idx + 1, last_idx + steps + 1)
    
    def get_model_info(self):
        """Información del modelo"""
        return {
            "name": self.model_name,
            "parameters": str(self.model.get_params()) if hasattr(self.model, 'get_params') else "N/A"
        }

class ARIMAModel(ForecastModel):
    """Modelo ARIMA para pronósticos de series temporales"""
    
    def __init__(self, order=(1, 1, 1)):
        super().__init__()
        self.order = order
        self.model_name = f"ARIMA{order}"
        
    def train(self, data):
        """Entrenar modelo ARIMA"""
        from statsmodels.tsa.arima.model import ARIMA
        
        try:
            self.data_index = data.index
            self.last_date = data.index[-1]
            self.model = ARIMA(data, order=self.order)
            self.fitted_model = self.model.fit()
            return True
        except Exception as e:
            print(f"Error entrenando ARIMA: {e}")
            return False
    
    def predict(self, steps=30):
        """Hacer predicciones"""
        if not hasattr(self, 'fitted_model'):
            return None
            
        try:
            forecast = self.fitted_model.get_forecast(steps=steps)
            predictions = forecast.predicted_mean
            confidence_intervals = forecast.conf_int()
            
            # Crear índice de fechas para el forecast
            future_dates = self._create_future_dates(steps)
            
            return {
                'predictions': pd.Series(predictions.values, index=future_dates),
                'confidence_intervals': pd.DataFrame({
                    'lower': confidence_intervals.iloc[:, 0].values,
                    'upper': confidence_intervals.iloc[:, 1].values
                }, index=future_dates),
                'model_info': self.get_model_info()
            }
        except Exception as e:
            print(f"Error prediciendo con ARIMA: {e}")
            return None

class LinearRegressionModel(ForecastModel):
    """Modelo de regresión lineal simple"""
    
    def __init__(self):
        super().__init__()
        self.model_name = "Linear Regression"
        
    def train(self, data):
        """Entrenar regresión lineal"""
        from sklearn.linear_model import LinearRegression
        
        try:
            self.data_index = data.index
            self.last_date = data.index[-1]
            
            # Crear características temporales
            X = np.arange(len(data)).reshape(-1, 1)
            y = data.values
            
            self.model = LinearRegression()
            self.model.fit(X, y)
            self.X_train = X
            return True
        except Exception as e:
            print(f"Error entrenando regresión lineal: {e}")
            return False
    
    def predict(self, steps=30):
        """Hacer predicciones"""
        if self.model is None:
            return None
            
        try:
            # Crear características futuras
            last_index = len(self.X_train)
            X_future = np.arange(last_index, last_index + steps).reshape(-1, 1)
            
            predictions = self.model.predict(X_future)
            
            # Calcular intervalo de confianza simple
            y_pred_train = self.model.predict(self.X_train)
            std_dev = np.std(y_pred_train - self.model.predict(self.X_train))
            
            # Crear índice de fechas para el forecast
            future_dates = self._create_future_dates(steps)
            
            return {
                'predictions': pd.Series(predictions, index=future_dates),
                'confidence_intervals': pd.DataFrame({
                    'lower': predictions - 1.96 * std_dev,
                    'upper': predictions + 1.96 * std_dev
                }, index=future_dates),
                'model_info': self.get_model_info()
            }
        except Exception as e:
            print(f"Error prediciendo con regresión lineal: {e}")
            return None

class ExponentialSmoothingModel(ForecastModel):
    """Suavizado exponencial para series temporales"""
    
    def __init__(self, trend='add', seasonal=None):
        super().__init__()
        self.trend = trend
        self.seasonal = seasonal
        self.model_name = "Exponential Smoothing"
        
    def train(self, data):
        """Entrenar suavizado exponencial"""
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        
        try:
            self.data_index = data.index
            self.last_date = data.index[-1]
            
            self.model = ExponentialSmoothing(
                data, 
                trend=self.trend, 
                seasonal=self.seasonal,
                seasonal_periods=30 if self.seasonal else None
            )
            self.fitted_model = self.model.fit()
            return True
        except Exception as e:
            print(f"Error entrenando suavizado exponencial: {e}")
            return False
    
    def predict(self, steps=30):
        """Hacer predicciones"""
        if not hasattr(self, 'fitted_model'):
            return None
            
        try:
            forecast = self.fitted_model.forecast(steps)
            
            # Para exponential smoothing, usamos un intervalo de confianza simple
            std_dev = np.std(self.fitted_model.fittedvalues - self.fitted_model.fittedvalues)
            
            # Crear índice de fechas para el forecast
            future_dates = self._create_future_dates(steps)
            
            return {
                'predictions': pd.Series(forecast.values, index=future_dates),
                'confidence_intervals': pd.DataFrame({
                    'lower': forecast - 1.96 * std_dev,
                    'upper': forecast + 1.96 * std_dev
                }, index=future_dates),
                'model_info': self.get_model_info()
            }
        except Exception as e:
            print(f"Error prediciendo con suavizado exponencial: {e}")
            return None

class ForecastManager:
    """Gestor de modelos de pronóstico"""
    
    def __init__(self):
        self.models = {
            'arima': ARIMAModel(order=(1, 1, 1)),
            'linear': LinearRegressionModel(),
            'exponential': ExponentialSmoothingModel(trend='add')
        }
        self.current_model = 'arima'
        self.historical_data = None
    
    def set_model(self, model_name):
        """Seleccionar modelo actual"""
        if model_name in self.models:
            self.current_model = model_name
            return True
        return False
    
    def get_available_models(self):
        """Obtener lista de modelos disponibles"""
        return list(self.models.keys())
    
    def train_model(self, data, model_name=None):
        """Entrenar modelo con datos históricos"""
        if model_name:
            self.set_model(model_name)
        
        self.historical_data = data
        return self.models[self.current_model].train(data)
    
    def make_forecast(self, steps=30, model_name=None):
        """Hacer pronóstico"""
        if model_name:
            self.set_model(model_name)
        
        if self.historical_data is None:
            return None
        
        return self.models[self.current_model].predict(steps)
    
    def get_model_performance(self, test_data):
        """Evaluar performance del modelo"""
        # TODO: Implementar métricas de evaluación
        return {"mae": 0, "mse": 0, "rmse": 0}

# Instancia global
forecast_manager = ForecastManager()