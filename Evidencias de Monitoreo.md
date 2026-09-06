# 📊 Evidencias de Monitoreo Operacional - FleetLogix

**Trazabilidad de Logs y Adquisición de Métricas en Producción**  
**Autora:** Camila Conde E. | *Entregable Visual de Control*  

---

## 1. Monitoreo del Rendimiento Local del Pipeline (Logs de Python)

El comportamiento del motor de inyección automatizado fue auditado mediante la consola integrada de logs en tiempo real. La ejecución del **Batch ID: `1780525322`** arrojó un canal de inyección masiva libre de advertencias y fallas estructurales:

```text
2026-06-03 19:22:29,968 [INFO] Extraídos 1,600,000 registros de forma exitosa
2026-06-03 19:22:29,968 [INFO] Iniciando transformación de datos...
2026-06-03 19:23:06,381 [INFO] Transformados 1,279,748 registros y mapeados al diccionario estrella
2026-06-03 19:23:19,697 [INFO] Iniciando carga masiva de 1,279,748 hechos en FACT_DELIVERIES...
2026-06-03 19:23:55,445 [INFO] ¡ÉXITO TOTAL! 1,279,748 hechos consolidados en FACT_DELIVERIES (1 bloques)
2026-06-03 19:23:57,077 [INFO] Métricas: {"records_extracted": 1600000, "records_transformed": 1279748, "records_loaded": 1279748, "errors": 0}

2. Verificación e Impacto en la Plataforma Cloud (Snowflake Monitoring)
La telemetría de procesamiento interna de Snowflake validó que la inyección masiva demoró escasos milisegundos en consolidar los datos de negocio tras recibir el paquete optimizado de Python Pandas.  
La distribución final arrojó un equilibrio analítico perfecto de control operativo:  
FALSE (Demoras registradas por desvíos en ruta): $639,864$ filas de hechos[cite: 8].
TRUE (Entregas optimizadas y consolidadas a tiempo): $639,884$ filas de hechos[cite: 8].
Volumen Neto Validado en Nube: $1,279,748$ registros analíticos disponibles para consultas de negocio[cite: 8].
