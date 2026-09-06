# 🛠️ Informe Técnico de Ingeniería de Datos y Optimización SQL

**Proyecto:** Arquitectura y Performance de la Base de Datos Transaccional FleetLogix  
**Rol:** Científico de Datos Junior  
**Estado de Carga:** 505.200 Registros Completados  

---

## 1. Resumen Ejecutivo

El presente documento reporta el despliegue de la infraestructura de datos relacional para **FleetLogix**[cite: 6]. Se implementó una estrategia de inyección masiva de 505,200 registros en PostgreSQL controlando restricciones de integridad y resolviendo cuellos de botella mediante `EXPLAIN ANALYZE` e indexación B-Tree[cite: 6].

---

## 2. Arquitectura y Modelo Relacional

El esquema relacional en PostgreSQL está integrado por 6 tablas interconectadas jerárquicamente[cite: 6]:

* **`vehicles`** *(Maestra)*: Inventario de la flota vehicular, capacidad nominal y tipo de combustible[cite: 6].
* **`drivers`** *(Maestra)*: Registro de personal, códigos internos de empleado y seguimiento de licencias de conducir[cite: 6].
* **`routes`** *(Maestra)*: Topología de la red logística, ciudades conectadas y peajes asociados[cite: 6].
* **`trips`** *(Transaccional Core)*: Registro de viajes vinculando vehículos, conductores y rutas con marcas de tiempo e insumos[cite: 6].
* **`deliveries`** *(Transaccional Secundaria)*: Trazabilidad atómica de paquetes por viaje y control del estado de entrega[cite: 6].
* **`maintenance`** *(Operativa)*: Historial de reparaciones y costos asociados al ciclo de vida del activo[cite: 6].

---

## 3. Decisiones Críticas en la Inyección Masiva

1. **Unicidad Preventiva:** Para evitar colisiones en la patente vehicular (`license_plate`) generadas por `Faker.seed(42)`, se refactorizó la lógica en Python mediante conjuntos en memoria (`set()`), garantizando registros unívocos por lote[cite: 6].
2. **Casting Explicito de Datos (NumPy vs. Psycopg2):** Se convirtió explícitamente el tipo de dato `np.float64` a `float()` nativo de Python para evitar fallas de interpretación en el driver `psycopg2`[cite: 6].
3. **Carga en Lotes (`Bulk Insert`):** Uso de `psycopg2.extras.execute_batch` con bloques de 1,000 registros para mitigar latencia de red y sobrecalentamiento del Write-Ahead Logging (WAL)[cite: 6].

---

## 4. Auditoría y Control de Calidad de Datos (Data Quality)

El motor relacional fue auditado mediante scripts integrados obteniendo un cumplimiento del 100%[cite: 6]:

| Regla de Calidad Auditada | Estado | Resultado |
| :--- | :---: | :--- |
| **Integridad Referencial (`trips` sin vehículo)** | `OK` | Cero registros huérfanos detectados[cite: 6] |
| **Integridad Referencial (`deliveries` sin trip)** | `OK` | Consistencia total de claves foráneas[cite: 6] |
| **Consistencia Temporal (`arrival < departure`)** | `OK` | Lógica cronológica impecable[cite: 6] |
| **Consistencia de Carga (Exceso de peso)** | `OK` | Cumplimiento estricto de límites de carga[cite: 6] |
| **Entregas sin Tracking Number** | `OK` | Cero valores nulos o vacíos en índices únicos[cite: 6] |

---

## 5. Plan de Indexación Estratégico

Para optimizar las consultas críticas de negocio y eliminar escaneos secuenciales masivos (`Seq Scan`)[cite: 6]:

```sql
-- Índice 1: Optimización de filtros cronológicos en viajes
CREATE INDEX idx_trips_departure_perf ON public.trips(departure_datetime);

-- Índice 2: Aceleración de Joins estructurados por Conductor
CREATE INDEX idx_trips_driver_id_perf ON public.trips(driver_id);

-- Índice 3: Indexación de la clave foránea transaccional de Entregas
CREATE INDEX idx_deliveries_trip_id_perf ON public.deliveries(trip_id);

-- Índice 4: Agrupamientos eficientes por activo en mantenimientos
CREATE INDEX idx_maintenance_vehicle_id_perf ON public.maintenance(vehicle_id);

-- Índice 5: Índice parcial condicional exclusivo para entregas exitosas
CREATE INDEX idx_deliveries_completed_perf ON public.deliveries(delivered_datetime)

WHERE delivery_status = 'delivered';
