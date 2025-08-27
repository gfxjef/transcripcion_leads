#!/usr/bin/env python3
"""
Script de prueba para el sistema de resúmenes de consultas técnicas
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Agregar el directorio actual al path para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from services.gemini_service import GeminiService
from services.batch_processor import BatchProcessor

load_dotenv()

# Configurar logging para testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("\nProbando conexion a MySQL...")
    try:
        db_service = DatabaseService()
        stats = db_service.obtener_estadisticas()
        print("Conexion a MySQL exitosa")
        print(f"Estadisticas actuales:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        db_service.close()
        return True
    except Exception as e:
        print(f"Error en conexion MySQL: {e}")
        return False

def test_gemini_connection():
    """Prueba la conexión con Gemini API"""
    print("\nProbando conexion a Gemini API...")
    try:
        gemini_service = GeminiService()
        if gemini_service.test_conexion():
            print(f"Gemini API conectado - Modelo: {gemini_service.model_name}")
            return True
        else:
            print("Gemini API no responde correctamente")
            return False
    except Exception as e:
        print(f"Error en conexion Gemini: {e}")
        return False

def test_prompt_ejemplo():
    """Prueba el prompt con un texto de ejemplo"""
    print("\nProbando generacion de resumen con texto de ejemplo...")
    
    texto_ejemplo = """
    Cliente reporta problemas con su router TP-Link Archer AX6000. 
    El equipo presenta desconexiones intermitentes cada 2-3 horas desde hace una semana.
    Velocidad contratada: 500 Mbps, pero solo alcanza 120 Mbps en WiFi 5GHz.
    Firmware actual: 1.2.3 Build 20231215.
    Configuración actual: Canal 36, ancho de banda 80MHz.
    Cliente solicita actualización de firmware y optimización de canales.
    Equipos conectados: 15 dispositivos (8 móviles, 4 laptops, 2 smart TV, 1 NAS).
    Temperatura del router: 68°C durante picos de uso.
    Se recomienda: actualizar firmware a versión 1.3.1, cambiar a canal 149, 
    reducir potencia TX a 75%, programar reinicio automático cada 48 horas.
    """
    
    try:
        gemini_service = GeminiService()
        resumen = gemini_service.generar_resumen(texto_ejemplo, 9999)
        
        if resumen:
            print("Resumen generado exitosamente:")
            print("=" * 60)
            print(resumen)
            print("=" * 60)
            return True
        else:
            print("No se pudo generar el resumen")
            return False
            
    except Exception as e:
        print(f"Error generando resumen: {e}")
        return False

def test_consultas_pendientes():
    """Muestra consultas pendientes sin procesarlas"""
    print("\nVerificando consultas pendientes...")
    try:
        db_service = DatabaseService()
        consultas = db_service.get_consultas_pendientes()
        
        print(f"Encontradas {len(consultas)} consultas pendientes")
        
        if consultas:
            print("\nPrimeras 3 consultas:")
            for i, consulta in enumerate(consultas[:3], 1):
                print(f"\n--- Consulta {i} ---")
                print(f"ID: {consulta['id']}")
                print(f"Asesor: {consulta['asesor_nombre']}")
                print(f"Fecha: {consulta['fecha_consulta']}")
                print(f"Texto: {consulta['consulta'][:200]}...")
        
        db_service.close()
        return True
        
    except Exception as e:
        print(f"Error obteniendo consultas: {e}")
        return False

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("INICIANDO PRUEBAS DEL SISTEMA DE RESUMENES")
    print("=" * 60)
    
    tests = [
        ("Base de Datos", test_database_connection),
        ("Gemini API", test_gemini_connection),
        ("Consultas Pendientes", test_consultas_pendientes),
        ("Generación de Resumen", test_prompt_ejemplo),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS:")
    
    for test_name, success in results.items():
        status = "PASO" if success else "FALLO"
        print(f"   {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\nTodas las pruebas pasaron! El sistema esta listo.")
        print("\nPara ejecutar el procesamiento batch:")
        print("   python -c \"from services.batch_processor import BatchProcessor; BatchProcessor().procesar_consultas_pendientes()\"")
        print("\nPara iniciar el servidor:")
        print("   python app.py")
    else:
        print("\nAlgunas pruebas fallaron. Revisa la configuracion.")
    
    return all_passed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pruebas del sistema de resúmenes")
    parser.add_argument("--test", choices=["db", "gemini", "pending", "prompt", "all"], 
                       default="all", help="Tipo de prueba a ejecutar")
    
    args = parser.parse_args()
    
    if args.test == "db":
        test_database_connection()
    elif args.test == "gemini":
        test_gemini_connection()
    elif args.test == "pending":
        test_consultas_pendientes()
    elif args.test == "prompt":
        test_prompt_ejemplo()
    else:
        run_all_tests()