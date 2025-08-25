# MIT-TTS-Streamer

🎤 **Servidor TTS streaming de baja latencia para sistemas conversacionales de voz en tiempo real**

**👨‍💻 Autor:** Beler Nolasco Almonte

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## 🚀 Características Principales

- **⚡ Latencia Ultra-Baja**: < 300ms desde texto hasta audio
- **🔄 Interrupciones Inmediatas**: Sistema de prioridades con cancelación < 10ms
- **📡 Streaming en Tiempo Real**: Audio chunked para respuesta inmediata
- **👥 Multi-Usuario**: Soporte concurrente para múltiples sesiones
- **🌍 Multi-Idioma**: Soporte extensible para diferentes idiomas
- **🎵 Multi-Formato**: WAV, MP3, OGG y más formatos de audio
- **🔌 API Dual**: WebSocket para streaming + HTTP REST para control

## 🏗️ Arquitectura

```
Cliente ←→ WebSocket Server ←→ Priority Queue ←→ TTS Engine ←→ Audio Processor
    ↕                                ↑
HTTP REST API                 Interrupciones
```

### Componentes Clave
- **WebSocket Server**: Streaming de audio en tiempo real
- **HTTP REST API**: Configuración y control del sistema
- **Priority Queue**: Gestión de prioridades (Critical, High, Normal)
- **TTS Engine**: Motor multi-idioma basado en MeloTTS
- **Session Manager**: Gestión de múltiples usuarios concurrentes

## 📦 Instalación

### Requisitos
- Python 3.8+
- PyTorch (CPU o CUDA)
- MeloTTS

### Instalación Rápida
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/mit-tts-streamer.git
cd mit-tts-streamer

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar
cp config/default.json config/local.json
# Editar config/local.json según tus necesidades

# Ejecutar servidor
python -m src.main
```

## 🚀 Uso Rápido

### Servidor
```bash
# Iniciar servidor (HTTP REST en 8080, WebSocket en 8081)
python -m src.main

# Con configuración personalizada
python -m src.main --config config/production.json
```

### Cliente Python
```python
import asyncio
from examples.client_example import TTSStreamingClient

async def demo():
    client = TTSStreamingClient("ws://localhost:8081")
    await client.connect()
    
    # Síntesis normal
    await client.synthesize_and_play("Hola mundo", priority="normal")
    
    # Interrupción crítica
    await client.synthesize_and_play("¡Alerta!", priority="critical")
    
    await client.close()

asyncio.run(demo())
```

### Cliente Web
Abre `examples/websocket_client.html` en tu navegador y conecta a `ws://localhost:8081`.

## 📡 API Reference

### WebSocket Protocol

#### Conectar
```json
{
  "type": "connect",
  "config": {
    "language": "es",
    "voice_id": 0,
    "format": "wav",
    "sample_rate": 22050
  }
}
```

#### Sintetizar
```json
{
  "type": "synthesize",
  "text": "Texto a sintetizar",
  "priority": "normal|high|critical",
  "config": {
    "speed": 1.0,
    "chunk_size": 1024
  }
}
```

#### Interrumpir
```json
{
  "type": "interrupt",
  "reason": "user_request"
}
```

### HTTP REST API

- `GET /api/v1/status` - Estado del servidor
- `GET /api/v1/voices` - Voces disponibles
- `POST /api/v1/sessions` - Crear sesión
- `POST /api/v1/interrupt/{session_id}` - Interrumpir sesión

## ⚙️ Configuración

### config/default.json
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
    "chunk_size": 1024
  },
  "performance": {
    "max_queue_size": 1000,
    "worker_processes": 4,
    "preload_models": true
  }
}
```

## 🎯 Casos de Uso

### 1. Asistente de Voz Conversacional
```python
# Integración con sistema de voz completo
assistant = VoiceAssistant(tts_url="ws://localhost:8081")
await assistant.start()  # Conversación natural con interrupciones
```

### 2. Sistema de Alertas por Voz
```python
# Alertas críticas que interrumpen cualquier síntesis
await tts_client.synthesize("Alerta de seguridad", priority="critical")
```

### 3. Aplicación de Accesibilidad
```python
# Lectura de texto con capacidad de interrupción
await tts_client.synthesize_streaming(long_text)
```

## 📊 Métricas de Rendimiento

### Objetivos
- **Primera respuesta**: < 100ms
- **Primer chunk de audio**: < 300ms
- **Tiempo de interrupción**: < 10ms
- **Usuarios concurrentes**: 50+

### Monitoreo
```bash
# Ver métricas en tiempo real
curl http://localhost:8080/api/v1/metrics

# Logs detallados
tail -f logs/mit-tts-streamer.log
```

## 🧪 Testing

```bash
# Tests unitarios
python -m pytest tests/unit/

# Tests de integración
python -m pytest tests/integration/

# Tests de rendimiento
python -m pytest tests/performance/

# Test de latencia
python examples/latency_test.py
```

## 🐳 Docker

```bash
# Construir imagen
docker build -t mit-tts-streamer .

# Ejecutar contenedor
docker run -p 8080:8080 -p 8081:8081 mit-tts-streamer

# Con volumen de configuración
docker run -v $(pwd)/config:/app/config -p 8080:8080 -p 8081:8081 mit-tts-streamer
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [MeloTTS](https://github.com/myshell-ai/MeloTTS) - Motor TTS base
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web
- [WebSockets](https://websockets.readthedocs.io/) - Comunicación en tiempo real

## 📞 Soporte

- 📧 Email: support@mit-tts-streamer.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/mit-tts-streamer/issues)
- 📖 Documentación: [Docs](https://mit-tts-streamer.readthedocs.io/)

---

**MIT-TTS-Streamer** - Haciendo la síntesis de voz más rápida y natural 🚀