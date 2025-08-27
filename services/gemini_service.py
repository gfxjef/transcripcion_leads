import google.generativeai as genai
import json
import time
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Optional
import re

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API')
        self.model_name = "gemini-2.0-flash-exp"
        self.max_retries = int(os.getenv('MAX_RETRIES', 5))
        self.rate_limit_delay = 60 / int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', 60))
        
        if not self.api_key:
            raise ValueError("GOOGLE_API key no encontrada en variables de entorno")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"GeminiService inicializado con modelo: {self.model_name}")
    
    def _construir_prompt_tecnico(self, consulta_texto: str) -> str:
        return f"""
Eres un asistente experto en análisis de llamadas técnicas de soporte.

INSTRUCCIONES CRÍTICAS:
- Extrae el 100% de la información relevante del texto
- NO inventes, inferas o agregues datos que no estén explícitamente mencionados
- Mantén absoluta fidelidad al contenido original
- Si no hay información específica para una sección, devuelve un array vacío []
- Sé exhaustivo con detalles técnicos, nombres de equipos, números, configuraciones, estadísticas

TEXTO DE LA CONSULTA:
{consulta_texto}

FORMATO DE RESPUESTA (JSON estricto):
{{
    "resumen_general": "Descripción concisa de la llamada sin perder contexto técnico",
    "requerimientos_cliente": ["Lista exacta de lo que solicita el cliente"],
    "detalles_tecnicos": ["Especificaciones técnicas, configuraciones, parámetros mencionados"],
    "equipos_modelos": ["Nombres exactos de hardware/software, modelos, versiones mencionados"],
    "metricas_uso": ["Datos cuantitativos, estadísticas, números, porcentajes citados"],
    "acciones_recomendadas": ["Pasos específicos sugeridos o discutidos durante la llamada"]
}}

RESPONDE ÚNICAMENTE CON EL JSON, SIN TEXTO ADICIONAL.
"""
    
    def _limpiar_respuesta_json(self, respuesta_raw: str) -> str:
        """Limpia la respuesta para extraer solo el JSON válido"""
        respuesta_raw = respuesta_raw.strip()
        
        # Buscar JSON entre ```json o simplemente el objeto JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', respuesta_raw, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        json_match = re.search(r'(\{.*\})', respuesta_raw, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return respuesta_raw
    
    def _validar_estructura_respuesta(self, respuesta_json: Dict) -> bool:
        """Valida que la respuesta tenga la estructura esperada"""
        campos_requeridos = [
            "resumen_general",
            "requerimientos_cliente", 
            "detalles_tecnicos",
            "equipos_modelos",
            "metricas_uso",
            "acciones_recomendadas"
        ]
        
        for campo in campos_requeridos:
            if campo not in respuesta_json:
                logger.error(f"Campo faltante en respuesta: {campo}")
                return False
            
            # Verificar que los arrays sean realmente arrays
            if campo != "resumen_general" and not isinstance(respuesta_json[campo], list):
                logger.error(f"Campo {campo} no es una lista")
                return False
        
        return True
    
    def generar_resumen(self, consulta_texto: str, consulta_id: int) -> Optional[str]:
        """Genera resumen usando Gemini con reintentos automáticos"""
        if not consulta_texto or len(consulta_texto.strip()) == 0:
            logger.warning(f"Consulta vacía para ID: {consulta_id}")
            return None
        
        prompt = self._construir_prompt_tecnico(consulta_texto)
        
        for intento in range(1, self.max_retries + 1):
            try:
                logger.info(f"Generando resumen para consulta {consulta_id} - Intento {intento}")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                # Generar contenido
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=4096,
                    )
                )
                
                if not response.text:
                    raise ValueError("Respuesta vacía de Gemini")
                
                # Limpiar y parsear JSON
                json_limpio = self._limpiar_respuesta_json(response.text)
                resumen_dict = json.loads(json_limpio)
                
                # Validar estructura
                if not self._validar_estructura_respuesta(resumen_dict):
                    raise ValueError("Estructura de respuesta inválida")
                
                # Convertir a JSON string para almacenar
                resumen_final = json.dumps(resumen_dict, ensure_ascii=False, indent=2)
                
                logger.info(f"Resumen generado exitosamente para consulta {consulta_id}")
                return resumen_final
                
            except json.JSONDecodeError as e:
                logger.error(f"Error JSON en intento {intento} para consulta {consulta_id}: {e}")
                logger.debug(f"Contenido problemático: {response.text[:500]}...")
                
            except Exception as e:
                logger.error(f"Error en intento {intento} para consulta {consulta_id}: {e}")
                
                # Si es el último intento, re-lanzar la excepción
                if intento == self.max_retries:
                    raise
                
                # Esperar antes del siguiente intento (backoff exponencial)
                tiempo_espera = min(60, 2 ** intento)
                logger.info(f"Esperando {tiempo_espera}s antes del siguiente intento...")
                time.sleep(tiempo_espera)
        
        logger.error(f"Falló generación de resumen para consulta {consulta_id} después de {self.max_retries} intentos")
        return None
    
    def test_conexion(self) -> bool:
        """Prueba la conexión con Gemini"""
        try:
            response = self.model.generate_content("Responde solo: OK")
            return response.text.strip().upper() == "OK"
        except Exception as e:
            logger.error(f"Error en test de conexión: {e}")
            return False