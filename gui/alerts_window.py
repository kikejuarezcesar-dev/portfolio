from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QComboBox, QGroupBox)
from PyQt5.QtCore import Qt
from alerts.alert_manager import alert_manager
from api.yahoo_finance import get_alert_conditions
from datetime import datetime
from PyQt5.QtGui import QColor

class AlertsWindow(QWidget):
    def __init__(self, portfolio_symbols):
        super().__init__()
        self.portfolio_symbols = portfolio_symbols
        self.setWindowTitle("Gestión de Alertas")
        self.setGeometry(300, 300, 800, 600)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("🔔 Gestión de Alertas de Trading")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #d32f2f; padding: 10px;")
        layout.addWidget(title_label)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(self.portfolio_symbols)
        self.symbol_combo.currentTextChanged.connect(self.update_alert_display)
        
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self.update_alert_display)
        
        self.check_all_btn = QPushButton("🔍 Verificar Todas las Alertas")
        self.check_all_btn.clicked.connect(self.check_all_alerts)
        
        controls_layout.addWidget(QLabel("Símbolo:"))
        controls_layout.addWidget(self.symbol_combo)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.check_all_btn)
        layout.addLayout(controls_layout)
        
        # Información de alertas actuales
        self.current_alert_label = QLabel()
        self.current_alert_label.setAlignment(Qt.AlignCenter)
        self.current_alert_label.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.current_alert_label)
        
        table_group = QGroupBox("Histórico de Alertas")
        table_group.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                margin-top: 1ex;
                padding-top: 12px;
            }
            QGroupBox::title {
                color: #64b5f6;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
            }
        """)
        
        # Layout para el groupbox
        table_layout = QVBoxLayout()
        
        # Tabla de histórico de alertas
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels(["Fecha", "Símbolo", "Tipo", "Precio", "Mensaje"])

        # Configurar header con estilo dark
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Símbolo
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Tipo
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Mensaje (expandible)

        self.alerts_table.setStyleSheet("""
            QTableWidget {
                background-color: #252525;
                alternate-background-color: #2d2d2d;
                gridline-color: #404040;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 6px;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #404040;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #1976d2;
                color: white;
            }
            QHeaderView::section {
                background-color: #1976d2;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget QScrollBar:vertical {
                background-color: #2d2d2d;
            }
            QTableWidget QScrollBar::handle:vertical {
                background-color: #1976d2;
            }
        """)
        
        # Habilitar alternancia de colores
        self.alerts_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.alerts_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        #self.alerts_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        #layout.addWidget(self.alerts_table)
        
        # Actualizar display inicial
        #self.update_alert_display()
        
    def update_alert_display(self):
        symbol = self.symbol_combo.currentText()
        
        # Obtener condiciones actuales
        conditions = get_alert_conditions(symbol)
        
        if conditions:
            alert_text = f"{symbol}: ${conditions['current_price']:.2f} | "
            alert_text += f"MM60: ${conditions['moving_avg']:.2f} | "
            alert_text += f"Límite: ${conditions['lower_band']:.2f}"
            
            if conditions['alert_message']:
                alert_text += f" | 🚨 {conditions['alert_message']}"
                self.current_alert_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            else:
                alert_text += " | ✅ Dentro de rangos normales"
                self.current_alert_label.setStyleSheet("color: #388e3c;")
                
            self.current_alert_label.setText(alert_text)
        
        # Cargar histórico de alertas
        self.load_alert_history(symbol)
    
    def load_alert_history(self, symbol):
        """Cargar histórico de alertas desde la base de datos"""
        try:
            from database import get_alertas
            
            alertas = get_alertas(symbol)
            self.alerts_table.setRowCount(len(alertas))
            
            for row, alerta in enumerate(alertas):
                # alerta[0]=id, [1]=fecha, [2]=simbolo, [3]=tipo_alerta, [4]=precio_actual,
                # [5]=precio_referencia, [6]=desviacion, [7]=mensaje, [8]=leida
                
                fecha = alerta[1].strftime("%Y-%m-%d %H:%M") if hasattr(alerta[1], 'strftime') else str(alerta[1])
                
                # ✅ USAR ESTILOS CONSISTENTES CON EL TEMA OSCURO
                self.alerts_table.setItem(row, 0, QTableWidgetItem(fecha))
                self.alerts_table.setItem(row, 1, QTableWidgetItem(alerta[2]))
                self.alerts_table.setItem(row, 2, QTableWidgetItem(alerta[3]))
                
                # Formatear precio con símbolo de moneda
                from config.currency_config import currency_config
                currency_symbol = currency_config.get_currency_symbol()
                precio_text = f"{currency_symbol}{alerta[4]:.2f}"
                self.alerts_table.setItem(row, 3, QTableWidgetItem(precio_text))
                
                # Mensaje con desviación
                mensaje_completo = f"{alerta[7]} (Desv: {alerta[6]:.1f}%)"
                self.alerts_table.setItem(row, 4, QTableWidgetItem(mensaje_completo))
                
                # ✅ ESTILO PARA ALERTAS NO LEÍDAS (fondo amarillo oscuro)
                if not alerta[8]:
                    for col in range(5):
                        item = self.alerts_table.item(row, col)
                        if item:
                            item.setBackground(QColor('#423c0d'))  # Amarillo oscuro
                            item.setForeground(QColor('#ffeb3b'))  # Texto amarillo
                
                # ✅ ESTILO PARA ALERTAS DE COMPRA (background verde oscuro)
                if "POR DEBAJO" in alerta[7] or "COMPRA" in alerta[7].upper():
                    for col in range(5):
                        item = self.alerts_table.item(row, col)
                        if item:
                            item.setBackground(QColor('#1b4332'))  # Verde oscuro
                            item.setForeground(QColor('#4caf50'))  # Texto verde
                
                # ✅ ESTILO PARA ALERTAS DE SOBRECOMPRA (background rojo oscuro)
                if "POR ENCIMA" in alerta[7] or "SOBRECOMPRA" in alerta[7].upper():
                    for col in range(5):
                        item = self.alerts_table.item(row, col)
                        if item:
                            item.setBackground(QColor('#4a1c1c'))  # Rojo oscuro
                            item.setForeground(QColor('#f44336'))  # Texto rojo
                
        except Exception as e:
            print(f"Error cargando histórico de alertas: {e}")
            # Mensaje de error en la tabla
            self.alerts_table.setRowCount(1)
            error_item = QTableWidgetItem(f"Error cargando alertas: {str(e)}")
            error_item.setForeground(QColor('#f44336'))
            self.alerts_table.setItem(0, 0, error_item)
    
    def check_all_alerts(self):
        alerts = alert_manager.check_portfolio_alerts(self.portfolio_symbols)
        
        if alerts:
            messages = [alert['alert_message'] for alert in alerts]
            QMessageBox.warning(self, "Alertas Encontradas", "\n\n".join(messages))
        else:
            QMessageBox.information(self, "Sin Alertas", "No se encontraron alertas en este momento.")

    def load_alert_history(self, symbol):
        """Cargar histórico de alertas desde la base de datos"""
        try:
            from database import get_alertas
            
            alertas = get_alertas(symbol)
            self.alerts_table.setRowCount(len(alertas))
            
            for row, alerta in enumerate(alertas):
                # alerta[0]=id, [1]=fecha, [2]=simbolo, [3]=tipo_alerta, [4]=precio_actual,
                # [5]=precio_referencia, [6]=desviacion, [7]=mensaje, [8]=leida
                
                fecha = alerta[1].strftime("%Y-%m-%d %H:%M") if hasattr(alerta[1], 'strftime') else str(alerta[1])
                
                self.alerts_table.setItem(row, 0, QTableWidgetItem(fecha))
                self.alerts_table.setItem(row, 1, QTableWidgetItem(alerta[2]))
                self.alerts_table.setItem(row, 2, QTableWidgetItem(alerta[3]))
                self.alerts_table.setItem(row, 3, QTableWidgetItem(f"${alerta[4]:.2f}"))
                
                # Mensaje con desviación
                mensaje_completo = f"{alerta[7]} (Desv: {alerta[6]:.1f}%)"
                self.alerts_table.setItem(row, 4, QTableWidgetItem(mensaje_completo))
                
                # Marcar filas no leídas
                if not alerta[8]:
                    for col in range(5):
                        item = self.alerts_table.item(row, col)
                        if item:
                            item.setBackground(QColor('#fff3cd'))  # Fondo amarillo claro para no leídas
                
        except Exception as e:
            print(f"Error cargando histórico de alertas: {e}")