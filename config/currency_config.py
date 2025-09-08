import json
import os

class CurrencyConfig:
    def __init__(self):
        self.config_file = "currency_config.json"
        self.default_currency = "MXN"  # Moneda por defecto: Pesos Mexicanos
        self.available_currencies = ["MXN", "USD"]
        self.load_config()
    
    def load_config(self):
        """Cargar configuración de moneda"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.default_currency = config.get('currency', self.default_currency)
            except:
                self.save_config()
        else:
            self.save_config()
    
    def save_config(self):
        """Guardar configuración de moneda"""
        config = {
            'currency': self.default_currency,
            'available_currencies': self.available_currencies
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_currency(self):
        """Obtener moneda actual"""
        return self.default_currency
    
    def set_currency(self, currency):
        """Establecer moneda"""
        if currency.upper() in self.available_currencies:
            self.default_currency = currency.upper()
            self.save_config()
            return True
        return False
    
    def get_currency_symbol(self):
        """Obtener símbolo de moneda"""
        if self.default_currency == "MXN":
            return "$"
        elif self.default_currency == "USD":
            return "US$"
        return "$"
    
    def get_currency_name(self):
        """Obtener nombre de la moneda"""
        if self.default_currency == "MXN":
            return "Pesos Mexicanos"
        elif self.default_currency == "USD":
            return "Dólares Americanos"
        return "Moneda"

# Instancia global
currency_config = CurrencyConfig()