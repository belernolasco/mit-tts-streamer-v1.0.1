# 📚 Documentación Técnica - MIT-TTS-Streamer

**Autor:** Beler Nolasco Almonte

Esta documentación técnica proporciona información detallada sobre la arquitectura, implementación y funcionamiento interno del sistema MIT-TTS-Streamer.

## 🏗️ Arquitectura del Sistema

### Visión General
MIT-TTS-Streamer es un servidor de síntesis de voz (TTS) de baja latencia diseñado para aplicaciones conversacionales en tiempo real. El sistema utiliza una arquitectura híbrida que combina HTTP REST API para control y WebSocket para streaming de audio.

```
┌─────────────────────────────────────────────────────────────┐
│                    MIT-TTS-Streamer                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ HTTP Server │  │ WebSocket   │  │ Session Manager     │  │
│  │ (FastAPI)   │  │ Server      │  │                     │  │
│  │ Port: 8000  │  │ Port: 8001  │  │ Multi-user Support  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Priority    │  │ TTS Engine  │  │ Audio Processor     │  │
│  │ Queue       │  │ (MeloTTS)   │  │ (WAV/MP3/OGG)      │  │
│  │ System      │  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Config      │  │ Logging &   │  │ Monitoring &        │  │
│  │ Manager     │  │ Error       │  │ Metrics             │  │
│  │             │  │ Handling    │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

#### 1. **HTTP Server (FastAPI)**
- **Puerto**: 8000 (configurable)
- **Función**: API REST para control y configuración
- **Características**:
  - Documentación automática con Swagger/OpenAPI
  - Validación automática de datos con Pydantic
  - Middleware para CORS, logging y autenticación
  - Endpoints para gestión de voces, configuración y monitoreo

#### 2. **WebSocket Server**
- **Puerto**: 8001 (configurable)
- **Función**: Streaming de audio en tiempo real
- **Características**:
  - Latencia ultra-baja (<10ms para interrupciones)
  - Soporte para múltiples conexiones concurrentes
  - Protocolo de mensajes binarios y JSON
  - Gestión automática de reconexión

#### 3. **Session Manager**
- **Función**: Gestión de sesiones multi-usuario
- **Características**:
  - Identificación única por sesión
  - Aislamiento de contexto entre usuarios
  - Limpieza automática de sesiones inactivas
  - Balanceado de carga entre sesiones

#### 4. **Priority Queue System**
- **Función**: Gestión de tareas con prioridades
- **Niveles de Prioridad**:
  - `CRITICAL`: Interrupciones inmediatas
  - `HIGH`: Solicitudes de usuarios premium
  - `NORMAL`: Solicitudes estándar
- **Características**:
  - Procesamiento FIFO dentro de cada prioridad
  - Preemption para tareas críticas
  - Métricas de rendimiento por prioridad

#### 5. **TTS Engine (MeloTTS)**
- **Función**: Motor de síntesis de voz
- **Características**:
  - Soporte multi-idioma (ES, EN, FR, etc.)
  - Múltiples voces por idioma
  - Optimización para baja latencia
  - Cache de modelos en memoria

#### 6. **Audio Processor**
- **Función**: Procesamiento y conversión de audio
- **Formatos Soportados**: WAV, MP3, OGG
- **Características**:
  - Conversión de formato en tiempo real
  - Normalización de audio
  - Compresión adaptativa
  - Streaming chunked

## 🔧 Especificaciones de la API

### HTTP REST API

#### Base URL
```
http://localhost:8000/api/v1
```

#### Autenticación
```http
Authorization: Bearer <token>
```

#### Endpoints Principales

##### 1. Health Check
```http
GET /health
```
**Respuesta:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

##### 2. Status del Sistema
```http
GET /status
```
**Respuesta:**
```json
{
  "server": {
    "status": "running",
    "connections": 5,
    "uptime": 3600
  },
  "tts_engine": {
    "status": "ready",
    "loaded_models": ["es", "en"],
    "queue_size": 2
  },
  "resources": {
    "cpu_usage": 25.5,
    "memory_usage": 512.3,
    "disk_usage": 1024.7
  }
}
```

##### 3. Listar Voces
```http
GET /voices
```
**Respuesta:**
```json
{
  "voices": [
    {
      "id": "es-female-1",
      "language": "es",
      "gender": "female",
      "name": "María",
      "description": "Voz femenina española natural"
    }
  ]
}
```

##### 4. Síntesis de Voz (HTTP)
```http
POST /synthesize
Content-Type: application/json

{
  "text": "Hola mundo",
  "voice_id": "es-female-1",
  "format": "wav",
  "priority": "normal",
  "session_id": "user123"
}
```

**Respuesta:**
```json
{
  "task_id": "task_abc123",
  "status": "queued",
  "estimated_time": 0.5,
  "audio_url": "/audio/task_abc123.wav"
}
```

##### 5. Estado de Tarea
```http
GET /tasks/{task_id}
```

##### 6. Configuración
```http
GET /config
PUT /config
```

##### 7. Métricas
```http
GET /metrics
```

### WebSocket API

#### Conexión
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');
```

#### Protocolo de Mensajes

##### 1. Mensaje de Conexión
```json
{
  "type": "connect",
  "session_id": "user123",
  "auth_token": "bearer_token"
}
```

##### 2. Solicitud de Síntesis
```json
{
  "type": "synthesize",
  "text": "Hola mundo",
  "voice_id": "es-female-1",
  "format": "wav",
  "priority": "high",
  "stream": true
}
```

##### 3. Interrupción
```json
{
  "type": "interrupt",
  "reason": "user_stop"
}
```

##### 4. Respuesta de Audio (Binario)
```
[HEADER: 4 bytes - message_type]
[HEADER: 4 bytes - data_length]
[DATA: audio_bytes]
```

##### 5. Respuesta de Estado
```json
{
  "type": "status",
  "task_id": "task_abc123",
  "status": "processing|completed|error",
  "progress": 0.75,
  "error": null
}
```

## 🔄 Flujo de Procesamiento

### Flujo HTTP
```
1. Cliente → HTTP POST /synthesize
2. Validación de datos (Pydantic)
3. Creación de tarea con prioridad
4. Encolado en Priority Queue
5. Procesamiento por TTS Engine
6. Conversión de formato de audio
7. Almacenamiento temporal
8. Respuesta con URL de descarga
```

### Flujo WebSocket
```
1. Cliente → WebSocket connect
2. Autenticación y creación de sesión
3. Cliente → Mensaje de síntesis
4. Procesamiento inmediato (alta prioridad)
5. Streaming de audio en chunks
6. Cliente recibe audio en tiempo real
7. Posibilidad de interrupción inmediata
```

### Flujo de Interrupción
```
1. Cliente → Mensaje de interrupción
2. Marcado de tarea como cancelada
3. Detención inmediata del procesamiento
4. Limpieza de recursos
5. Notificación al cliente
6. Tiempo total: <10ms
```

## 🏛️ Arquitectura de Datos

### Modelos de Datos

#### 1. **SynthesisRequest**
```python
class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(..., regex=r'^[a-z]{2}-[a-z]+-\d+$')
    format: AudioFormat = Field(default=AudioFormat.WAV)
    priority: Priority = Field(default=Priority.NORMAL)
    session_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
```

#### 2. **Task**
```python
class Task:
    id: str
    request: SynthesisRequest
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    priority: Priority
    session_id: str
    result: Optional[bytes]
    error: Optional[str]
```

#### 3. **Session**
```python
class Session:
    id: str
    user_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    websocket: Optional[WebSocket]
    active_tasks: List[str]
    preferences: Dict[str, Any]
```

#### 4. **Voice**
```python
class Voice:
    id: str
    language: str
    gender: str
    name: str
    description: str
    model_path: str
    sample_rate: int
    is_available: bool
```

### Base de Datos

#### Almacenamiento en Memoria
- **Sessions**: Redis/In-memory dict
- **Tasks**: Redis con TTL
- **Cache de Audio**: LRU Cache con límite de tamaño

#### Almacenamiento Persistente
- **Configuración**: JSON files
- **Logs**: Archivos rotativos
- **Modelos TTS**: Sistema de archivos
- **Métricas**: InfluxDB (opcional)

## ⚡ Optimizaciones de Rendimiento

### Latencia Ultra-Baja

#### 1. **Optimizaciones de Red**
```python
# Configuración de WebSocket
WEBSOCKET_CONFIG = {
    'ping_interval': None,  # Deshabilitar ping/pong
    'ping_timeout': None,
    'close_timeout': 1,
    'max_size': 2**20,  # 1MB max message
    'compression': None  # Sin compresión para menor latencia
}
```

#### 2. **Optimizaciones de TTS**
```python
# Pre-carga de modelos
async def preload_models():
    for voice in AVAILABLE_VOICES:
        model = load_tts_model(voice.model_path)
        MODEL_CACHE[voice.id] = model

# Procesamiento en chunks
async def synthesize_streaming(text: str, voice_id: str):
    sentences = split_into_sentences(text)
    for sentence in sentences:
        audio_chunk = await synthesize_chunk(sentence, voice_id)
        yield audio_chunk
```

#### 3. **Optimizaciones de Audio**
```python
# Procesamiento paralelo
async def process_audio_parallel(audio_data: bytes, format: str):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=4) as executor:
        future = loop.run_in_executor(
            executor, convert_audio_format, audio_data, format
        )
        return await future
```

### Escalabilidad

#### 1. **Pool de Conexiones**
```python
# Gestión de conexiones WebSocket
class ConnectionPool:
    def __init__(self, max_connections: int = 1000):
        self.connections: Dict[str, WebSocket] = {}
        self.max_connections = max_connections
        
    async def add_connection(self, session_id: str, ws: WebSocket):
        if len(self.connections) >= self.max_connections:
            await self.cleanup_inactive_connections()
        self.connections[session_id] = ws
```

#### 2. **Load Balancing**
```python
# Balanceador de carga simple
class LoadBalancer:
    def __init__(self):
        self.workers = []
        self.current = 0
        
    def get_next_worker(self):
        worker = self.workers[self.current]
        self.current = (self.current + 1) % len(self.workers)
        return worker
```

## 🔒 Seguridad

### Autenticación y Autorización

#### 1. **JWT Tokens**
```python
# Configuración JWT
JWT_CONFIG = {
    'algorithm': 'HS256',
    'secret_key': os.getenv('JWT_SECRET_KEY'),
    'access_token_expire_minutes': 30,
    'refresh_token_expire_days': 7
}
```

#### 2. **Rate Limiting**
```python
# Limitación de velocidad
RATE_LIMITS = {
    'synthesize': '100/minute',
    'websocket': '1000/minute',
    'health': '1000/minute'
}
```

#### 3. **Validación de Entrada**
```python
# Sanitización de texto
def sanitize_text(text: str) -> str:
    # Remover caracteres peligrosos
    text = re.sub(r'[<>"\']', '', text)
    # Limitar longitud
    text = text[:MAX_TEXT_LENGTH]
    return text.strip()
```

### Protección contra Ataques

#### 1. **DDoS Protection**
```python
# Middleware de protección
class DDoSProtectionMiddleware:
    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
```

#### 2. **Input Validation**
```python
# Validación estricta
class StrictSynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    voice_id: str = Field(..., regex=r'^[a-z]{2}-[a-z]+-\d+$')
    
    @validator('text')
    def validate_text(cls, v):
        if any(char in v for char in '<>"\';'):
            raise ValueError('Caracteres no permitidos en el texto')
        return v
```

## 📊 Monitoreo y Métricas

### Métricas del Sistema

#### 1. **Métricas de Rendimiento**
```python
METRICS = {
    'requests_total': Counter('requests_total', 'Total requests'),
    'request_duration': Histogram('request_duration_seconds', 'Request duration'),
    'active_connections': Gauge('active_connections', 'Active WebSocket connections'),
    'queue_size': Gauge('queue_size', 'Current queue size'),
    'tts_latency': Histogram('tts_latency_seconds', 'TTS processing latency')
}
```

#### 2. **Health Checks**
```python
async def health_check():
    checks = {
        'tts_engine': await check_tts_engine(),
        'websocket_server': await check_websocket_server(),
        'database': await check_database(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    return all(checks.values()), checks
```

#### 3. **Alertas**
```python
# Sistema de alertas
class AlertManager:
    def __init__(self):
        self.thresholds = {
            'cpu_usage': 80,
            'memory_usage': 85,
            'queue_size': 100,
            'error_rate': 5
        }
    
    async def check_alerts(self):
        metrics = await get_current_metrics()
        for metric, threshold in self.thresholds.items():
            if metrics[metric] > threshold:
                await send_alert(metric, metrics[metric], threshold)
```

## 🧪 Testing

### Estrategia de Testing

#### 1. **Unit Tests**
```python
# Ejemplo de test unitario
class TestTTSEngine:
    async def test_synthesize_text(self):
        engine = TTSEngine()
        audio = await engine.synthesize("Hola mundo", "es-female-1")
        assert len(audio) > 0
        assert audio.startswith(b'RIFF')  # WAV header
```

#### 2. **Integration Tests**
```python
# Test de integración
class TestWebSocketAPI:
    async def test_websocket_synthesis(self):
        async with websockets.connect("ws://localhost:8001/ws") as ws:
            await ws.send(json.dumps({
                "type": "synthesize",
                "text": "Test",
                "voice_id": "es-female-1"
            }))
            response = await ws.recv()
            assert len(response) > 0
```

#### 3. **Load Tests**
```python
# Test de carga
async def load_test():
    tasks = []
    for i in range(100):
        task = asyncio.create_task(make_request())
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    success_rate = sum(1 for r in results if r.status_code == 200) / len(results)
    assert success_rate > 0.95
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# Servidor
MIT_TTS_HOST=0.0.0.0
MIT_TTS_HTTP_PORT=8000
MIT_TTS_WS_PORT=8001

# TTS Engine
MIT_TTS_MODEL_PATH=/app/models
MIT_TTS_CACHE_SIZE=1000
MIT_TTS_MAX_TEXT_LENGTH=5000

# Base de datos
MIT_TTS_REDIS_URL=redis://localhost:6379
MIT_TTS_DB_URL=sqlite:///app.db

# Seguridad
MIT_TTS_JWT_SECRET=your-secret-key
MIT_TTS_CORS_ORIGINS=*

# Logging
MIT_TTS_LOG_LEVEL=INFO
MIT_TTS_LOG_FILE=/app/logs/app.log

# Monitoreo
MIT_TTS_METRICS_ENABLED=true
MIT_TTS_PROMETHEUS_PORT=9090
```

### Configuración de Producción
```json
{
  "server": {
    "host": "0.0.0.0",
    "http_port": 8000,
    "ws_port": 8001,
    "workers": 4,
    "max_connections": 1000
  },
  "tts": {
    "model_path": "/app/models",
    "cache_size": 1000,
    "max_text_length": 5000,
    "supported_languages": ["es", "en", "fr"],
    "default_voice": "es-female-1"
  },
  "security": {
    "jwt_secret": "${JWT_SECRET}",
    "cors_origins": ["https://yourdomain.com"],
    "rate_limits": {
      "synthesize": "100/minute",
      "websocket": "1000/minute"
    }
  },
  "monitoring": {
    "metrics_enabled": true,
    "prometheus_port": 9090,
    "health_check_interval": 30
  }
}
```

## 📈 Roadmap Técnico

### Versión 1.1
- [ ] Soporte para SSML (Speech Synthesis Markup Language)
- [ ] Cache distribuido con Redis Cluster
- [ ] Métricas avanzadas con Prometheus
- [ ] Soporte para múltiples motores TTS

### Versión 1.2
- [ ] Streaming adaptativo basado en ancho de banda
- [ ] Soporte para emociones en la voz
- [ ] API GraphQL
- [ ] Integración con Kubernetes

### Versión 2.0
- [ ] Machine Learning para optimización automática
- [ ] Soporte para voz neural personalizada
- [ ] Clustering automático
- [ ] Dashboard web completo

## 📞 Soporte Técnico

### Debugging
```bash
# Habilitar debug logging
export MIT_TTS_LOG_LEVEL=DEBUG

# Ejecutar con profiling
python3 -m cProfile -o profile.stats src/main.py

# Analizar memoria
python3 -m memory_profiler src/main.py
```

### Herramientas de Desarrollo
```bash
# Linting
flake8 src/
black src/
isort src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

---

**Documentación Técnica v1.0**  
**Autor:** Beler Nolasco Almonte  
**Última actualización:** 2024-01-01