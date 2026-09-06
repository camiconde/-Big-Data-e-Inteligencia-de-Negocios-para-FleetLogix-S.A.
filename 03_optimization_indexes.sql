-- =====================================================
-- FLEETLOGIX - ESTRATEGIA DE INDEXACIÓN Y OPTIMIZACIÓN SQL
-- Módulo 2 / Avance 2 - Camila Conde E.
-- =====================================================

-- Índice 1: Optimiza las búsquedas de entregas vinculadas a un viaje específico
CREATE INDEX idx_maintenance_vehicle_id_perf ON public.maintenance(vehicle_id);

-- Índice 2: Acelera los filtros por estado de entrega entregado
CREATE INDEX idx_deliveries_delivery_status_perf ON public.deliveries(delivery_status);