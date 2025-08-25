# MIT-TTS-Streamer HTTP REST API

## Documentación Completa de la API REST

### 🌐 Información General

- **Base URL**: `http://localhost:8080`
- **Documentación Interactiva**: `http://localhost:8080/docs`
- **Redoc**: `http://localhost:8080/redoc`
- **Formato**: JSON
- **Autenticación**: Ninguna (por ahora)

### 📊 Endpoints Disponibles

## 1. Salud y Estado del Sistema

### `GET /api/v1/health`
Verificar salud del servidor

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "components": {
    "config_manager": "healthy",
    "session_manager": "not_initialized",
    "queue_manager": "not_initialized",
    "tts_engine": "not_initialized"
  }
}
```

### `GET /api/v1/status`
Estado detallado del sistema

**Respuesta:**
```json
{
  "status": "running",
  "timestamp": "2025-01-01T12:00:00",
  "server": {
    "uptime_seconds": 3600.5,
    "host": "0.0.0.0",
    "http_port": 8080,
    "websocket_port": 8081,
    "max_connections": 100
  },
  "tts_engine": {
    "engine": "melo",
    "device": "cpu",
    "default_language": "es",
    "supported_languages": ["es", "en", "fr"],
    "preload_languages": ["es", "en"]
  },
  "audio_processor": {
    "default_format": "wav",
    "supported_formats": ["wav", "mp3", "ogg", "flac"],
    "buffer_size": 4096
  },
  "active_connections": 0,
  "queue_status": {
    "max_size": 1000,
    "current_size": 0,
    "worker_processes": 4
  }
}
```

### `GET /api/v1/metrics`
Métricas de rendimiento

**Respuesta:**
```json
{
  "timestamp": "2025-01-01T12:00:00",
  "uptime_seconds": 3600.5,
  "active_sessions": 5,
  "total_requests": 1250,
  "average_latency_ms": 45.2,
  "queue_size": 3,
  "memory_usage_mb": 256.8,
  "cpu_usage_percent": 15.3
}
```

## 2. Gestión de Configuración

### `GET /api/v1/config`
Obtener configuración actual

**Respuesta:**
```json
{
  "server": {
    "host": "0.0.0.0",
    "http_port": 8080,
    "websocket_port": 8081,
    "max_connections": 100
  },
  "tts": {
    "engine": "melo",
    "device": "cpu",
    "default_language": "es",
    "default_voice_id": 0,
    "default_speed": 1.0
  },
  "audio": {
    "default_format": "wav",
    "supported_formats": ["wav", "mp3", "ogg"]
  }
}
```

### `POST /api/v1/config`
Actualizar configuración

**Request Body:**
```json
{
  "server": {
    "max_connections": 200
  },
  "tts": {
    "default_language": "en",
    "default_speed": 1.2
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

**Respuesta:**
```json
{
  "status": "success",
  "message": "Configuration updated successfully"
}
```

### `POST /api/v1/config/reload`
Recargar configuración desde archivo

**Respuesta:**
```json
{
  "status": "success",
  "message": "Configuration reloaded successfully"
}
```

### `POST /api/v1/config/save`
Guardar configuración actual

**Respuesta:**
```json
{
  "status": "success",
  "message": "Configuration saved successfully"
}
```

## 3. Voces e Idiomas

### `GET /api/v1/voices`
Listar voces disponibles

**Respuesta:**
```json
[
  {
    "code": "es",
    "name": "Spanish",
    "speakers": [
      {
        "id": 0,
        "name": "ES-Female-1",
        "gender": "female",
        "description": "Voz femenina española estándar",
        "sample_rate": 22050,
        "quality": "high"
      },
      {
        "id": 1,
        "name": "ES-Male-1",
        "gender": "male",
        "description": "Voz masculina española estándar",
        "sample_rate": 22050,
        "quality": "high"
      }
    ]
  },
  {
    "code": "en",
    "name": "English",
    "speakers": [
      {
        "id": 0,
        "name": "EN-Female-1",
        "gender": "female",
        "description": "Standard English female voice",
        "sample_rate": 22050,
        "quality": "high"
      }
    ]
  }
]
```

### `GET /api/v1/languages`
Idiomas soportados

**Respuesta:**
```json
{
  "supported_languages": ["es", "en", "fr", "zh", "jp", "kr"],
  "preload_languages": ["es", "en"],
  "default_language": "es"
}
```

## 4. Gestión de Sesiones

### `POST /api/v1/sessions`
Crear nueva sesión

**Request Body:**
```json
{
  "language": "es",
  "voice_id": 0,
  "format": "wav",
  "sample_rate": 22050,
  "speed": 1.0
}
```

**Respuesta:**
```json
{
  "session_id": "session_1640995200",
  "created_at": "2025-01-01T12:00:00",
  "last_activity": "2025-01-01T12:00:00",
  "config": {
    "language": "es",
    "voice_id": 0,
    "format": "wav",
    "sample_rate": 22050,
    "speed": 1.0
  },
  "is_active": true
}
```

### `GET /api/v1/sessions/{session_id}`
Obtener información de sesión

**Respuesta:**
```json
{
  "session_id": "session_1640995200",
  "created_at": "2025-01-01T12:00:00",
  "last_activity": "2025-01-01T12:05:30",
  "config": {
    "language": "es",
    "voice_id": 0
  },
  "is_active": true
}
```

### `DELETE /api/v1/sessions/{session_id}`
Cerrar sesión

**Respuesta:**
```json
{
  "status": "success",
  "message": "Session session_1640995200 closed"
}
```

### `GET /api/v1/sessions`
Listar sesiones activas

**Respuesta:**
```json
{
  "sessions": [
    {
      "session_id": "session_1640995200",
      "created_at": "2025-01-01T12:00:00",
      "is_active": true
    }
  ],
  "total": 1
}
```

## 5. Control de Interrupciones

### `POST /api/v1/interrupt/{session_id}`
Interrumpir sesión específica

**Respuesta:**
```json
{
  "status": "success",
  "message": "Session session_1640995200 interrupted"
}
```

### `POST /api/v1/interrupt/all`
Interrumpir todas las sesiones

**Respuesta:**
```json
{
  "status": "success",
  "message": "All sessions interrupted"
}
```

## 📝 Códigos de Estado HTTP

- `200 OK` - Operación exitosa
- `201 Created` - Recurso creado exitosamente
- `400 Bad Request` - Solicitud inválida
- `404 Not Found` - Recurso no encontrado
- `500 Internal Server Error` - Error interno del servidor

## 🔧 Headers de Respuesta

Todas las respuestas incluyen headers adicionales:

- `X-Process-Time` - Tiempo de procesamiento en segundos
- `X-Request-ID` - ID único de la solicitud
- `Content-Type: application/json`

## 📊 Ejemplos de Uso

### Verificar Estado del Servidor
```bash
curl -X GET "http://localhost:8080/api/v1/health"
```

### Obtener Configuración
```bash
curl -X GET "http://localhost:8080/api/v1/config"
```

### Actualizar Configuración
```bash
curl -X POST "http://localhost:8080/api/v1/config" \
  -H "Content-Type: application/json" \
  -d '{
    "tts": {
      "default_language": "en",
      "default_speed": 1.2
    }
  }'
```

### Crear Sesión TTS
```bash
curl -X POST "http://localhost:8080/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "es",
    "voice_id": 0,
    "format": "wav",
    "sample_rate": 22050,
    "speed": 1.0
  }'
```

### Obtener Voces Disponibles
```bash
curl -X GET "http://localhost:8080/api/v1/voices"
```

### Interrumpir Todas las Sesiones
```bash
curl -X POST "http://localhost:8080/api/v1/interrupt/all"
```

## 🐍 Cliente Python

Ejemplo usando el cliente HTTP incluido:

```python
from examples.http_client_example import TTSHTTPClient

# Crear cliente
client = TTSHTTPClient("http://localhost:8080")

# Verificar salud
health = client.health_check()
print(f"Server status: {health['status']}")

# Crear sesión
session = client.create_session({
    "language": "es",
    "voice_id": 0,
    "format": "wav"
})
print(f"Session created: {session['session_id']}")

# Obtener métricas
metrics = client.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
```

## 🌐 Documentación Interactiva

Una vez que el servidor esté ejecutándose, puedes acceder a:

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

Estas interfaces permiten:
- Explorar todos los endpoints
- Probar la API directamente desde el navegador
- Ver esquemas de datos detallados
- Generar código de cliente automáticamente

## 🔒 Seguridad

**Nota**: La implementación actual no incluye autenticación. Para producción, considera:

- Autenticación por API Key
- Rate limiting
- HTTPS/TLS
- Validación de entrada estricta
- Logging de seguridad

## 🚀 Próximas Funcionalidades

- Autenticación y autorización
- Rate limiting avanzado
- Streaming de audio por HTTP
- Webhooks para eventos
- Métricas de Prometheus
- Health checks más detallados