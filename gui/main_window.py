import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QLineEdit, QDateEdit, QComboBox, QTabWidget,
                             QMessageBox, QHeaderView, QFormLayout, QGroupBox,
                             QProgressBar)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from api.yahoo_finance import get_current_price, validate_symbol
import sqlite3
import os
import sys
from alerts.alert_manager import alert_manager
from PyQt5.QtCore import QTimer
from gui.forecast_window import ForecastWindow
from config.currency_config import currency_config

# Añadir el directorio padre al path para importar database.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection,insert_activo,insert_transaccion,get_transacciones,close_connection

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("DEBUG: MainWindow inicializando")

        # Aplicar tema oscuro primero
        self.setup_dark_theme()
        self.setWindowIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        # Hacer la ventana más nativa de Mac
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)

        self.setWindowTitle("Sistema de Supervisión de Portafolio de Inversión")
        self.setGeometry(100, 100, 1000, 700)
        
        # Widget central y layout principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Crear pestañas
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Pestaña de transacciones
        self.transactions_tab = QWidget()
        self.tabs.addTab(self.transactions_tab, "Transacciones")
        self.setup_transactions_tab()
        
        # Pestaña de portafolio
        self.portfolio_tab = QWidget()
        self.tabs.addTab(self.portfolio_tab, "Portafolio")
        self.setup_portfolio_tab()

        # Pestaña de Alertas
        self.alerts_tab = QWidget()
        self.tabs.addTab(self.alerts_tab, "Alertas")
        self.setup_alerts_tab()

        # Pestaña de pronostico
        self.forecast_tab = QWidget()
        self.tabs.addTab(self.forecast_tab, "Pronósticos")
        self.setup_forecast_tab()

        # Timer para alertas automáticas
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.check_alerts)
        self.alert_timer.start(300000)  # 5 minutos

        self.alert_label = None

        # Cargar datos iniciales
        print("DEBUG: Cargando datos iniciales...")
        self.load_transactions()
        self.load_portfolio()
        print("DEBUG: Datos iniciales cargados")

        # Verificar alertas iniciales
        QTimer.singleShot(5000, self.check_alerts)  # Verificar después de 5 segundos

        print("DEBUG: Tema oscuro aplicado correctamente")
        print("DEBUG: Stylesheet length:", len(self.styleSheet()))

        self.alert_label = None  # Para el label de alertas

        # Verificar alertas iniciales
        QTimer.singleShot(5000, self.check_alerts)  # Verificar después de 5 segundos
        QTimer.singleShot(6000, self.update_alert_stats)  # Actualizar stats después de 6 segundos
    
    def setup_transactions_tab(self):
        layout = QVBoxLayout(self.transactions_tab)
        
        # Formulario para nueva transacción
        form_group = QGroupBox("Nueva Transacción")
        form_layout = QFormLayout()
        
        self.symbol_input = QLineEdit()
        self.name_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["accion", "cripto", "etf", "cetes","otro_varaible","otro_fija"])
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.price_input = QLineEdit()
        self.quantity_input = QLineEdit()
        self.commission_input = QLineEdit()
        self.commission_input.setText("0")
        
        form_layout.addRow("Símbolo:", self.symbol_input)
        form_layout.addRow("Nombre:", self.name_input)
        form_layout.addRow("Tipo:", self.type_combo)
        form_layout.addRow("Fecha:", self.date_input)
        form_layout.addRow("Precio:", self.price_input)
        form_layout.addRow("Cantidad:", self.quantity_input)
        form_layout.addRow("Comisiones:", self.commission_input)
        
        self.add_btn = QPushButton("Agregar Transacción")
        self.add_btn.clicked.connect(self.add_transaction)
        form_layout.addRow("", self.add_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Tabla de transacciones
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "Símbolo", "Precio", "Cantidad", "Comisiones", "Total"
        ])
        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("Historial de Transacciones:"))
        layout.addWidget(self.transactions_table)
    
    def setup_portfolio_tab(self):

        # Contenedor principal
        portfolio_container = QWidget()
        layout = QVBoxLayout(portfolio_container)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Botón de actualizar precios
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Actualizar Precios")
        self.refresh_btn.clicked.connect(self.load_portfolio)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        
        self.charts_btn = QPushButton("📈 Ver Gráficos")
        self.charts_btn.setStyleSheet("background-color: #ff6d00; color: white;")
        self.charts_btn.clicked.connect(self.show_charts)
        refresh_layout.addWidget(self.charts_btn)
        
        self.last_update_label = QLabel("Última actualización: -")
        refresh_layout.addWidget(self.last_update_label)
        layout.addLayout(refresh_layout)

        # Resumen del portafolio
        summary_group = QGroupBox("Resumen del Portafolio")
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(15)
        
        self.total_invested_label = QLabel("Total Invertido: $0.00")
        self.current_value_label = QLabel("Valor Actual: $0.00")
        self.profit_loss_label = QLabel("Ganancia/Pérdida: $0.00 (0.00%)")
        
        for label in [self.total_invested_label, self.current_value_label, self.profit_loss_label]:
            label.setAlignment(Qt.AlignCenter)
            summary_layout.addWidget(label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Selector de moneda
        currency_layout = QHBoxLayout()
        currency_layout.addWidget(QLabel("Moneda:"))
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["MXN - Pesos Mexicanos", "USD - Dólares Americanos"])
        self.currency_combo.setCurrentText("MXN - Pesos Mexicanos" if currency_config.get_currency() == "MXN" else "USD - Dólares Americanos")
        self.currency_combo.currentTextChanged.connect(self.change_currency)
        currency_layout.addWidget(self.currency_combo)
        
        currency_layout.addStretch()
        layout.addLayout(currency_layout)

        # Estadísticas adicionales
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()
        
        self.total_assets_label = QLabel("Activos: 0")
        self.best_performer_label = QLabel("Mejor: -")
        self.worst_performer_label = QLabel("Peor: -")
        
        for label in [self.total_assets_label, self.best_performer_label, self.worst_performer_label]:
            label.setAlignment(Qt.AlignCenter)
            stats_layout.addWidget(label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Tabla de portafolio
        table_group = QGroupBox("Detalles del Portafolio")
        table_layout = QVBoxLayout()
        
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(8)
        self.portfolio_table.setHorizontalHeaderLabels([
            "Símbolo", "Nombre", "Cantidad", "P. Promedio", 
            "Inversión", "P. Actual", "Valor Actual", "Rendimiento"
        ])
        
        # Configurar header
        header = self.portfolio_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.portfolio_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Configurar la pestaña
        self.portfolio_tab.setLayout(QVBoxLayout())
        self.portfolio_tab.layout().setContentsMargins(0, 0, 0, 0)
        self.portfolio_tab.layout().addWidget(portfolio_container)

        # Botón para verificar alertas manualmente
        self.alert_btn = QPushButton("" \
        "" \
        "Verificar Alertas Ahora")
        self.alert_btn.setStyleSheet("background-color: #ff6d00; color: white;")
        self.alert_btn.clicked.connect(self.check_alerts)
        refresh_layout.addWidget(self.alert_btn)
    
    def change_currency(self, currency_text):
        """Cambiar la moneda de visualización"""
        currency = "MXN" if "MXN" in currency_text else "USD"
        if currency_config.set_currency(currency):
            self.load_portfolio()  # Recargar con la nueva moneda
    
    def setup_alerts_tab(self):
        """Configurar la pestaña de alertas"""
        layout = QVBoxLayout(self.alerts_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel("Sistema de Alertas Automáticas")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("backgrond-color: #ff6d00; color: white")
        layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel(
            "Alertas basadas en análisis estadístico:\n"
            "• Precio por debajo del intervalo de confianza del 90%\n"
            "• Media móvil de 60 días\n"
            "• Alertas automáticas cada 5 minutos"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #bdbdbd; font-size: 12px; padding: 10px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Botones de control
        controls_layout = QHBoxLayout()
        
        self.check_alerts_btn = QPushButton("🔍 Verificar Alertas Ahora")
        self.check_alerts_btn.setStyleSheet("backgrond-color: #ff6d00; color: white")
        self.check_alerts_btn.clicked.connect(self.check_alerts)
        controls_layout.addWidget(self.check_alerts_btn)
        
        self.open_alerts_window_btn = QPushButton("📊 Gestión de Alertas")
        self.open_alerts_window_btn.setStyleSheet("backgrond-color: #ff6d00; color: white")
        self.open_alerts_window_btn.clicked.connect(self.open_alerts_manager)
        controls_layout.addWidget(self.open_alerts_window_btn)
        
        layout.addLayout(controls_layout)
        
        # Área de alertas activas
        alerts_group = QGroupBox("🚨 Alertas Activas")
        alerts_group.setStyleSheet("backgrond-color: #ff6d00; color: white")
        alerts_layout = QVBoxLayout()
        
        self.active_alerts_label = QLabel("No hay alertas activas en este momento")
        self.active_alerts_label.setAlignment(Qt.AlignCenter)
        self.active_alerts_label.setStyleSheet("backgrond-color: #ff6d00; color: white")
        self.active_alerts_label.setWordWrap(True)
        alerts_layout.addWidget(self.active_alerts_label)
        
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)
        
        # Estadísticas
        stats_group = QGroupBox("📈 Estadísticas de Alertas")
        stats_group.setStyleSheet("backgrond-color: #ff6d00; color: white")
        stats_layout = QHBoxLayout()
        
        self.total_alerts_label = QLabel("Alertas totales: 0")
        self.last_alert_label = QLabel("Última alerta: Nunca")
        
        for label in [self.total_alerts_label, self.last_alert_label]:
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #e0e0e0; padding: 10px;")
            stats_layout.addWidget(label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Configuración
        config_group = QGroupBox("⚙️ Configuración de Alertas")
        config_group.setStyleSheet("backgrond-color: #ff6d00; color: white")
        config_layout = QVBoxLayout()
        
        config_info = QLabel(
            "Configuración actual:\n"
            "• Media móvil: 60 días\n"
            "• Intervalo de confianza: 90%\n"
            "• Verificación automática: Cada 5 minutos"
        )
        config_info.setStyleSheet("color: #bdbdbd; padding: 10px;")
        config_info.setWordWrap(True)
        config_layout.addWidget(config_info)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        layout.addStretch()

    def setup_forecast_tab(self):
        """Configurar pestaña de pronósticos"""
        layout = QVBoxLayout(self.forecast_tab)
        
        title_label = QLabel("Pronósticos de Precios - Análisis Predictivo")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 20px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Esta funcionalidad te permite generar pronósticos de precios para cualquier activo.\n"
            "Selecciona un símbolo, el período histórico y el modelo de pronóstico a utilizar.\n\n"
            "Modelos disponibles:\n"
            "• ARIMA: Modelo estadístico para series temporales\n"
            "• Regresión Lineal: Modelo lineal simple\n"
            "• Suavizado Exponencial: Modelo de suavizado de series"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #bdbdbd; padding: 10px;")
        layout.addWidget(desc_label)
        
        self.open_forecast_btn = QPushButton("📊 Abrir Pronósticos Avanzados")
        self.open_forecast_btn.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #9c27b0;
            }
        """)
        self.open_forecast_btn.clicked.connect(self.open_forecast_window)
        layout.addWidget(self.open_forecast_btn)
        
        layout.addStretch()

    def open_forecast_window(self):
        """Abrir ventana de pronósticos"""
        try:
            self.forecast_window = ForecastWindow()
            self.forecast_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al abrir pronósticos: {str(e)}")
    
    def add_transaction(self):
        # Obtener datos del formulario
        symbol = self.symbol_input.text().strip().upper()
        name = self.name_input.text().strip()
        asset_type = self.type_combo.currentText()
        date = self.date_input.date().toString("yyyy-MM-dd")
        
        try:
            price = float(self.price_input.text())
            quantity = float(self.quantity_input.text())
            commission = float(self.commission_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Por favor ingresa valores numéricos válidos para precio, cantidad y comisiones.")
            return
        
        if not symbol or not name:
            QMessageBox.warning(self, "Error", "Por favor ingresa símbolo y nombre.")
            return
        
        if not validate_symbol(symbol):
            reply = QMessageBox.question(self,"Simbolo no validado",
                                         f"El sìnbolo {symbol} no se pudo validar con Yahoo Finance. ¿Deseas continuar aún así?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # Insertar en la base de datos
        try:
            # Primero verificar si el activo ya existe
            from database import get_activos,insert_transaccion,insert_activo
            activos = get_activos()
            existe_activo = any(activo[1] == symbol for activo in activos)
            
            #cursor = self.conn.cursor()
            #cursor.execute("SELECT id FROM activos WHERE simbolo = ?", (symbol,))
            #asset = cursor.fetchone()
            
            if not existe_activo:
                # Insertar nuevo activo
                insert_activo(symbol, name, asset_type)
            
            # Insertar transacción
            success = insert_transaccion(date, symbol, price, quantity, commission)

            if success:
            
                # Limpiar formulario
                self.symbol_input.clear()
                self.name_input.clear()
                self.price_input.clear()
                self.quantity_input.clear()
                self.commission_input.setText("0")
                
                # Actualizar tablas
                self.load_transactions()
                self.load_portfolio()
                
                QMessageBox.information(self, "Éxito", "Transacción agregada correctamente.")
            else:
                QMessageBox.critical(self,"Error","Error al agregar transacción")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al agregar transacción: {str(e)}")
    
    def load_transactions(self):
        try:
            from database import get_transacciones
            transactions = get_transacciones()
            #transactions = get_transacciones(self.conn)
            self.transactions_table.setRowCount(len(transactions))
            
            for row, transaction in enumerate(transactions):
                id, fecha, simbolo, precio, cantidad, comisiones = transaction
                total = precio * cantidad
                
                self.transactions_table.setItem(row, 0, QTableWidgetItem(str(id)))
                self.transactions_table.setItem(row, 1, QTableWidgetItem(fecha))
                self.transactions_table.setItem(row, 2, QTableWidgetItem(simbolo))
                self.transactions_table.setItem(row, 3, QTableWidgetItem(f"{precio:.2f}"))
                self.transactions_table.setItem(row, 4, QTableWidgetItem(f"{cantidad:.4f}"))
                self.transactions_table.setItem(row, 5, QTableWidgetItem(f"{comisiones:.2f}"))
                self.transactions_table.setItem(row, 6, QTableWidgetItem(f"{total:.2f}"))
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Error al cargar transacciones: {str(e)}")
    
    def load_portfolio(self):
        try:

            print("DEBUG: load_portfolio() iniciando")

            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)
            QApplication.processEvents()  # Actualizar UI

            from database import get_portfolio_with_current_prices
            self.progress_bar.setValue(30)

            portfolio_data = get_portfolio_with_current_prices()
            print(f"DEBUG: Datos recibidos: {portfolio_data}")  # Debug
            print(f"DEBUG: Número de assets = {len(portfolio_data)}")
            self.progress_bar.setValue(60)

            self.portfolio_table.setRowCount(len(portfolio_data))
            print(f"DEBUG: Tabla configurada con {len(portfolio_data)} filas")

            total_invested = 0
            current_value = 0

            self.progress_bar.setValue(70)

            currency_symbol = currency_config.get_currency_symbol()
            print(f"DEBUG: Moneda actual: {currency_symbol}")

            best_performer = {"symbol": "-", "return": -1000}
            worst_performer = {"symbol": "-", "return": 1000}

            for row, asset in enumerate(portfolio_data):
                print(f"DEBUG: Procesando fila {row} - {asset['symbol']}")

                total_invested += asset['total_invested']
                current_value += asset['current_value']

                # Calcular rendimiento
                return_pct = ((asset['current_price'] - asset['avg_price']) / asset['avg_price'] * 100) if asset['avg_price'] > 0 else 0
                return_color = "green" if return_pct >= 0 else "red"
                
                # Track best and worst performers
                if return_pct > best_performer["return"]:
                    best_performer = {"symbol": asset['symbol'], "return": return_pct}
                if return_pct < worst_performer["return"]:
                    worst_performer = {"symbol": asset['symbol'], "return": return_pct}
                
                # LLenar la tabla
                self.portfolio_table.setItem(row, 0, QTableWidgetItem(asset['symbol']))
                self.portfolio_table.setItem(row, 1, QTableWidgetItem(asset['name']))
                self.portfolio_table.setItem(row, 2, QTableWidgetItem(f"{asset['quantity']:.2f}"))
                self.portfolio_table.setItem(row, 3, QTableWidgetItem(f"{asset['avg_price']:.2f}"))
                self.portfolio_table.setItem(row, 4, QTableWidgetItem(f"{asset['total_invested']:.2f}"))
                self.portfolio_table.setItem(row, 5, QTableWidgetItem(f"{asset['current_price']:.2f}"))
                self.portfolio_table.setItem(row, 6, QTableWidgetItem(f"{asset['current_value']:.2f}"))

                # Celda de rendimiento con color
                return_item = QTableWidgetItem(f"{return_pct:+.2f}%")
                return_item.setForeground(QColor(return_color))
                self.portfolio_table.setItem(row, 7, return_item)
                
                print(f"DEBUG: fila {row} completada - {asset['symbol']}")

                # Añadir tooltip con precio actual
                tooltip = f"""Símbolo: {asset['symbol']}
                Nombre: {asset['name']}
                Cantidad: {asset['quantity']:.4f}
                Precio promedio: ${asset['avg_price']:.2f}
                Precio actual: ${asset['current_price']:.2f}
                Inversión: ${asset['total_invested']:.2f}
                Valor actual: ${asset['current_value']:.2f}
                Rendimiento: {return_pct:+.2f}%"""
                            
                for col in range(8):
                    item = self.portfolio_table.item(row, col)
                    if item:
                        item.setToolTip(tooltip)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Hacer celdas no editables
            
            self.progress_bar.setValue(80)
            print(f"DEBUG: Total invested = {total_invested}, Current value = {current_value}")

            # Actualizar resumen
            profit_loss = current_value - total_invested
            profit_loss_percent = (profit_loss / total_invested * 100) if total_invested > 0 else 0
            
            #currency_symbol = currency_config.get_currency_symbol()

            self.total_invested_label.setText(f"Total Invertido: {currency_symbol}{total_invested:,.2f}")
            self.current_value_label.setText(f"Valor Actual: {currency_symbol}{current_value:,.2f}")
            
            color = "green" if profit_loss >= 0 else "red"
            self.profit_loss_label.setText(
                f"Ganancia/Pérdida: <font color='{color}'>${profit_loss:.2f} ({profit_loss_percent:.2f}%)</font>"
            )

            # Actualizar estadísticas
            self.total_assets_label.setText(f"Activos: {len(portfolio_data)}")
            print(f"DEBUG: Estadísticas Actualizadas")

            self.best_performer_label.setText(
                f"Mejor: {best_performer['symbol']} ({best_performer['return']:+.1f}%)"
            )
            self.worst_performer_label.setText(
                f"Peor: {worst_performer['symbol']} ({worst_performer['return']:+.1f}%)"
            )
            
            # Actualizar timestamp
            from datetime import datetime
            self.last_update_label.setText(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

            self.progress_bar.setValue(100)
            # Ocultar barra de progreso después de un momento
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))

            print("DEBUG: load_portfolio() completado exitosamente")
            
        except Exception as e:
            print(f"DEBUG: ERROR en load_portfolio: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error al cargar portafolio: {str(e)}")
            self.progress_bar.setVisible(False)

    def show_charts(self):
        """Mostrar ventana de gráficos"""
        from gui.charts_window import ChartsWindow
        from database import get_portfolio_with_current_prices
        
        portfolio_data = get_portfolio_with_current_prices()
        self.charts_window = ChartsWindow(portfolio_data)
        self.charts_window.show()
    
    def closeEvent(self, event):
        # Cerrar conexión a la base de datos al salir
        from database import close_connection
        close_connection()
        event.accept()
    
    def setup_dark_theme(self):
        """Tema oscuro corregido - menos agresivo"""
        dark_stylesheet = """
        /* TEMA OSCURO MÍNIMO Y SEGURO */
        QMainWindow {
            background-color: #1e1e1e;
        }
        
        QTabWidget::pane {
            background-color: #1e1e1e;
            border: 1px solid #404040;
        }
        
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #bdbdbd;
            padding: 10px 20px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #1976d2;
            color: white;
        }
        
        QGroupBox {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #404040;
            border-radius: 8px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            color: #64b5f6;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QTableWidget {
            background-color: #252525;
            alternate-background-color: #2d2d2d;
            gridline-color: #404040;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 6px;
        }
        
        QTableWidget::item {
            padding: 6px;
            border-bottom: 1px solid #404040;
        }
        
        QTableWidget::item:selected {
            background-color: #1976d2;
            color: white;
        }
        
        QHeaderView::section {
            background-color: #1976d2;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        
        QPushButton {
            background-color: #1976d2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #1565c0;
        }
        
        QLabel {
            color: #e0e0e0;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def check_alerts(self):
        """Verificar y mostrar alertas automáticas"""
        try:
            from database import get_all_symbols
            from alerts.alert_manager import alert_manager
            
            symbols = get_all_symbols()
            if not symbols:
                return
            
            alerts = alert_manager.check_portfolio_alerts(symbols)
            
            # Actualizar la pestaña de alertas
            self.update_alerts_tab(alerts)
            
            # Mostrar notificación si hay alertas
            if alerts:
                self.show_alert_notification(alerts)
                
        except Exception as e:
            print(f"Error verificando alertas: {e}")
    
    def update_alerts_tab(self, alerts):
        """Actualizar la pestaña de alertas con la información más reciente"""
        if alerts:
            alert_messages = [alert['alert_message'] for alert in alerts if alert['alert_message']]
            alert_text = "🚨 ALERTAS ACTIVAS:\n\n" + "\n\n".join(alert_messages)
            
            self.active_alerts_label.setText(alert_text)
            self.active_alerts_label.setStyleSheet("""
                color: #d32f2f; 
                font-weight: bold;
                font-size: 14px; 
                padding: 20px;
                background-color: #1e1e1e;
                border-radius: 6px;
                border: 2px solid #d32f2f;
            """)
        else:
            self.active_alerts_label.setText("✅ No hay alertas activas en este momento")
            self.active_alerts_label.setStyleSheet("""
                color: #388e3c; 
                font-size: 14px; 
                padding: 20px;
                background-color: #1e1e1e;
                border-radius: 6px;
            """)
        
        # Actualizar estadísticas
        self.update_alert_stats()
    
    def update_alert_stats(self):
        """Actualizar estadísticas de alertas"""
        try:
            from alerts.alert_manager import alert_manager
            from database import get_all_symbols
            
            symbols = get_all_symbols()
            total_alerts = 0
            last_alert = None
            
            for symbol in symbols:
                stats = alert_manager.get_alert_stats(symbol)
                total_alerts += stats['total_alerts']
                
                if stats['last_alert'] and (not last_alert or stats['last_alert'] > last_alert):
                    last_alert = stats['last_alert']
            
            self.total_alerts_label.setText(f"Alertas totales: {total_alerts}")
            
            if last_alert:
                from datetime import datetime
                last_alert_dt = datetime.fromisoformat(last_alert)
                last_alert_str = last_alert_dt.strftime("%Y-%m-%d %H:%M")
                self.last_alert_label.setText(f"Última alerta: {last_alert_str}")
            else:
                self.last_alert_label.setText("Última alerta: Nunca")
                
        except Exception as e:
            print(f"Error actualizando estadísticas: {e}")

    def show_alert_notification(self, alerts):
        """Mostrar notificación de alertas"""
        alert_messages = [alert['alert_message'] for alert in alerts if alert['alert_message']]
        
        if alert_messages:
            # Crear o actualizar label de alertas
            if not self.alert_label:
                self.alert_label = QLabel()
                self.alert_label.setStyleSheet("""
                    QLabel {
                        background-color: #d32f2f;
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        font-weight: bold;
                        margin: 5px;
                    }
                """)
                self.alert_label.setWordWrap(True)
                self.main_layout.insertWidget(0, self.alert_label)  # Al inicio del layout
            
            message = "🚨 ALERTAS: " + " | ".join(alert_messages)
            self.alert_label.setText(message)
            self.alert_label.show()
            
            # Ocultar después de 30 segundos
            QTimer.singleShot(30000, self.hide_alerts)
            
            # También mostrar messagebox
            QMessageBox.warning(self, "Alertas de Trading", "\n".join(alert_messages))

    def hide_alerts(self):
        """Ocultar label de alertas"""
        if self.alert_label:
            self.alert_label.hide()
    
    def open_alerts_manager(self):
        """Abrir ventana de gestión de alertas"""
        try:
            from database import get_all_symbols
            from gui.alerts_window import AlertsWindow
            
            symbols = get_all_symbols()
            if not symbols:
                QMessageBox.information(self, "Sin datos", "No hay símbolos en el portafolio.")
                return
            
            self.alerts_manager_window = AlertsWindow(symbols)
            self.alerts_manager_window.show()
            
        except ImportError as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el gestor de alertas: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al abrir gestor de alertas: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()