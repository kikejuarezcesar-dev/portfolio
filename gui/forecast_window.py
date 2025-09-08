from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QComboBox, QLabel, QLineEdit, QGroupBox, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta

from api.yahoo_finance import get_historical_data
from forecast.models import forecast_manager

class ForecastCanvas(FigureCanvasQTAgg):
    """Canvas para mostrar gráficos de pronósticos"""
    
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
    def plot_forecast(self, historical_data, forecast_data, symbol):
        """Plotear datos históricos y pronóstico"""
        self.axes.clear()
        
        # Plot historical data
        historical_data.plot(ax=self.axes, label='Histórico', color='blue', linewidth=2)
        
        if forecast_data:
            # Plot predictions
            forecast_data['predictions'].plot(
                ax=self.axes, 
                label='Pronóstico', 
                color='red', 
                linewidth=2,
                linestyle='--'
            )
            
            # Plot confidence intervals
            if 'confidence_intervals' in forecast_data:
                self.axes.fill_between(
                    forecast_data['predictions'].index,
                    forecast_data['confidence_intervals']['lower'],
                    forecast_data['confidence_intervals']['upper'],
                    color='red', 
                    alpha=0.2,
                    label='Intervalo de confianza (95%)'
                )
        
        self.axes.set_title(f'Pronóstico de Precios - {symbol}', fontsize=14, fontweight='bold')
        self.axes.set_xlabel('Fecha', fontsize=12)
        self.axes.set_ylabel('Precio ($)', fontsize=12)
        self.axes.legend(loc='upper left')
        self.axes.grid(True, alpha=0.3)
        plt.setp(self.axes.xaxis.get_majorticklabels(), rotation=45)
        
        self.fig.tight_layout()
        self.draw()

class ForecastWindow(QWidget):
    """Ventana de pronósticos de precios"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Pronósticos de Precios")
        self.setGeometry(300, 300, 1000, 700)
        self.current_symbol = None
        self.historical_data = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel("🔮 Pronósticos de Precios - Análisis Predictivo")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #7b1fa2; 
            padding: 10px;
            background-color: #2d2d2d;
            border-radius: 8px;
        """)
        layout.addWidget(title_label)
        
        # Controles de entrada
        input_group = QGroupBox("Configuración de Pronóstico")
        input_layout = QVBoxLayout()
        
        # Símbolo y período
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Símbolo:"))
        
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Ej: AAPL, MSFT, BTC-USD")
        symbol_layout.addWidget(self.symbol_input)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["3mo", "6mo", "1y", "2y"])
        self.period_combo.setCurrentText("6mo")
        symbol_layout.addWidget(QLabel("Período histórico:"))
        symbol_layout.addWidget(self.period_combo)
        
        input_layout.addLayout(symbol_layout)
        
        # Modelo y steps
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Modelo:"))
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(forecast_manager.get_available_models())
        model_layout.addWidget(self.model_combo)
        
        model_layout.addWidget(QLabel("Días a predecir:"))
        self.steps_spinbox = QSpinBox()
        self.steps_spinbox.setRange(7, 365)
        self.steps_spinbox.setValue(30)
        model_layout.addWidget(self.steps_spinbox)
        
        input_layout.addLayout(model_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📥 Cargar Datos")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        self.load_btn.clicked.connect(self.load_data)
        button_layout.addWidget(self.load_btn)
        
        self.forecast_btn = QPushButton("🔮 Generar Pronóstico")
        self.forecast_btn.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2e7d32; }
        """)
        self.forecast_btn.clicked.connect(self.generate_forecast)
        self.forecast_btn.setEnabled(False)
        button_layout.addWidget(self.forecast_btn)
        
        input_layout.addLayout(button_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Gráfico
        self.canvas = ForecastCanvas(self)
        layout.addWidget(self.canvas)
        
        # Información del modelo
        info_group = QGroupBox("Información del Modelo")
        info_layout = QVBoxLayout()
        
        self.model_info_label = QLabel("Selecciona un símbolo y genera un pronóstico...")
        self.model_info_label.setStyleSheet("color: #bdbdbd; padding: 10px;")
        self.model_info_label.setWordWrap(True)
        info_layout.addWidget(self.model_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
    def load_data(self):
        """Cargar datos históricos"""
        symbol = self.symbol_input.text().strip().upper()
        period = self.period_combo.currentText()
        
        if not symbol:
            QMessageBox.warning(self, "Error", "Por favor ingresa un símbolo válido.")
            return
        
        try:
            self.current_symbol = symbol
            self.historical_data = get_historical_data(symbol, period)
            
            if self.historical_data is None or self.historical_data.empty:
                QMessageBox.warning(self, "Error", f"No se pudieron obtener datos para {symbol}.")
                return
            
            # Usar precios de cierre
            close_prices = self.historical_data['Close']
            
            # Plotear datos históricos
            self.canvas.plot_forecast(close_prices, None, symbol)
            self.debug_dates()
            
            self.forecast_btn.setEnabled(True)
            self.model_info_label.setText(f"Datos cargados: {symbol} | {len(close_prices)} registros | Período: {period}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar datos: {str(e)}")
    
    def generate_forecast(self):
        """Generar pronóstico"""
        if self.historical_data is None or self.current_symbol is None:
            return
        
        try:
            # Obtener configuración
            model_name = self.model_combo.currentText()
            steps = self.steps_spinbox.value()
            close_prices = self.historical_data['Close']
            
            # Entrenar modelo
            success = forecast_manager.train_model(close_prices, model_name)
            
            if not success:
                QMessageBox.warning(self, "Error", "Error al entrenar el modelo.")
                return
            
            # Generar pronóstico
            forecast_data = forecast_manager.make_forecast(steps)
            
            if forecast_data is None:
                QMessageBox.warning(self, "Error", "Error al generar el pronóstico.")
                return
            
            # Verificar que los índices estén alineados
            historical_index = close_prices.index
            forecast_index = forecast_data['predictions'].index
            
            print(f"Índice histórico: {historical_index[-5:]}")
            print(f"Índice forecast: {forecast_index[:5]}")
            
            # Plotear resultados
            self.canvas.plot_forecast(close_prices, forecast_data, self.current_symbol)
            
            # Mostrar información del modelo
            model_info = forecast_data.get('model_info', {})
            # Porcentaje de cambio
            last_price = close_prices.iloc[-1]
            forecast_price = forecast_data['predictions'].iloc[-1]
            change_pct = ((forecast_price - last_price) / last_price) * 100

            info_text = f"""
            📊 Modelo: {model_info.get('name', 'N/A')}
            ⚙️ Parámetros: {model_info.get('parameters', 'N/A')}
            🔮 Días pronosticados: {steps}
            📈 Último precio: ${last_price:.2f}
            🎯 Precio proyectado (día {steps}): ${forecast_price:.2f}
            📉 Cambio proyectado: {change_pct:+.2f}%
            """
            
            self.model_info_label.setText(info_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar pronóstico: {str(e)}")
            import traceback
            traceback.print_exc()

    def debug_dates(self):
        """Función de debugging para ver las fechas"""
        if self.historical_data is not None:
            close_prices = self.historical_data['Close']
            print("=== DEBUG: FECHAS HISTÓRICAS ===")
            print(f"Tipo de índice: {type(close_prices.index)}")
            print(f"Primeras 5 fechas: {close_prices.index[:5]}")
            print(f"Últimas 5 fechas: {close_prices.index[-5:]}")
            print(f"Frecuencia: {pd.infer_freq(close_prices.index)}")