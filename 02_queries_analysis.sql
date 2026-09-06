-- Tanda 1: Análisis Operativo Base (Estructura Oficial)
--Query 1: Composición de la Flota
--Problema de negocio: Conocer la composición de la flota para entender la distribución de activos por tipo de vehículo y evaluar si la capacidad instalada se alinea con la estrategia logística.


EXPLAIN ANALYZE
SELECT vehicle_type, COUNT(*) as total_vehiculos
FROM public.vehicles
GROUP BY vehicle_type
ORDER BY total_vehiculos DESC;

-- Nota para tu informe: Verás que hace un Seq Scan. Al tener solo 200 filas, es el camino óptimo para el motor (tarda menos de 1 ms).

--Query 2: Licencias próximas a vencer
--Problema de negocio: Prevenir problemas legales y multas operativas identificando proactivamente a los conductores cuyas licencias vencerán en los próximos 60 días.

EXPLAIN ANALYZE
SELECT driver_id, employee_code, first_name, last_name, license_number, license_expiry
FROM public.drivers
WHERE license_expiry <= CURRENT_DATE + INTERVAL '60 days'
ORDER BY license_expiry ASC;
--Nota para tu informe: Analiza cuántos conductores te devuelve. Al igual que la anterior, al ser una tabla maestra pequeña (400 filas), el escaneo secuencial es inmediato.

--Query 3: Total de viajes por estado del viaje
--Problema de negocio: Monitorear operaciones en curso y analizar el volumen histórico para evaluar cuántos viajes logísticos se completaron con éxito frente a los que siguen activos (in_progress).

EXPLAIN ANALYZE
SELECT status, COUNT(*) as cantidad_viajes
FROM public.trips
GROUP BY status
ORDER BY cantidad_viajes DESC;
--Nota para tu informe: Acá ya interactúas con 100.000 filas. Anota detalladamente el "Execution Time" (tiempo de ejecución) que te devuelve abajo en los logs de DBeaver.

--Query 4: Total de entregas por ciudad destino en los últimos 2 meses
--Problema de negocio: Identificar la demanda reciente por ciudad para la planificación eficiente de recursos, distribución de personal y asignación estratégica de vehículos.

EXPLAIN ANALYZE
SELECT r.destination_city, COUNT(d.delivery_id) as total_entregas
FROM public.deliveries d
JOIN public.trips t ON d.trip_id = t.trip_id
JOIN public.routes r ON t.route_id = r.route_id
WHERE t.departure_datetime >= CURRENT_DATE - INTERVAL '2 months'
GROUP BY r.destination_city
ORDER BY total_entregas DESC;
--Nota para tu informe: Esta query es un excelente escenario de estrés. Cruza la tabla de entregas (400.000 filas) con viajes (100.000) y filtra por rango de tiempo. El tiempo de respuesta base suele ser notable.


CREATE INDEX idx_trips_departure_perf ON public.trips(departure_datetime);

--Query 5: Conductores activos con cantidad de viajes completados
--Problema de negocio: Evaluar la carga de trabajo por conductor. Permite identificar si la distribución de viajes es equitativa entre el personal activo o si hay concentración de tareas en pocos empleados.

EXPLAIN ANALYZE
SELECT d.driver_id, d.employee_code, d.first_name, d.last_name, COUNT(t.trip_id) as total_viajes_completados
FROM public.drivers d
LEFT JOIN public.trips t ON d.driver_id = t.driver_id AND t.status = 'completed'
WHERE d.status = 'active'
GROUP BY d.driver_id, d.employee_code, d.first_name, d.last_name
ORDER BY total_viajes_completados DESC;

--Query 6: Promedio de entregas por conductor en los últimos 6 meses
--Problema de negocio: Medir la productividad individual de los conductores en el corto plazo, evaluando la densidad de entregas por viaje para optimizar las asignaciones.

EXPLAIN ANALYZE
SELECT d.driver_id, d.employee_code, d.first_name, d.last_name, 
       ROUND(COUNT(del.delivery_id)::NUMERIC / NULLIF(COUNT(DISTINCT t.trip_id), 0), 2) as promedio_entregas_por_viaje
FROM public.drivers d
JOIN public.trips t ON d.driver_id = t.driver_id
JOIN public.deliveries del ON t.trip_id = del.trip_id
WHERE t.departure_datetime >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY d.driver_id, d.employee_code, d.first_name, d.last_name
ORDER BY promedio_entregas_por_viaje DESC;

--Query 7: Rutas con mayor consumo de combustible por kilómetro
--Problema de negocio: Identificar rutas ineficientes para optimización. Cruzar los kilómetros con el combustible consumido ayuda a detectar trayectos con problemas de tráfico, desvíos o terrenos difíciles.

EXPLAIN ANALYZE
SELECT r.route_code, r.origin_city, r.destination_city,
       ROUND(SUM(t.fuel_consumed_liters) / SUM(r.distance_km), 4) as consumo_litros_por_km,
       COUNT(t.trip_id) as total_viajes
FROM public.routes r
JOIN public.trips t ON r.route_id = t.route_id
GROUP BY r.route_id, r.route_code, r.origin_city, r.destination_city
ORDER BY consumo_litros_por_km DESC;

--Query 8: Análisis de entregas retrasadas por día de la semana
--Problema de negocio: Identificar patrones de retraso para mejorar la planificación. Si ciertos días presentan sistemáticamente problemas de cumplimiento, se pueden ajustar las ventanas horarias de compromiso con el cliente.

EXPLAIN ANALYZE
SELECT EXTRACT(ISODOW FROM t.departure_datetime) as numero_dia,
       TO_CHAR(t.departure_datetime, 'Day') as dia_semana,
       COUNT(del.delivery_id) as entregas_no_exitosas
FROM public.deliveries del
JOIN public.trips t ON del.trip_id = t.trip_id
WHERE del.delivery_status <> 'delivered'
GROUP BY EXTRACT(ISODOW FROM t.departure_datetime), TO_CHAR(t.departure_datetime, 'Day')
ORDER BY numero_dia ASC;

--Para acelerar la velocidad a la que PostgreSQL une las tablas masivas, vamos a crear dos índices estratégicos sobre las Claves Foráneas (Foreign Keys). Ejecutá estos comandos en DBeaver:

-- Índice 2: Acelera la búsqueda de viajes asociados a un conductor (Optimiza Query 5 y 6)
CREATE INDEX idx_trips_driver_id_perf ON public.trips(driver_id);
-- Índice 3: Acelera la vinculación masiva de entregas a sus respectivos viajes (Optimiza Query 6 y 8)
CREATE INDEX idx_deliveries_trip_id_perf ON public.deliveries(trip_id);

--Query 9: Costo de mantenimiento por kilómetro recorrido
--Problema de negocio: Evaluar el costo-beneficio de cada tipo de vehículo. Permite cruzar los gastos del historial de mantenimiento contra la distancia total recorrida en los viajes para saber qué modelos o marcas de camiones son más rentables y cuáles generan pérdidas por roturas constantes.

EXPLAIN ANALYZE
SELECT v.vehicle_id, v.vehicle_type,
       ROUND(COALESCE(SUM(m.cost), 0), 2) as costo_total_mantenimiento,
       ROUND(COALESCE(SUM(DISTINCT t.total_weight_kg), 0), 2) as carga_total_transportada, -- Medida proxy de desgaste comercial
       ROUND(COALESCE(SUM(m.cost), 0) / NULLIF(SUM(DISTINCT r.distance_km), 0), 2) as costo_mantenimiento_por_km
FROM public.vehicles v
LEFT JOIN public.maintenance m ON v.vehicle_id = m.vehicle_id
LEFT JOIN public.trips t ON v.vehicle_id = t.vehicle_id
LEFT JOIN public.routes r ON t.route_id = r.route_id
GROUP BY v.vehicle_id, v.vehicle_type
ORDER BY costo_mantenimiento_por_km DESC;

--Query 10: Ranking de conductores por eficiencia usando Window Functions
--Problema de negocio: Identificar a los top performers (mejores empleados) para el otorgamiento de incentivos y bonificaciones, evaluando quiénes consumen menos combustible en relación a los kilómetros conducidos.

EXPLAIN ANALYZE
SELECT d.driver_id, d.first_name, d.last_name,
       COUNT(t.trip_id) as viajes_totales,
       ROUND(SUM(t.fuel_consumed_liters), 2) as combustible_total_litros,
       RANK() OVER (
           ORDER BY (SUM(t.fuel_consumed_liters) / NULLIF(SUM(t.fuel_consumed_liters), 0)) ASC
       ) as ranking_eficiencia
FROM public.drivers d
JOIN public.trips t ON d.driver_id = t.driver_id
WHERE t.status = 'completed'
GROUP BY d.driver_id, d.first_name, d.last_name;

--Query 11: Análisis de tendencia de viajes con LAG y LEAD
--Problema de negocio: Proyectar necesidades futuras basadas en tendencias históricas. Al usar funciones analíticas como LAG o LEAD, el negocio puede comparar la cantidad de viajes de una semana contra la semana anterior para identificar si la demanda logística está creciendo o contrayéndose.

EXPLAIN ANALYZE
SELECT EXTRACT(YEAR FROM departure_datetime) as anio,
       EXTRACT(WEEK FROM departure_datetime) as semana,
       COUNT(trip_id) as viajes_esta_semana,
       LAG(COUNT(trip_id), 1) OVER (
           ORDER BY EXTRACT(YEAR FROM departure_datetime), EXTRACT(WEEK FROM departure_datetime)
       ) as viajes_semana_anterior,
       COUNT(trip_id) - LAG(COUNT(trip_id), 1) OVER (
           ORDER BY EXTRACT(YEAR FROM departure_datetime), EXTRACT(WEEK FROM departure_datetime)
       ) as variacion_viajes
FROM public.trips
GROUP BY EXTRACT(YEAR FROM departure_datetime), EXTRACT(WEEK FROM departure_datetime)
ORDER BY anio ASC, semana ASC;

--Query 12: Pivot de entregas por hora y día de la semana
--Problema de negocio: Optimizar los horarios de operación y la asignación de personal. Permite visualizar qué horas del día de la semana concentran los mayores picos de entrega efectiva para prever la contratación de personal en las bodegas o guardias de despacho.

EXPLAIN ANALYZE
SELECT EXTRACT(HOUR FROM delivered_datetime) as hora_entrega,
       COUNT(CASE WHEN EXTRACT(ISODOW FROM delivered_datetime) = 1 THEN 1 END) as Lunes,
       COUNT(CASE WHEN EXTRACT(ISODOW FROM delivered_datetime) = 2 THEN 1 END) as Martes,
       COUNT(CASE WHEN EXTRACT(ISODOW FROM delivered_datetime) = 3 THEN 1 END) as Miercoles,
       COUNT(CASE WHEN EXTRACT(ISODOW FROM delivered_datetime) = 4 THEN 1 END) as Jueves,
       COUNT(CASE WHEN EXTRACT(ISODOW FROM delivered_datetime) = 5 THEN 1 END) as Viernes,
       COUNT(CASE WHEN EXTRACT(ISODOW FROM delivered_datetime) = 6 THEN 1 END) as Sabado,
       COUNT(CASE WHEN EXTRACT(ISODOW FROM delivered_datetime) = 7 THEN 1 END) as Domingo
FROM public.deliveries
WHERE delivery_status = 'delivered' AND delivered_datetime IS NOT NULL
GROUP BY EXTRACT(HOUR FROM delivered_datetime)
ORDER BY hora_entrega ASC;

-- Índice 4: Optimiza los agrupamientos por vehículo en la tabla de mantenimientos (Acelera Query 9)
CREATE INDEX idx_maintenance_vehicle_id_perf ON public.maintenance(vehicle_id);

-- Índice 5: Índice condicional parcial enfocado solo en entregas exitosas (Acelera la Query 12 y reportes diarios)
CREATE INDEX idx_deliveries_completed_perf ON public.deliveries(delivered_datetime) WHERE delivery_status = 'delivered';