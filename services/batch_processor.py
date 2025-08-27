import time
import logging
import os
from dotenv import load_dotenv
from typing import Dict, List
from .database_service import DatabaseService
from .gemini_service import GeminiService

load_dotenv()

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self):
        self.db_service = DatabaseService()
        self.gemini_service = GeminiService()
        self.batch_delay = int(os.getenv('BATCH_DELAY_SECONDS', 5))
        
    def procesar_consultas_pendientes(self) -> Dict:
        """Procesa todas las consultas pendientes de resumen"""
        logger.info("Iniciando proceso batch de resúmenes de consultas")
        
        # Estadísticas del proceso
        stats = {
            "inicio": time.strftime("%Y-%m-%d %H:%M:%S"),
            "procesadas_exitosamente": 0,
            "errores": 0,
            "saltadas": 0,
            "total_encontradas": 0,
            "detalles_errores": [],
            "tiempo_total": 0
        }
        
        inicio_tiempo = time.time()
        
        try:
            # Obtener consultas pendientes
            consultas_pendientes = self.db_service.get_consultas_pendientes()
            stats["total_encontradas"] = len(consultas_pendientes)
            
            if not consultas_pendientes:
                logger.info("No hay consultas pendientes de procesar")
                stats["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
                stats["tiempo_total"] = round(time.time() - inicio_tiempo, 2)
                return stats
            
            logger.info(f"Procesando {len(consultas_pendientes)} consultas pendientes")
            
            # Procesar cada consulta
            for i, consulta in enumerate(consultas_pendientes, 1):
                consulta_id = consulta['id']
                consulta_texto = consulta['consulta']
                
                try:
                    logger.info(f"Procesando consulta {i}/{len(consultas_pendientes)} - ID: {consulta_id}")
                    
                    # Validar que hay texto para procesar
                    if not consulta_texto or len(consulta_texto.strip()) < 10:
                        logger.warning(f"Consulta ID {consulta_id} tiene texto muy corto o vacío")
                        stats["saltadas"] += 1
                        continue
                    
                    # Generar resumen con Gemini
                    resumen = self.gemini_service.generar_resumen(consulta_texto, consulta_id)
                    
                    if resumen:
                        # Actualizar en base de datos
                        if self.db_service.actualizar_resumen(consulta_id, resumen):
                            stats["procesadas_exitosamente"] += 1
                            logger.info(f"✅ Consulta {consulta_id} procesada exitosamente")
                        else:
                            error_msg = f"Error actualizando resumen en BD para ID {consulta_id}"
                            logger.error(error_msg)
                            stats["errores"] += 1
                            stats["detalles_errores"].append({
                                "consulta_id": consulta_id,
                                "error": error_msg
                            })
                    else:
                        error_msg = f"Gemini no pudo generar resumen válido para ID {consulta_id}"
                        logger.error(error_msg)
                        
                        # Marcar error en BD
                        self.db_service.marcar_error_procesamiento(consulta_id, "Fallo generación resumen")
                        
                        stats["errores"] += 1
                        stats["detalles_errores"].append({
                            "consulta_id": consulta_id,
                            "error": error_msg
                        })
                
                except Exception as e:
                    error_msg = f"Error procesando consulta ID {consulta_id}: {str(e)}"
                    logger.error(error_msg)
                    
                    # Marcar error en BD
                    try:
                        self.db_service.marcar_error_procesamiento(consulta_id, str(e))
                    except:
                        logger.error(f"No se pudo marcar error en BD para consulta {consulta_id}")
                    
                    stats["errores"] += 1
                    stats["detalles_errores"].append({
                        "consulta_id": consulta_id,
                        "error": error_msg
                    })
                
                # Delay entre procesamiento para no saturar APIs
                if i < len(consultas_pendientes):  # No esperar después de la última
                    time.sleep(self.batch_delay)
            
            stats["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
            stats["tiempo_total"] = round(time.time() - inicio_tiempo, 2)
            
            logger.info(f"""
            📊 PROCESO BATCH COMPLETADO:
            - Total encontradas: {stats['total_encontradas']}
            - Procesadas exitosamente: {stats['procesadas_exitosamente']}
            - Errores: {stats['errores']}
            - Saltadas: {stats['saltadas']}
            - Tiempo total: {stats['tiempo_total']}s
            """)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error crítico en proceso batch: {e}")
            stats["error_critico"] = str(e)
            stats["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
            stats["tiempo_total"] = round(time.time() - inicio_tiempo, 2)
            raise
        
        finally:
            # Cerrar conexión a BD
            try:
                self.db_service.close()
            except:
                pass
    
    def procesar_consulta_individual(self, consulta_id: int) -> Dict:
        """Procesa una consulta específica por ID"""
        logger.info(f"Procesando consulta individual ID: {consulta_id}")
        
        try:
            # Obtener consulta específica
            cursor = self.db_service.connection.cursor(dictionary=True)
            query = """
            SELECT id, registro_id, asesor_nombre, consulta, fecha_consulta 
            FROM expokossodo_consultas 
            WHERE id = %s AND uso_transcripcion = 1
            """
            cursor.execute(query, (consulta_id,))
            consulta = cursor.fetchone()
            cursor.close()
            
            if not consulta:
                return {
                    "error": f"Consulta ID {consulta_id} no encontrada o no habilitada para transcripción"
                }
            
            # Generar resumen
            resumen = self.gemini_service.generar_resumen(consulta['consulta'], consulta_id)
            
            if resumen:
                if self.db_service.actualizar_resumen(consulta_id, resumen):
                    return {
                        "exito": True,
                        "consulta_id": consulta_id,
                        "mensaje": "Resumen generado y actualizado exitosamente"
                    }
                else:
                    return {
                        "error": f"Error actualizando resumen en BD para ID {consulta_id}"
                    }
            else:
                return {
                    "error": f"No se pudo generar resumen para ID {consulta_id}"
                }
                
        except Exception as e:
            logger.error(f"Error procesando consulta individual {consulta_id}: {e}")
            return {
                "error": str(e)
            }
        finally:
            try:
                self.db_service.close()
            except:
                pass