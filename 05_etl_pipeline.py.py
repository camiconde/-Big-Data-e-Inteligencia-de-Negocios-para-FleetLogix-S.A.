"""
FleetLogix - Pipeline ETL Automático
Extrae de PostgreSQL, Transforma y Carga en Snowflake
Ejecución diaria automatizada
"""

import psycopg2
import snowflake.connector
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import schedule
import time
import json
from typing import Dict, List, Tuple

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_pipeline.log'),
        logging.StreamHandler()
    ]
)

# Configuración de conexiones
POSTGRES_CONFIG = {
    'host': 'localhost',
    'database': 'fleetlogix',
    'user': 'postgres',
    'password': 'Vicen28',
    'port': 5432
}

SNOWFLAKE_CONFIG = {
    'user': 'ECAMILACONDE',
    'password': '8Ek3AEYXk8SqKVp',
    'account': 'MAUCUOE-OC99969',
    'warehouse': 'FLEETLOGIX_WH',
    'database': 'FLEETLOGIX_DW',
    'schema': 'ANALYTICS'
}

class FleetLogixETL:
    def __init__(self):
        self.pg_conn = None
        self.sf_conn = None
        self.batch_id = int(datetime.now().timestamp())
        self.metrics = {
            'records_extracted': 0,
            'records_transformed': 0,
            'records_loaded': 0,
            'errors': 0
        }
    
    def connect_databases(self):
        """Establecer conexiones con PostgreSQL y Snowflake"""
        try:
            # PostgreSQL
            self.pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
            logging.info(" Conectado a PostgreSQL")
            
            # Snowflake
            self.sf_conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
            logging.info(" Conectado a Snowflake")
            
            return True
        except Exception as e:
            logging.error(f" Error en conexión: {e}")
            return False
    
    def extract_daily_data(self) -> pd.DataFrame:
        """Extraer datos de PostgreSQL utilizando las columnas reales analizadas"""
        logging.info(" Iniciando extracción de datos con columnas definitivas...")
        
        query = """
        SELECT 
            d.delivery_id,
            d.package_weight_kg,
            d.delivery_status,
            d.delivery_address,
            t.trip_id as operational_trip_id,
            t.vehicle_id,
            t.driver_id,
            t.route_id,
            t.departure_time,
            t.arrival_time,
            t.status as trip_status
        FROM public.deliveries d
        INNER JOIN public.trips t ON d.trip_id = t.trip_id;
        """
        
        try:
            df = pd.read_sql(query, self.pg_conn)
            # Eliminar columnas duplicadas si las hubiera por el JOIN
            df = df.loc[:, ~df.columns.duplicated()].copy()
            self.metrics['records_extracted'] = len(df)
            logging.info(f" Extraídos {len(df)} registros de forma exitosa")
            return df
        except Exception as e:
            logging.error(f" Error en extracción: {e}")
            self.metrics['errors'] += 1
            return pd.DataFrame()
        
    def transform_data(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Transformar datos mapeando las columnas reales al modelo dimensional"""
        logging.info(" Iniciando transformación de datos...")
        transformed_data = {} 
        
        try:
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                logging.warning(" El DataFrame de entrada está vacío.")
                return {}

            # =====================================================
            # CÁLCULOS ANALÍTICOS (MANTIENEN TUS FÓRMULAS)
            # =====================================================
            # Modificación sugerida para tu función transform_data:
            df['delivery_time_minutes'] = (
                (pd.to_datetime(df['arrival_time']) - 
                 pd.to_datetime(df['departure_time'])).dt.total_seconds() / 60
            ).round(2)

            # Consideramos una tolerancia de retraso más realista para rutas largas
            # (Por ejemplo, si el tiempo de viaje excede los 360 minutos / 6 hours, se considera demorado)
            df['is_on_time'] = df['delivery_time_minutes'] <= 360

            df['delay_minutes'] = df['delivery_time_minutes'].apply(
                lambda x: max(0, x) if x > 0 else 0
            )
            
            df['is_on_time'] = df['delay_minutes'] <= 30
            df['trip_duration_hours'] = (df['delivery_time_minutes'] / 60.0).round(2)
            
            deliveries_per_trip = df.groupby('operational_trip_id').size()
            df['deliveries_in_trip'] = df['operational_trip_id'].map(deliveries_per_trip)
            
            df['deliveries_per_hour'] = (
                df['deliveries_in_trip'] / df['trip_duration_hours']
            ).fillna(0).round(2)
            
            df['fuel_consumed_liters'] = (df['package_weight_kg'] * 0.05 + 10).round(2)
            
            df['cost_per_delivery'] = (
                (df['fuel_consumed_liters'] * 5000 + 1500) / df['deliveries_in_trip']
            ).round(2)
            
            df['revenue_per_delivery'] = (20000 + df['package_weight_kg'] * 500).round(2)
            df['tracking_number'] = 'TRK-' + df['delivery_id'].astype(str)
            
            # Calidad de datos
            df = df[df['delivery_time_minutes'] >= 0]
            df = df[(df['package_weight_kg'] > 0) & (df['package_weight_kg'] < 10000)]
            
            df['date_key'] = pd.to_datetime(df['arrival_time']).dt.strftime('%Y%m%d').fillna('19000101').astype(int)
            df['scheduled_time_key'] = pd.to_datetime(df['departure_time']).dt.strftime('%H%M').fillna('0000').astype(int)

            # =====================================================
            # CONSTRUCCIÓN DE LA TABLA DE HECHOS (CORREGIDA SIN DUPLICADOS)
            # =====================================================
            # Eliminamos la duplicación de delivery_id que causaba el error fatal
            # =====================================================
            # CONSTRUCCIÓN DE LA TABLA DE HECHOS (BLINDADA)
            # =====================================================
            df_fact = df[[
                'date_key', 'scheduled_time_key', 'vehicle_id', 'driver_id', 'route_id',
                'operational_trip_id', 'delivery_id', 'tracking_number', 'delivery_time_minutes',
                'delay_minutes', 'package_weight_kg', 'fuel_consumed_liters', 'revenue_per_delivery',
                'delivery_status'
            ]].copy()
            
            # Forzamos el cálculo de la mediana DIRECTAMENTE acá para evitar desfases
            mediana_tiempo = df_fact['delivery_time_minutes'].median()
            
            # Creamos la columna asegurando valores booleanos puros de Python
            df_fact['is_on_time'] = df_fact['delivery_time_minutes'] <= mediana_tiempo
            
            # Renombrar columnas para el DDL analítico de Snowflake
            df_fact.rename(columns={
                'date_key': 'DATE_KEY',
                'scheduled_time_key': 'SCHEDULED_TIME_KEY',
                'vehicle_id': 'VEHICLE_KEY',
                'driver_id': 'DRIVER_KEY',
                'route_id': 'ROUTE_KEY',
                'delivery_id': 'OPERATIONAL_DELIVERY_ID',
                'operational_trip_id': 'OPERATIONAL_TRIP_ID',
                'tracking_number': 'TRACKING_NUMBER',
                'delivery_time_minutes': 'DELIVERY_TIME_MINUTES',
                'delay_minutes': 'DELAY_MINUTES',
                'package_weight_kg': 'PACKAGE_WEIGHT_KG',
                'fuel_consumed_liters': 'FUEL_CONSUMED_LITERS',
                'revenue_per_delivery': 'REVENUE_PER_DELIVERY',
                'is_on_time': 'IS_ON_TIME',
                'delivery_status': 'DELIVERY_STATUS'
            }, inplace=True)
            
            df_fact['CUSTOMER_KEY'] = 1
            df_fact.reset_index(drop=True, inplace=True)
            
            # Verificación de control en tu consola de Python antes de subir
            conteo_true = (df_fact['IS_ON_TIME'] == True).sum()
            conteo_false = (df_fact['IS_ON_TIME'] == False).sum()
            logging.info(f" [CONTROL LOCAL] Registros calculados -> A tiempo (TRUE): {conteo_true} | Demorados (FALSE): {conteo_false}")
            
            transformed_data['fact_deliveries'] = df_fact
            # =====================================================
            # CONSTRUCCIÓN DE DIMENSIONES EN MAYÚSCULAS
            # =====================================================
            # Dimensión Vehículo
            df_veh = df[['vehicle_id']].drop_duplicates().copy()
            df_veh.rename(columns={'vehicle_id': 'VEHICLE_ID'}, inplace=True)
            df_veh['STATUS'] = 'Activo'
            df_veh.reset_index(drop=True, inplace=True)
            transformed_data['dim_vehicle'] = df_veh
            
            # Dimensión Chofer
            df_drv = df[['driver_id']].drop_duplicates().copy()
            df_drv.rename(columns={'driver_id': 'DRIVER_ID'}, inplace=True)
            df_drv['STATUS'] = 'Activo'
            df_drv.reset_index(drop=True, inplace=True)
            transformed_data['dim_driver'] = df_drv
            
            # Dimensión Ruta
            df_rte = df[['route_id']].drop_duplicates().copy()
            df_rte.rename(columns={'route_id': 'ROUTE_ID'}, inplace=True)
            df_rte.reset_index(drop=True, inplace=True)
            transformed_data['dim_route'] = df_rte
            
            # Dimensión Cliente (Fija)
            df_cust = pd.DataFrame([{
                'CUSTOMER_ID': 1, 
                'CUSTOMER_NAME': 'Consumidor Final', 
                'CUSTOMER_TYPE': 'Individual'
            }])
            transformed_data['dim_customer'] = df_cust
            
            self.metrics['records_transformed'] = len(df_fact)
            logging.info(f" Transformados {len(df_fact)} registros y mapeados al diccionario estrella")
            
            return transformed_data
            
        except Exception as e:
            logging.error(f" Error en transformación: {e}")
            self.metrics['errors'] += 1
            return {}
    
    def load_dimensions(self, transformed_data: dict):
        """Cargar las tablas de dimensiones en Snowflake esquivando el bug de ON_ERROR"""
        logging.info(" Cargando dimensiones en Snowflake...")
        try:
            from snowflake.connector.pandas_tools import write_pandas
            
            for table_name, df_dim in transformed_data.items():
                if table_name.startswith('dim_'):
                    if df_dim is None or df_dim.empty:
                        continue
                        
                    snowflake_table = table_name.upper()
                    logging.info(f" Inyectando {len(df_dim)} registros en la tabla cloud: {snowflake_table}...")
                    
                    # Agregamos on_error='CONTINUE' de forma explícita para corregir el bug de Python 3.14
                    success, nchunks, nrows, _ = write_pandas(
                        conn=self.sf_conn,
                        df=df_dim,
                        table_name=snowflake_table,
                        schema='ANALYTICS',
                        database='FLEETLOGIX_DW',
                        on_error='CONTINUE'
                    )
                    if success:
                        logging.info(f" Éxito: {nrows} filas cargadas en {snowflake_table}")
                        
        except Exception as e:
            logging.error(f" Error cargando dimensiones: {e}")
            self.metrics['errors'] += 1

    def load_facts(self, transformed_data: dict):
        """Cargar la tabla de hechos en Snowflake mapeando TRIP_ID"""
        logging.info(" Cargando tabla de hechos en Snowflake...")
        try:
            from snowflake.connector.pandas_tools import write_pandas
            
            df_fact = transformed_data.get('fact_deliveries')
            
            if df_fact is not None and not df_fact.empty:
                # Ajuste de Contrato: Si Snowflake busca 'TRIP_ID' en lugar de 'OPERATIONAL_TRIP_ID'
                if 'OPERATIONAL_TRIP_ID' in df_fact.columns:
                    df_fact.rename(columns={'OPERATIONAL_TRIP_ID': 'TRIP_ID'}, inplace=True)
                
                # Por si acaso Snowflake busca 'DELIVERY_ID' plano en lugar del operacional
                if 'OPERATIONAL_DELIVERY_ID' in df_fact.columns:
                    df_fact.rename(columns={'OPERATIONAL_DELIVERY_ID': 'DELIVERY_ID'}, inplace=True)

                logging.info(f" Iniciando carga masiva de {len(df_fact)} hechos en FACT_DELIVERIES...")
                
                # Agregamos on_error='CONTINUE' también aquí por seguridad
                success, nchunks, nrows, _ = write_pandas(
                    conn=self.sf_conn,
                    df=df_fact,
                    table_name='FACT_DELIVERIES',
                    schema='ANALYTICS',
                    database='FLEETLOGIX_DW',
                    on_error='CONTINUE'
                )
                if success:
                    logging.info(f" ¡ÉXITO TOTAL! {nrows} hechos consolidados en FACT_DELIVERIES ({nchunks} bloques)")
                    self.metrics['records_loaded'] = nrows
            else:
                logging.warning(" No se encontraron hechos para procesar.")
                
        except Exception as e:
            logging.error(f" Error cargando hechos: {e}")
            self.metrics['errors'] += 1

    def run_etl(self):
        """Ejecutar pipeline ETL completo"""
        start_time = datetime.now()
        logging.info(f" Iniciando ETL - Batch ID: {self.batch_id}")
        
        try:
            # Conectar
            if not self.connect_databases():
                return
            
            # =====================================================
            # CONTROL DEL FLUJO ETL (CORREGIDO PARA MODELO ESTRELLA)
            # =====================================================
            df = self.extract_daily_data()
            if not df.empty:
                # transform_data ahora genera el diccionario estrella
                transformed_dict = self.transform_data(df)
                
                # Validamos que el diccionario no esté vacío
                if transformed_dict:
                    logging.info(" Iniciando la carga en Snowflake...")
                    
                    # Pasamos el diccionario a las funciones de carga nativas
                    self.load_dimensions(transformed_dict)
                    self.load_facts(transformed_dict)

            # Calcular totales para reportes
            self._calculate_daily_totals()
            
            # Cerrar conexiones
            self.close_connections()
            
            # Log final
            duration = (datetime.now() - start_time).total_seconds()
            logging.info(f" ETL completado en {duration:.2f} segundos")
            logging.info(f" Métricas: {json.dumps(self.metrics, indent=2)}")
            
        except Exception as e:
            logging.error(f" Error fatal en ETL: {e}")
            self.metrics['errors'] += 1
            self.close_connections()
    
    def _calculate_daily_totals(self):
        """Pre-calcular totales para reportes rápidos"""
        cursor = self.sf_conn.cursor()
        
        try:
           # Crear tabla histórica de totales de control si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS control_daily_aggregates (
                    batch_id BIGINT PRIMARY KEY,
                    extraction_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    total_deliveries INT,
                    total_revenue DECIMAL(15,2),
                    total_fuel_liters DECIMAL(12,2),
                    delayed_deliveries_count INT
                );
            """)
            # Insertar los totales calculados dinámicamente desde la tabla de hechos en Snowflake
            cursor.execute("""
                INSERT INTO control_daily_aggregates (batch_id, total_deliveries, total_revenue, total_fuel_liters, delayed_deliveries_count)
                SELECT 
                    %s as batch_id,
                    COUNT(delivery_key) as total_deliveries,
                    SUM(revenue_per_delivery) as total_revenue,
                    SUM(fuel_consumed_liters) as total_fuel_liters,
                    SUM(CASE WHEN is_on_time = FALSE THEN 1 ELSE 0 END) as delayed_deliveries_count
                FROM fact_deliveries;
            """, (self.batch_id,))
            self.sf_conn.commit()
            logging.info(" Totales diarios calculados")
            
        except Exception as e:
            logging.error(f" Error calculando totales: {e}")
    
    def close_connections(self):
        """Cerrar conexiones a bases de datos"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.sf_conn:
            self.sf_conn.close()
        logging.info(" Conexiones cerradas")

def job():
    """Función para programar con schedule"""
    etl = FleetLogixETL()
    etl.run_etl()

def main():
    """Función principal - Automatización diaria"""
    logging.info(" Pipeline ETL FleetLogix iniciado")
    
    # Programar ejecución diaria a las 2:00 AM
    schedule.every().day.at("02:00").do(job)
    
    logging.info(" ETL programado para ejecutarse diariamente a las 2:00 AM")
    logging.info("Presiona Ctrl+C para detener")
    
    # Ejecutar una vez al inicio (para pruebas)
    job()
    
    # Loop infinito esperando la hora programada
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verificar cada minuto

if __name__ == "__main__":
    main()