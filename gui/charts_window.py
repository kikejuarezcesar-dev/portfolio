from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QComboBox, QLabel, QTabWidget, QSizePolicy, QMessageBox,
                             QApplication)
from PyQt5.QtCore import Qt
import plotly.express as px
import webbrowser
import os
from datetime import datetime
import pandas as pd
import numpy as np

from charts.plotly_charts import tech_charts
from api.yahoo_finance import get_historical_data

class ChartsWindow(QWidget):
    def __init__(self, portfolio_data):
        super().__init__()
        self.portfolio_data = portfolio_data
        self.setWindowTitle("Análisis Técnico - Gráficos")
        self.setGeometry(200, 200, 600, 400)
        self.charts_dir = "charts_html"
        os.makedirs(self.charts_dir, exist_ok=True)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("📊 Generador de Gráficos de Análisis Técnico")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #64b5f6; padding: 10px;")
        layout.addWidget(title_label)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.symbol_combo = QComboBox()
        symbols = [asset['symbol'] for asset in self.portfolio_data]
        self.symbol_combo.addItems(symbols)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["1mo", "3mo", "6mo", "1y", "2y"])
        self.period_combo.setCurrentText("6mo")
        
        controls_layout.addWidget(QLabel("Símbolo:"))
        controls_layout.addWidget(self.symbol_combo)
        controls_layout.addWidget(QLabel("Período:"))
        controls_layout.addWidget(self.period_combo)
        
        layout.addLayout(controls_layout)
        
        # Botones de gráficos
        buttons_layout = QHBoxLayout()
        
        self.tech_btn = QPushButton("📈 Gráfico Técnico Completo")
        self.tech_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.tech_btn.clicked.connect(self.show_technical_chart)
        buttons_layout.addWidget(self.tech_btn)
        
        self.performance_btn = QPushButton("🚀 Rendimiento del Portafolio")
        self.performance_btn.setStyleSheet("""
            QPushButton {
                background-color: #00c853;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00e676;
            }
        """)
        self.performance_btn.clicked.connect(self.show_performance_chart)
        buttons_layout.addWidget(self.performance_btn)
        
        self.allocation_btn = QPushButton("🥧 Distribución de Activos")
        self.allocation_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6d00;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff9100;
            }
        """)
        self.allocation_btn.clicked.connect(self.show_allocation_chart)
        buttons_layout.addWidget(self.allocation_btn)
        
        layout.addLayout(buttons_layout)
        
        # Área de información
        self.info_label = QLabel("Selecciona el tipo de gráfico que deseas generar.\nSe abrirá automáticamente en tu navegador web.")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #bdbdbd; font-size: 12px; padding: 20px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Botón para abrir carpeta de gráficos
        self.open_folder_btn = QPushButton("📂 Abrir Carpeta de Gráficos")
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #9c27b0;
            }
        """)
        self.open_folder_btn.clicked.connect(self.open_charts_folder)
        layout.addWidget(self.open_folder_btn)
        
    def show_technical_chart(self):
        symbol = self.symbol_combo.currentText()
        period = self.period_combo.currentText()
        
        try:
            self.info_label.setText(f"📡 Obteniendo datos de {symbol}...")
            QApplication.processEvents()
            
            historical_data = get_historical_data(symbol, period)
            if historical_data is not None and not historical_data.empty:
                self.info_label.setText(f"🎨 Generando gráfico técnico de {symbol}...")
                QApplication.processEvents()
                
                fig = tech_charts.create_technical_chart(symbol, historical_data)
                
                # Guardar como HTML
                filename = f"technical_{symbol}_{period}.html"
                filepath = os.path.join(self.charts_dir, filename)
                fig.write_html(filepath)
                
                # Abrir en navegador
                webbrowser.open(f"file://{os.path.abspath(filepath)}")
                
                self.info_label.setText(f"✅ Gráfico técnico de {symbol} generado!\nAbierto en tu navegador.")
            else:
                QMessageBox.warning(self, "Error", f"No se pudieron obtener datos para {symbol}")
                self.info_label.setText("❌ Error al obtener datos. Intenta con otro símbolo.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar gráfico: {str(e)}")
            self.info_label.setText("❌ Error al generar el gráfico.")
            print(f"Error en show_technical_chart: {e}")
    
    def show_performance_chart(self):
        try:
            self.info_label.setText("📊 Generando gráfico de rendimiento...")
            QApplication.processEvents()
            
            # Datos de ejemplo - deberías implementar histórico real
            portfolio_history = self.get_portfolio_history()
            fig = tech_charts.create_portfolio_performance_chart(portfolio_history)
            
            filename = "portfolio_performance.html"
            filepath = os.path.join(self.charts_dir, filename)
            fig.write_html(filepath)
            
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
            self.info_label.setText("✅ Gráfico de rendimiento generado!\nAbierto en tu navegador.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar gráfico de rendimiento: {str(e)}")
            self.info_label.setText("❌ Error al generar gráfico de rendimiento.")
            print(f"Error en show_performance_chart: {e}")
    
    def show_allocation_chart(self):
        try:
            self.info_label.setText("🥧 Generando gráfico de distribución...")
            QApplication.processEvents()
            
            fig = tech_charts.create_asset_allocation_chart(self.portfolio_data)
            
            filename = "asset_allocation.html"
            filepath = os.path.join(self.charts_dir, filename)
            fig.write_html(filepath)
            
            webbrowser.open(f"file://{os.path.abspath(filepath)}")
            self.info_label.setText("✅ Gráfico de distribución generado!\nAbierto en tu navegador.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar gráfico de distribución: {str(e)}")
            self.info_label.setText("❌ Error al generar gráfico de distribución.")
            print(f"Error en show_allocation_chart: {e}")
    
    def get_portfolio_history(self):
        """Simular datos históricos del portafolio"""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Simular crecimiento basado en los datos actuales
        current_value = sum(asset['current_value'] for asset in self.portfolio_data)
        values = np.linspace(current_value * 0.8, current_value, 30)
        
        return pd.DataFrame({'date': dates, 'value': values})
    
    def open_charts_folder(self):
        """Abrir carpeta con gráficos generados"""
        try:
            abs_path = os.path.abspath(self.charts_dir)
            if os.name == 'nt':  # Windows
                os.startfile(abs_path)
            elif os.name == 'posix':  # macOS/Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    os.system(f'open "{abs_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{abs_path}"')
            self.info_label.setText(f"📂 Carpeta de gráficos abierta.")
        except Exception as e:
            QMessageBox.information(self, "Carpeta de Gráficos", 
                                  f"Carpeta de gráficos: {os.path.abspath(self.charts_dir)}")