# ☁️ Informe de Diseño: Arquitectura Cloud y Telemetría en Tiempo Real

**Proyecto:** Análisis Conceptual y Evaluación Serverless — Ecosistema FleetLogix  
**Autora:** Camila Conde E. | *Científico de Datos Junior*[cite: 9]  

---

## 1. Introducción y Cambio de Paradigma Logístico

El presente documento analiza la migración de los componentes locales de **FleetLogix** hacia **Amazon Web Services (AWS)**[cite: 9]. Esta transición representa un cambio desde un modelo relacional síncrono por lotes hacia una **Arquitectura Serverless y Orientada a Eventos**[cite: 9].

Bajo este esquema, la telemetría vehicular (ubicación GPS, estado de entregas y marcas temporales) se captura y evalúa al instante[cite: 9]. Esto elimina la necesidad de mantener infraestructura encendida $24/7$, reduciendo costos directos y habilitando escalabilidad elástica automatizada[cite: 9].

---

## 2. Recursos de AWS e Infraestructura Provista

### A. Persistencia Políglota y Almacenamiento
* **AWS RDS PostgreSQL (`fleetlogix-db`):** Instancia administrada (`db.t3.micro`, PostgreSQL 15.4)[cite: 9]. Aloja el modelo operativo histórico transaccional garantizando propiedades ACID[cite: 9].
* **Amazon S3 Bucket (`fleetlogix-data`):** Repositorio de objetos que opera como *Data Lake Central*[cite: 9]. Almacena respaldos fríos en CSV y volcados de logs en JSON[cite: 9].
* **Amazon DynamoDB (NoSQL):** Cuatro tablas con claves hash para telemetría en tiempo real:
  * `deliveries_status` *(PK: `delivery_id`)*: Estado instantáneo del paquete[cite: 9].
  * `vehicle_tracking` *(PK: `vehicle_id`)*: Última coordenada GPS reportada[cite: 9].
  * `routes_waypoints` *(PK: `route_id`)*: Geometrías de control de rutas[cite: 9].
  * `alerts_history` *(PK: `alert_id`)*: Bitácora de incidentes y desvíos[cite: 9].

### B. Componentes de Cómputo Analítico Serverless
* **AWS Lambda 1 (`lambda_verificar_entrega`):** Microservicio síncrono (API Gateway) para validar el estado de entrega en la app móvil[cite: 9].
* **AWS Lambda 2 (`lambda_calcular_eta`):** Proceso periódico automatizado vía AWS EventBridge (cada 5 min) para estimar tiempos de arribo[cite: 9].
* **AWS Lambda 3 (`lambda_alerta_desvio`):** Función orientada a eventos en tiempo real. Compara coordenadas contra waypoints y dispara alertas mediante Amazon SNS[cite: 9].
* **Rol de Ejecución IAM (`FleetLogixLambdaRole`):** Otorga permisos para escribir en DynamoDB y publicar mensajes en SNS[cite: 9].

---

## 3. Auditoría de Código: Función `lambda_verificar_entrega`

1. **Extracción y Validación de Payload:** Lee el evento desde API Gateway[cite: 9]. Si falta el `delivery_id`, ejecuta una cláusula de guarda retornando `HTTP 400 Bad Request`[cite: 9].
2. **Búsqueda Indexada Clave-Valor:** Ejecuta `get_item` en DynamoDB sobre la tabla `deliveries_status`[cite: 9]. La consulta se resuelve en milisegundos de un solo dígito sin requerir *JOINs*[cite: 9].
3. **Evaluación de Estados de Negocio:**
   * **Registro Inexistente:** Si no existe el registro, responde con `HTTP 200`, asignando `status = 'not_found'` e `is_completed = False`[cite: 9].
   * **Registro Encontrado:** Evalúa la condición lógica:
     $$is\_completed = (item.get('status') == 'delivered')$$[cite: 9]
4. **Serialización:** Retorna un código `HTTP 200` encapsulando la respuesta en formato JSON[cite: 9].

---

## 4. Auditoría de Código: Función `migrar_datos_postgresql()`

La función `migrar_datos_postgresql()` automatiza la migración inicial desde el entorno local hacia AWS RDS[cite: 9]:

* **Conectividad Múltiple:** Abre conexiones simultáneas a PostgreSQL local y a la instancia remota de AWS RDS mediante `psycopg2`[cite: 9].
* **Secuenciación Jerárquica:** Para respetar las claves foráneas (*Foreign Keys*), itera las tablas en orden estrictamente secuencial:  
  `['vehicles', 'drivers', 'routes', 'trips', 'deliveries', 'maintenance']`[cite: 9].
* **Procesamiento en Lote y Atomicidad:** Extrae con `fetchall()`, construye consultas `INSERT INTO` parametrizadas y ejecuta `connection_rds.commit()` por tabla[cite: 9]. Si la red falla, se revierten los cambios garantizando la integridad[cite: 9].
* **Cierre de Buffers:** Cierra conexiones y cursores al finalizar para evitar fugas de memoria[cite: 9].

---

## 5. Resumen de Persistencia Híbrida

| Servicio de Almacenamiento | Paradigma de Datos | Rol Crítico en FleetLogix | Ventaja Principal Evaluada |
| :--- | :---: | :--- | :--- |
| **AWS RDS PostgreSQL** | Relacional (SQL)[cite: 9] | Datos operacionales estables[cite: 9] | Consistencia estricta (ACID) e integridad[cite: 9] |
| **Amazon DynamoDB** | NoSQL (Clave-Valor)[cite: 9] | Telemetría y consultas móviles[cite: 9] | Baja latencia ($<10\text{ ms}$) y alta concurrencia[cite: 9] |
| **Amazon S3** | Orientado a Objetos[cite: 9] | *Data Lake* e histórico frío[cite: 9] | Escala ilimitada y costo muy bajo[cite: 9] |
