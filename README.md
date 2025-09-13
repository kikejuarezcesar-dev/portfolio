# 📈 Sistema de Supervisión de Portafolio de Inversión

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![PyQt](https://img.shields.io/badge/PyQt5-5.15-green)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Una aplicación desktop completa para el análisis y supervisión de portafolios de inversión con interfaz moderna y análisis técnico integrado.

## Características

- Dashboard interactivo con métricas en tiempo real
- Integración con Yahoo Finance API para precios actualizados
- Análisis técnico con gráficos interactivos (Plotly)
- Sistema de alertas inteligentes basado en estadística
- Base de datos SQLite para persistencia local
- Interfaz dark theme optimizada para macOS
- Responsive design adaptable a diferentes resoluciones

## Tecnologías Utilizadas

- Backend: Python 3.8+, SQLite, yfinance API
- Frontend: PyQt5, Plotly, Matplotlib
- Análisis de datos: Pandas, NumPy, SciPy
- Visualización: Plotly, Matplotlib
- Tools: Git, GitHub, PEP8

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/tuusuario/trader-portfolio.git
cd trader-portfolio

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python src/main.py
