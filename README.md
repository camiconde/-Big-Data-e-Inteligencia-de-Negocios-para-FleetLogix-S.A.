# -Big-Data-e-Inteligencia-de-Negocios-para-FleetLogix-S.A.
Ecosistema de BI y Big Data desarrollado para FleetLogix S.A.. Transforma una base OLTP de 1.6M de registros en PostgreSQL a un Data Warehouse en Snowflake bajo un modelo en estrella, usando un pipeline ETL en Python. Optimiza el control de combustible, rutas y choferes procesando la carga en solo 114 segundos.
# 🚚 Sistema Integral de Inteligencia Logística | FleetLogix S.A.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-00a1e9?logo=snowflake)](https://www.snowflake.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-OLTP-336791?logo=postgresql)](https://www.postgresql.org/)
[![Status](https://img.shields.io/badge/Estado-Producción%20Concluido-brightgreen)](#)

**Autora:** Camila Conde E.  
**Proyecto Integrador II**

---

## 📌 Descripción General del Proyecto

Este proyecto implementa una solución de **Big Data e Inteligencia de Negocios** de extremo a extremo para la compañía logística **FleetLogix S.A.**. El objetivo principal es transformar un entorno relacional transaccional (**OLTP**) saturado en un ecosistema analítico moderno (**OLAP**) en la nube.

Esta arquitectura permite mitigar ineficiencias operativas críticas como:
* Control de gasto e ineficiencias en combustible.
* Desvíos temporales en rutas logísticas.
* Auditoría y seguimiento de desempeño de choferes.
* Toma de decisiones estratégicas basadas en el comportamiento del mercado[cite: 2, 5].

---

## 🏗️ Arquitectura Técnica del Flujo de Datos

La solución está construida sobre una arquitectura híbrida de tres capas diseñada para alto rendimiento:

```text
  [ Origen: OLTP ]            [ Orquestación: ETL ]             [ Destino: OLAP ]
┌──────────────────┐        ┌─────────────────────────┐        ┌──────────────────┐
│    PostgreSQL    │ ────>  │  Python 3.11+ (Pandas)  │ ────>  │    Snowflake     │
│ 1.6M Registros   │        │ Limpieza & Transformación│        │ Modelado Estrella│
└──────────────────┘        └─────────────────────────┘        └──────────────────┘

Origen (OLTP): Base de datos relacional local en PostgreSQL que almacena el flujo transaccional original del negocio (1,600,000 registros).  
PDF

Orquestación y Transformación (ETL): Pipeline en Python encargado de filtros de calidad de datos, ingeniería de variables analíticas, prorrateos económicos y mapeo dimensional.  
PDF

Data Warehouse (OLAP): Repositorio central en Snowflake bajo un modelo en estrella (Star Schema) optimizado para consultas de BI.  
PDF

📂 Estructura del Repositorio
Plaintext
.
├── A3-05_etl_pipeline_estudiantes.py   # Script central con la lógica de extracción e ingesta masiva
├── data/
│   ├── raw/                           # Datos transaccionales crudos (PostgreSQL dumps)
│   └── processed/                     # Salidas procesadas y validadas
├── notebooks/
│   ├── informe_estrategico.ipynb       # Análisis exploratorio y recomendaciones de negocio
│   └── eda_logistica.ipynb            # Auditoría e higiene de datos
├── models/
│   ├── FACT_DELIVERIES.sql            # Tabla de hechos central (1,279,748 transacciones depuradas)
│   └── DIM_*.sql                      # Tablas de dimensiones Tipo SCD 1
├── README.md                          # Documentación principal del proyecto
└── requirements.txt                   # Dependencias del sistema

📊 Modelo de Datos (Star Schema)
El repositorio en Snowflake consolida los datos bajo la siguiente estructura dimensional:  
PDF

FACT_DELIVERIES: Tabla de hechos centralizada con 1,279,748 transacciones de entrega depuradas.  
PDF

DIM_VEHICLE: Dimensiones de flota, capacidad y mantenimiento.  
PDF

DIM_DRIVER: Datos descriptivos y métricas de desempeño del conductor.  
PDF

DIM_ROUTE: Mapeo de rutas, kilometraje y tiempos estimados vs. reales.  
PDF

DIM_CUSTOMER: Segmentación descriptiva del cliente y nivel de servicio[cite: 5].

📈 Resumen de Recomendaciones Estratégicas
El análisis derivado de la capa analítica arrojó los siguientes ejes de optimización estratégica:  
IPYNB

Eje Estratégico	Acción Recomendada	Prioridad	Impacto Esperado
Segmentación de Valor	Enfoque en clientes de alto volumen/estrato con servicios premium	Alta	Incremento en margen por servicio
Fidelización B2B	Programa de membresías y priorización de flota	Media	Mayor tasa de retención de clientes
Rendimiento de Flota	Optimización de rutas y cartas de insumos según rango de edad/uso	Alta	Reducción de costos operativos
Reputación Digital / Servicio	Monitoreo continuo de indicadores de satisfacción en plataformas	Media	Mejora en posicionamiento orgánico
🚀 Requisitos de Instalación y Ejecución
Prerrequisitos
Python 3.11+

[cite: 5]

Instancias activas y credenciales de acceso a PostgreSQL y Snowflake

[cite: 5]

Configuración del Entorno
Clonar el repositorio:

Bash
git clone [https://github.com/tu-usuario/fleetlogix-intelligence.git](https://github.com/tu-usuario/fleetlogix-intelligence.git)
cd fleetlogix-intelligence
Instalar dependencias requeridas[cite: 5]:

Bash
pip install pandas psycopg2-binary snowflake-connector-python
Ejecutar el pipeline ETL[cite: 5]:

Bash
python A3-05_etl_pipeline_estudiantes.py
⚡ Rendimiento del Pipeline: El script procesa el dataset masivo desde PostgreSQL hacia la nube en Snowflake en un tiempo promedio de 114 segundos[cite: 5].
