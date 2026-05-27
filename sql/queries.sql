-- sql/queries.sql
-- Example queries for the HackIAthon fraud detection prototype.
-- The SQLite database can be created with:
--   python -m src.sql.load_csv_to_sqlite --csv data/raw/siniestros.csv data/raw/polizas.csv --db fraudia.db
-- After that you can open the DB with any SQLite client or via the ``sqlite3`` command.

-- 1️⃣  Top 10 siniestros con mayor riesgo (según el puntaje calculado en la tabla ``siniestros``).
SELECT s.id_siniestro,
       s.ramo,
       s.fecha_ocurrencia,
       s.monto_reclamado,
       s.etiqueta_fraude_simulada AS pseudo_score,
       CASE
           WHEN s.etiqueta_fraude_simulada >= 76 THEN '🔴 Rojo'
           WHEN s.etiqueta_fraude_simulada >= 41 THEN '🟡 Amarillo'
           ELSE '🟢 Verde'
       END AS nivel_riesgo
FROM siniestros s
ORDER BY s.etiqueta_fraude_simulada DESC
LIMIT 10;

-- 2️⃣  Proveedores que concentran más alertas rojas.
SELECT p.id_proveedor,
       p.tipo,
       COUNT(*) AS total_alertas,
       SUM(CASE WHEN s.etiqueta_fraude_simulada >= 76 THEN 1 ELSE 0 END) AS alertas_rojas
FROM siniestros s
JOIN proveedores p ON p.id_proveedor = (('PR' || (CAST(substr(s.id_siniestro, 2) AS INTEGER) % 50 + 1)) --  (same logic used in dummy graph)
GROUP BY p.id_proveedor
ORDER BY alertas_rojas DESC
LIMIT 10;

-- 3️⃣  Ramo con mayor porcentaje de casos sospechosos (score >= 41).
SELECT ramo,
       COUNT(*) AS total,
       SUM(CASE WHEN etiqueta_fraude_simulada >= 41 THEN 1 ELSE 0 END) AS sospechosos,
       ROUND(100.0 * sospechosos / total, 2) AS pct_sospechosos
FROM siniestros
GROUP BY ramo
ORDER BY pct_sospechosos DESC;

-- 4️⃣  Siniestros que ocurrieron dentro de los 30 días de la fecha de inicio de la póliza.
SELECT s.id_siniestro,
       s.id_poliza,
       s.fecha_ocurrencia,
       p.fecha_inicio,
       julianday(s.fecha_ocurrencia) - julianday(p.fecha_inicio) AS dias_desde_inicio
FROM siniestros s
JOIN polizas p ON p.id_poliza = s.id_poliza
WHERE julianday(s.fecha_ocurrencia) - julianday(p.fecha_inicio) BETWEEN 0 AND 30;

-- 5️⃣  Reclamaciones con documentos incompletos o ilegibles.
SELECT s.id_siniestro,
       s.documentos_completos,
       d.legible,
       d.entregado,
       d.inconsistencia_detectada
FROM siniestros s
JOIN documentos d ON d.id_siniestro = s.id_siniestro
WHERE s.documentos_completos = 'No'
   OR d.legible = 'No'
   OR d.inconsistencia_detectada = 'Sí';

-- 6️⃣  Casos donde la diferencia entre monto reclamado y suma asegurada supera el 95 %.
SELECT s.id_siniestro,
       s.monto_reclamado,
       p.suma_asegurada,
       ROUND(100.0 * s.monto_reclamado / p.suma_asegurada, 2) AS pct_suma
FROM siniestros s
JOIN polizas p ON p.id_poliza = s.id_poliza
WHERE (s.monto_reclamado * 1.0) / p.suma_asegurada >= 0.95;
