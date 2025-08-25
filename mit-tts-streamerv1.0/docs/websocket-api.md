# WebSocket API Documentation

## MIT-TTS-Streamer WebSocket API

La API WebSocket de MIT-TTS-Streamer proporciona streaming de audio TTS en tiempo real con interrupciones inmediatas y baja latencia.

### Conexión

```
ws://localhost:8001
```

### Características Principales

- **Streaming en tiempo real**: Audio enviado por chunks conforme se genera
- **Interrupciones inmediatas**: Latencia <10ms para interrumpir síntesis
- **Gestión de sesiones**: Múltiples usuarios concurrentes
- **Sistema de prioridades**: NORMAL, HIGH, CRITICAL
- **Configuración por sesión**: Idioma, voz, formato, velocidad

## Formato de Mensajes

Todos los mensajes siguen el formato JSON:

```json
{
  "type": "message_type",
  "data": { ... },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

## Mensajes Cliente → Servidor

### 1. Síntesis de Texto

Solicitar síntesis de texto con streaming de audio.

```json
{
  "type": "synthesize",
  "data": {
    "text": "Texto a sintetizar",
    "priority": "normal"  // "normal", "high", "critical"
  }
}
```

**Parámetros:**
- `text` (string, requerido): Texto a sintetizar
- `priority` (string, opcional): Prioridad de la tarea (default: "normal")

### 2. Interrupción

Interrumpir síntesis actual inmediatamente.

```json
{
  "type": "interrupt",
  "data": {}
}
```

### 3. Actualización de Configuración

Actualizar configuración de la sesión.

```json
{
  "type": "config_update",
  "data": {
    "config": {
      "language": "es",
      "voice_id": 0,
      "speed": 1.0,
      "format": "wav",
      "sample_rate": 22050,
      "chunk_size": 1024
    }
  }
}
```

**Configuraciones disponibles:**
- `language` (string): Código de idioma ("es", "en", etc.)
- `voice_id` (int): ID de la voz (0-N)
- `speed` (float): Velocidad de síntesis (0.5-2.0)
- `format` (string): Formato de audio ("wav", "mp3", "ogg")
- `sample_rate` (int): Frecuencia de muestreo (8000, 16000, 22050, 44100)
- `chunk_size` (int): Tamaño de chunk en bytes

### 4. Ping

Verificar conectividad y medir latencia.

```json
{
  "type": "ping",
  "data": {}
}
```

## Mensajes Servidor → Cliente

### 1. Inicio de Síntesis

Confirmación de que la síntesis ha comenzado.

```json
{
  "type": "synthesis_start",
  "data": {
    "text": "Texto siendo sintetizado",
    "priority": "normal"
  },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

### 2. Chunk de Audio

Datos de audio en streaming.

```json
{
  "type": "audio_chunk",
  "data": {
    "chunk_index": 0,
    "total_chunks": 5,
    "audio_data": "hexadecimal_encoded_audio",
    "format": "wav"
  },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

**Campos:**
- `chunk_index`: Índice del chunk actual (0-based)
- `total_chunks`: Total de chunks esperados
- `audio_data`: Datos de audio codificados en hexadecimal
- `format`: Formato del audio

### 3. Síntesis Completada

Confirmación de síntesis completada exitosamente.

```json
{
  "type": "synthesis_complete",
  "data": {
    "text": "Texto sintetizado",
    "total_chunks": 5,
    "synthesis_time_ms": 250.5,
    "audio_bytes": 12345
  },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

### 4. Síntesis Interrumpida

Confirmación de interrupción exitosa.

```json
{
  "type": "interrupted",
  "data": {
    "interrupted_tasks": 2,
    "latency_ms": 8.5
  },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

### 5. Configuración Actualizada

Confirmación de actualización de configuración.

```json
{
  "type": "config_updated",
  "data": {
    "config": { ... },
    "status": "updated"
  },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

### 6. Pong

Respuesta al ping con medición de latencia.

```json
{
  "type": "pong",
  "data": {
    "timestamp": 1234567890.123  // timestamp original del ping
  },
  "session_id": "uuid",
  "timestamp": 1234567890.456
}
```

### 7. Error de Síntesis

Error durante el proceso de síntesis.

```json
{
  "type": "synthesis_error",
  "data": {
    "error": "Descripción del error",
    "task_id": "task_uuid"
  },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

### 8. Error General

Error general del servidor.

```json
{
  "type": "error",
  "data": {
    "error": "Descripción del error"
  },
  "session_id": "uuid",
  "timestamp": 1234567890.123
}
```

## Flujo de Trabajo Típico

### 1. Síntesis Básica

```
Cliente → Servidor: synthesize
Servidor → Cliente: synthesis_start
Servidor → Cliente: audio_chunk (múltiples)
Servidor → Cliente: synthesis_complete
```

### 2. Síntesis con Interrupción

```
Cliente → Servidor: synthesize
Servidor → Cliente: synthesis_start
Servidor → Cliente: audio_chunk
Cliente → Servidor: interrupt
Servidor → Cliente: interrupted
```

### 3. Configuración de Sesión

```
Cliente → Servidor: config_update
Servidor → Cliente: config_updated
Cliente → Servidor: synthesize (con nueva config)
```

## Códigos de Estado de Conexión

- **1000**: Cierre normal
- **1001**: Endpoint desconectado
- **1002**: Error de protocolo
- **1003**: Datos no soportados
- **1011**: Error interno del servidor

## Límites y Restricciones

- **Conexiones máximas por IP**: 10 (configurable)
- **Tamaño máximo de mensaje**: 64KB
- **Timeout de sesión**: 300 segundos (configurable)
- **Tamaño máximo de texto**: 10,000 caracteres
- **Cola máxima por sesión**: 100 tareas

## Métricas de Rendimiento

El servidor proporciona métricas de rendimiento:

- **Latencia de síntesis**: Tiempo desde solicitud hasta primer chunk
- **Latencia de interrupción**: Tiempo para procesar interrupción
- **Throughput**: Chunks de audio por segundo
- **Conexiones concurrentes**: Número de sesiones activas

## Ejemplos de Uso

### JavaScript (Browser)

```javascript
const ws = new WebSocket('ws://localhost:8001');

ws.onopen = function() {
    console.log('Conectado al servidor TTS');
    
    // Solicitar síntesis
    ws.send(JSON.stringify({
        type: 'synthesize',
        data: {
            text: 'Hola mundo',
            priority: 'normal'
        }
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'audio_chunk':
            // Procesar chunk de audio
            const audioData = hexToBytes(message.data.audio_data);
            playAudio(audioData);
            break;
            
        case 'synthesis_complete':
            console.log('Síntesis completada');
            break;
            
        case 'error':
            console.error('Error:', message.data.error);
            break;
    }
};

// Interrumpir síntesis
function interrupt() {
    ws.send(JSON.stringify({
        type: 'interrupt',
        data: {}
    }));
}
```

### Python (Cliente)

```python
import asyncio
import json
import websockets

async def tts_client():
    uri = "ws://localhost:8001"
    
    async with websockets.connect(uri) as websocket:
        # Solicitar síntesis
        await websocket.send(json.dumps({
            "type": "synthesize",
            "data": {
                "text": "Hola mundo",
                "priority": "normal"
            }
        }))
        
        # Escuchar respuestas
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "audio_chunk":
                # Procesar chunk de audio
                audio_hex = data["data"]["audio_data"]
                audio_bytes = bytes.fromhex(audio_hex)
                # Reproducir o guardar audio
                
            elif data["type"] == "synthesis_complete":
                print("Síntesis completada")
                break

asyncio.run(tts_client())
```

## Manejo de Errores

### Errores Comunes

1. **Texto vacío**: Error si se envía texto vacío para síntesis
2. **Sesión no encontrada**: Error si la sesión ha expirado
3. **Formato no soportado**: Error si se solicita formato de audio no disponible
4. **Cola llena**: Error si se excede el límite de tareas en cola
5. **Conexión perdida**: Reconexión automática recomendada

### Estrategias de Recuperación

1. **Reconexión automática** con backoff exponencial
2. **Reintento de mensajes** para operaciones críticas
3. **Validación de mensajes** antes del envío
4. **Timeout de operaciones** para evitar bloqueos

## Configuración del Servidor

El servidor WebSocket se configura en `config/default.json`:

```json
{
  "websocket": {
    "host": "0.0.0.0",
    "port": 8001,
    "max_connections": 100,
    "max_connections_per_ip": 10,
    "session_timeout": 300,
    "ping_interval": 30,
    "ping_timeout": 10,
    "max_message_size": 65536,
    "max_queue_size": 1000
  }
}
```

## Seguridad

- **Validación de entrada**: Todos los mensajes son validados
- **Límites de rate**: Prevención de spam y DoS
- **Timeout de sesiones**: Limpieza automática de sesiones inactivas
- **Límites de recursos**: Prevención de agotamiento de memoria

Para más información, consulta la [documentación de la API REST](http-rest-api.md) y los [ejemplos de cliente](../examples/).