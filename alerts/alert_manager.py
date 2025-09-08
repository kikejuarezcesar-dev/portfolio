import json
import os
from datetime import datetime, timedelta
import time
from api.yahoo_finance import get_alert_conditions, get_multiple_prices
from database import insert_alerta, get_alertas, marcar_alerta_leida, get_estadisticas_alertas
from datetime import datetime

class AlertManager:
    def __init__(self):
        self.alerts_dir = "alerts"
        self.alert_cooldown = 3600  # 1 hora en segundos entre alertas del mismo tipo
        os.makedirs(self.alerts_dir, exist_ok=True)
    
    def _get_alert_file_path(self, symbol, alert_type):
        return os.path.join(self.alerts_dir, f"{symbol}_{alert_type}.json")
    
    def _can_send_alert(self, symbol, alert_type):
        """Verificar si ha pasado suficiente tiempo desde la última alerta"""
        try:
            # Buscar la última alerta del mismo tipo para este símbolo
            alertas = get_alertas(symbol)
            ultima_alerta = None
            
            for alerta in alertas:
                if alerta[3] == alert_type:  # tipo_alerta está en la posición 3
                    ultima_alerta = alerta[1]  # fecha está en la posición 1
                    break
            
            if not ultima_alerta:
                return True
            
            # Convertir string de fecha a datetime
            if isinstance(ultima_alerta, str):
                ultima_alerta_dt = datetime.fromisoformat(ultima_alerta.replace('Z', '+00:00'))
            else:
                ultima_alerta_dt = ultima_alerta
                
            return (datetime.now() - ultima_alerta_dt).total_seconds() > self.alert_cooldown
            
        except Exception as e:
            print(f"Error verificando cooldown de alerta: {e}")
            return True
    
    def _record_alert_sent(self, symbol, alert_type, alert_data):
        """Registrar alerta en la base de datos"""
        try:
            desviacion = ((alert_data['lower_band'] - alert_data['current_price']) / 
                         alert_data['lower_band']) * 100 if alert_data['current_price'] < alert_data['lower_band'] else 0
            
            alert_id = insert_alerta(
                simbolo=symbol,
                tipo_alerta=alert_type,
                precio_actual=alert_data['current_price'],
                precio_referencia=alert_data['lower_band'],
                desviacion=desviacion,
                mensaje=alert_data['alert_message']
            )
            
            return alert_id is not None
            
        except Exception as e:
            print(f"Error registrando alerta en BD: {e}")
            return False
    
    def check_portfolio_alerts(self, portfolio_symbols):
        """Verificar alertas para todos los símbolos del portafolio"""
        alerts = []
        
        for symbol in portfolio_symbols:
            alert_conditions = get_alert_conditions(symbol)
            
            if alert_conditions and alert_conditions['alert_message']:
                # Verificar cooldown
                if self._can_send_alert(symbol, alert_conditions['alert_type']):
                    alerts.append(alert_conditions)
                    self._record_alert_sent(symbol, alert_conditions['alert_type'], alert_conditions)
                    print(f"ALERTA: {alert_conditions['alert_message']}")
        
        return alerts
    
    def get_alert_stats(self, symbol):
        """Obtener estadísticas de alertas para un símbolo"""
        stats = {
            'total_alerts': 0,
            'last_alert': None,
            'alert_history': []
        }
        
        for alert_type in ['buy_opportunity', 'overbought']:
            alert_file = self._get_alert_file_path(symbol, alert_type)
            
            if os.path.exists(alert_file):
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                        stats['total_alerts'] += 1
                        stats['alert_history'].append(alert_data)
                        
                        if not stats['last_alert'] or alert_data['timestamp'] > stats['last_alert']:
                            stats['last_alert'] = alert_data['timestamp']
                except:
                    continue
        
        return stats
    
    def get_alert_stats(self, symbol=None):
        """Obtener estadísticas de alertas desde la base de datos"""
        try:
            if symbol:
                alertas = get_alertas(symbol)
            else:
                alertas = get_alertas()
            
            stats = {
                'total_alerts': len(alertas),
                'unread_alerts': len([a for a in alertas if not a[8]]),  # leida está en posición 8
                'last_alert': max([a[1] for a in alertas]) if alertas else None,  # fecha en posición 1
                'alert_history': []
            }
            
            for alerta in alertas:
                stats['alert_history'].append({
                    'id': alerta[0],
                    'fecha': alerta[1],
                    'simbolo': alerta[2],
                    'tipo_alerta': alerta[3],
                    'precio_actual': alerta[4],
                    'precio_referencia': alerta[5],
                    'desviacion': alerta[6],
                    'mensaje': alerta[7],
                    'leida': bool(alerta[8])
                })
            
            return stats
            
        except Exception as e:
            print(f"Error obteniendo estadísticas de alertas: {e}")
            return {'total_alerts': 0, 'unread_alerts': 0, 'last_alert': None, 'alert_history': []}

# Instancia global
alert_manager = AlertManager()