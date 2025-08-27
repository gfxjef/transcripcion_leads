import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT', 3306)),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            if self.connection.is_connected():
                logger.info("Conexión exitosa a MySQL")
        except Error as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise
    
    def get_consultas_pendientes(self) -> List[Dict]:
        cursor = self.connection.cursor(dictionary=True)
        try:
            query = """
            SELECT id, registro_id, asesor_nombre, consulta, fecha_consulta 
            FROM expokossodo_consultas 
            WHERE uso_transcripcion = 1 
            AND (resumen IS NULL OR resumen = '')
            ORDER BY fecha_consulta ASC
            """
            cursor.execute(query)
            consultas = cursor.fetchall()
            logger.info(f"Encontradas {len(consultas)} consultas pendientes de procesar")
            return consultas
        except Error as e:
            logger.error(f"Error obteniendo consultas pendientes: {e}")
            raise
        finally:
            cursor.close()
    
    def actualizar_resumen(self, consulta_id: int, resumen: str) -> bool:
        cursor = self.connection.cursor()
        try:
            query = """
            UPDATE expokossodo_consultas 
            SET resumen = %s 
            WHERE id = %s
            """
            cursor.execute(query, (resumen, consulta_id))
            self.connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Resumen actualizado para consulta ID: {consulta_id}")
                return True
            else:
                logger.warning(f"No se encontró consulta con ID: {consulta_id}")
                return False
                
        except Error as e:
            logger.error(f"Error actualizando resumen para ID {consulta_id}: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()
    
    def marcar_error_procesamiento(self, consulta_id: int, error_msg: str) -> bool:
        cursor = self.connection.cursor()
        try:
            error_resumen = f"ERROR_PROCESAMIENTO: {error_msg[:500]}"
            query = """
            UPDATE expokossodo_consultas 
            SET resumen = %s 
            WHERE id = %s
            """
            cursor.execute(query, (error_resumen, consulta_id))
            self.connection.commit()
            logger.warning(f"Marcado error en consulta ID: {consulta_id}")
            return True
        except Error as e:
            logger.error(f"Error marcando error para ID {consulta_id}: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def obtener_estadisticas(self) -> Dict:
        cursor = self.connection.cursor(dictionary=True)
        try:
            stats = {}
            
            # Total de consultas con transcripción activa
            cursor.execute("SELECT COUNT(*) as total FROM expokossodo_consultas WHERE uso_transcripcion = 1")
            stats['total_transcripciones'] = cursor.fetchone()['total']
            
            # Consultas procesadas (con resumen)
            cursor.execute("""
                SELECT COUNT(*) as procesadas 
                FROM expokossodo_consultas 
                WHERE uso_transcripcion = 1 AND resumen IS NOT NULL AND resumen != ''
            """)
            stats['procesadas'] = cursor.fetchone()['procesadas']
            
            # Consultas pendientes
            cursor.execute("""
                SELECT COUNT(*) as pendientes 
                FROM expokossodo_consultas 
                WHERE uso_transcripcion = 1 AND (resumen IS NULL OR resumen = '')
            """)
            stats['pendientes'] = cursor.fetchone()['pendientes']
            
            # Consultas con errores
            cursor.execute("""
                SELECT COUNT(*) as errores 
                FROM expokossodo_consultas 
                WHERE uso_transcripcion = 1 AND resumen LIKE 'ERROR_PROCESAMIENTO:%'
            """)
            stats['errores'] = cursor.fetchone()['errores']
            
            return stats
            
        except Error as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            raise
        finally:
            cursor.close()
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión MySQL cerrada")