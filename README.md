# Sistema de Resumen de Llamadas Técnicas

Sistema automatizado para procesar y resumir consultas técnicas usando **Gemini 2.5 Flash** de Google AI.

## 🎯 Características

- ✅ **Procesamiento batch** de consultas pendientes
- ✅ **Reintentos automáticos** (hasta 5 intentos)
- ✅ **Rate limiting** respetando límites de Google API (60 req/min)
- ✅ **Extracción completa** de información técnica sin generar datos ficticios
- ✅ **Logging detallado** para monitoreo y debugging
- ✅ **API REST** con endpoints para control y estadísticas

## 📋 Estructura del Proyecto

```
transcripcion_expokossodo/
├── app.py                     # Aplicación Flask principal
├── requirements.txt           # Dependencias Python
├── test_sistema.py           # Script de pruebas
├── .env                      # Variables de entorno
└── services/
    ├── __init__.py
    ├── database_service.py   # Conexión y operaciones MySQL
    ├── gemini_service.py     # Cliente Google Gemini API
    └── batch_processor.py    # Procesador batch de consultas
```

## 🚀 Instalación

### 1. Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configuración de Base de Datos
Asegúrate que tu tabla tenga la columna `resumen`:
```sql
ALTER TABLE expokossodo_consultas ADD COLUMN resumen TEXT DEFAULT NULL;
```

### 3. Variables de Entorno
El archivo `.env` ya contiene tu configuración. Verifica que esté correcta:
```env
GOOGLE_API=AIzaSyD-T_yOIwIpLLAcuuVIToi865zVKVACR7Q
DB_HOST=atusaludlicoreria.com
DB_NAME=atusalud_kossomet
# ... resto de configuración
```

## 🧪 Pruebas

Antes de usar el sistema, ejecuta las pruebas:

```bash
# Todas las pruebas
python test_sistema.py

# Pruebas específicas
python test_sistema.py --test db      # Solo base de datos
python test_sistema.py --test gemini  # Solo Gemini API
python test_sistema.py --test pending # Solo consultas pendientes
python test_sistema.py --test prompt  # Solo generación de resumen
```

## 🔧 Uso

### Opción 1: Servidor Flask (Recomendado)

```bash
# Iniciar servidor
python app.py

# El servidor estará disponible en http://localhost:5000
```

**Endpoints disponibles:**

- `GET /health` - Estado del sistema
- `GET /stats` - Estadísticas de consultas
- `POST /procesar-resumenes` - Procesar todas las consultas pendientes
- `POST /procesar-consulta/<id>` - Procesar consulta específica
- `GET /test-gemini` - Probar conexión con Gemini

### Opción 2: Procesamiento directo

```python
from services.batch_processor import BatchProcessor

# Procesar todas las consultas pendientes
processor = BatchProcessor()
resultado = processor.procesar_consultas_pendientes()
print(resultado)
```

## 📊 Formato del Resumen

El sistema genera un JSON estructurado con:

```json
{
  "resumen_general": "Descripción concisa de la llamada",
  "requerimientos_cliente": ["Lista de solicitudes exactas"],
  "detalles_tecnicos": ["Especificaciones, configuraciones"],
  "equipos_modelos": ["Hardware/software mencionado"],
  "metricas_uso": ["Datos cuantitativos, estadísticas"],
  "acciones_recomendadas": ["Pasos sugeridos"]
}
```

## 🔍 Logging y Monitoreo

Los logs se guardan en:
- **Archivo**: `resumen_llamadas.log`
- **Consola**: Salida estándar

Niveles de log importantes:
- `INFO`: Progreso normal del procesamiento
- `WARNING`: Consultas saltadas o problemas menores
- `ERROR`: Errores en procesamiento individual
- `CRITICAL`: Errores del sistema

## ⚡ Deployment en Render

### 1. Preparar para producción

```bash
# Instalar gunicorn (ya está en requirements.txt)
pip install gunicorn
```

### 2. Comando de inicio en Render
```
gunicorn --bind 0.0.0.0:$PORT app:app
```

### 3. Variables de entorno en Render
Configura todas las variables del `.env` en el panel de Render.

## 📈 Monitoreo de Performance

El sistema incluye métricas automáticas:

- **Tiempo total** de procesamiento batch
- **Consultas procesadas** exitosamente  
- **Errores** por consulta con detalles
- **Rate limiting** automático
- **Reintentos** con backoff exponencial

## 🚨 Manejo de Errores

### Errores Comunes:

1. **`GOOGLE_API key no encontrada`**
   - Verifica que la variable esté en `.env`

2. **`Error conectando a MySQL`**
   - Revisa credenciales de BD en `.env`
   - Verifica conectividad de red

3. **`Gemini API no responde`**
   - Verifica límites de API rate
   - Revisa que la API key sea válida

4. **`Estructura de respuesta inválida`**
   - El sistema reintentará automáticamente
   - Revisa logs para patrones en errores

### Recuperación Automática:

- **Reintentos**: Hasta 5 intentos por consulta
- **Rate limiting**: Respeta límites de Google (60/min)
- **Marcado de errores**: Consultas problemáticas se marcan en BD
- **Continuidad**: Si una consulta falla, continúa con la siguiente

## 🔧 Configuración Avanzada

### Rate Limiting
```env
RATE_LIMIT_REQUESTS_PER_MINUTE=60  # Ajustar según tu plan de Google
```

### Batch Processing
```env
BATCH_DELAY_SECONDS=5  # Pausa entre consultas
MAX_RETRIES=5          # Intentos máximos por consulta
```

## 📞 Soporte

Para problemas o mejoras:
1. Revisa los logs en `resumen_llamadas.log`
2. Ejecuta `python test_sistema.py` para diagnosticar
3. Verifica conectividad de BD y APIs

---

**🤖 Sistema implementado con Gemini 2.0 Flash para máxima precisión en extracción técnica**# transcripcion_leads
