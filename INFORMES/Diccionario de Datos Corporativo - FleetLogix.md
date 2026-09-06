# 📘 Diccionario de Datos Corporativo - FleetLogix

**Entregable Técnico de Gobierno de Datos**  
**Autora:** Camila Conde E.[cite: 7]  

---

## 1. Especificación Técnica: `FACT_DELIVERIES`

Este componente actúa como la **tabla analítica central de hechos** en el Data Warehouse[cite: 7]. Almacena las claves foráneas de conexión dimensional y las métricas e indicadores clave de rendimiento (KPIs) logísticos transformados[cite: 7].

| Nombre del Campo Cloud | Tipo de Dato | Clave | Columna Origen | Regla de Negocio / Descripción Analítica |
| :--- | :---: | :---: | :--- | :--- |
| **`OPERATIONAL_DELIVERY_ID`** | `INTEGER` | **PK** | `deliveries.delivery_id` | Clave primaria física que identifica de forma unívoca cada paquete de la operación[cite: 7]. |
| **`DATE_KEY`** | `INTEGER` | **FK** | `trips.arrival_time` | Clave temporal calculada en formato `AAAAMMDD` para enlazar la dimensión tiempo[cite: 7]. |
| **`VEHICLE_KEY`** | `INTEGER` | **FK** | `trips.vehicle_id` | Enlace relacional directo a la dimensión de camiones y unidades de la flota[cite: 7]. |
| **`DRIVER_KEY`** | `INTEGER` | **FK** | `trips.driver_id` | Vínculo relacional analítico hacia el catálogo descriptivo corporativo de choferes[cite: 7]. |
| **`ROUTE_KEY`** | `INTEGER` | **FK** | `trips.route_id` | Clave de asociación a la dimensión descriptiva de rutas y trayectos interprovinciales[cite: 7]. |
| **`DELIVERY_TIME_MINUTES`** | `FLOAT` | - | *Calculado* | Métrica de duración total del trayecto calculada en minutos (`Arrival - Departure`)[cite: 7]. |
| **`DELAY_MINUTES`** | `FLOAT` | - | *Calculado* | Minutos excedidos registrados en base al umbral operativo de la ruta[cite: 7]. |
| **`FUEL_CONSUMED_LITERS`** | `FLOAT` | - | *Calculado* | Estimación polinómica del consumo de combustible (`Peso * 0.05 + 10`)[cite: 7]. |
| **`IS_ON_TIME`** | `BOOLEAN` | - | *Calculado* | Indicador booleano de cumplimiento logístico equilibrado mediante la mediana de performance[cite: 7]. |
