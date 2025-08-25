"""
HTTP REST Server for MIT-TTS-Streamer

Servidor HTTP REST para configuración y control del sistema TTS.
Proporciona endpoints para gestión de configuración, estado del sistema,
y control de sesiones.

Autor: Beler Nolasco Almonte
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Depends, status, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Fallbacks simples
    class BaseModel:
        pass
    class FastAPI:
        def __init__(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)

# Modelos de datos para la API
class HealthResponse(BaseModel):
    """Respuesta del endpoint de salud"""
    status: str = "healthy"
    timestamp: str
    version: str = "0.1.0"
    uptime_seconds: float
    components: Dict[str, str]

class ConfigUpdateRequest(BaseModel):
    """Solicitud de actualización de configuración"""
    server: Optional[Dict[str, Any]] = None
    tts: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None

class SessionCreateRequest(BaseModel):
    """Solicitud de creación de sesión"""
    language: str = "es"
    voice_id: int = 0
    format: str = "wav"
    sample_rate: int = 22050
    speed: float = 1.0

class SessionResponse(BaseModel):
    """Respuesta de información de sesión"""
    session_id: str
    created_at: str
    last_activity: str
    config: Dict[str, Any]
    is_active: bool

class VoiceInfo(BaseModel):
    """Información de una voz"""
    id: int
    name: str
    gender: str
    description: str
    sample_rate: int
    quality: str

class LanguageInfo(BaseModel):
    """Información de un idioma"""
    code: str
    name: str
    speakers: List[VoiceInfo]

class MetricsResponse(BaseModel):
    """Respuesta de métricas del sistema"""
    timestamp: str
    uptime_seconds: float
    active_sessions: int
    total_requests: int
    average_latency_ms: float
    queue_size: int
    memory_usage_mb: float
    cpu_usage_percent: float

class StatusResponse(BaseModel):
    """Respuesta de estado del sistema"""
    status: str
    timestamp: str
    server: Dict[str, Any]
    tts_engine: Dict[str, Any]
    audio_processor: Dict[str, Any]
    active_connections: int
    queue_status: Dict[str, Any]


class HTTPServer:
    """Servidor HTTP REST para MIT-TTS-Streamer"""
    
    def __init__(self, config_manager, session_manager=None, queue_manager=None, tts_engine=None):
        self.config_manager = config_manager
        self.session_manager = session_manager
        self.queue_manager = queue_manager
        self.tts_engine = tts_engine
        self.config = config_manager.get_config()
        
        # Métricas del servidor
        self.start_time = time.time()
        self.request_count = 0
        self.total_latency = 0.0
        
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, HTTP server will be limited")
            self.app = None
            return
        
        # Crear aplicación FastAPI
        self.app = FastAPI(
            title="MIT-TTS-Streamer API",
            description="API REST para servidor TTS streaming de baja latencia - Desarrollado por Beler Nolasco Almonte",
            version="0.1.0",
            docs_url="/docs",
            redoc_url="/redoc",
            contact={
                "name": "Beler Nolasco Almonte",
                "email": "beler.nolasco@example.com",
            },
            license_info={
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT",
            },
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.server.cors_origins,
            allow_credentials=True,
            allow_methods=self.config.server.cors_methods,
            allow_headers=self.config.server.cors_headers,
        )
        
        # Middleware para métricas
        self.app.middleware("http")(self.metrics_middleware)
        
        # Registrar rutas
        self._register_routes()
    
    async def metrics_middleware(self, request: Request, call_next):
        """Middleware para recopilar métricas de requests"""
        start_time = time.time()
        
        response = await call_next(request)
        
        # Actualizar métricas
        process_time = time.time() - start_time
        self.request_count += 1
        self.total_latency += process_time * 1000  # en ms
        
        # Agregar headers de timing
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(self.request_count)
        
        return response
    
    def _register_routes(self):
        """Registrar todas las rutas de la API"""
        
        # Rutas de salud y estado
        @self.app.get("/api/v1/health", response_model=HealthResponse)
        async def health_check():
            """Endpoint de verificación de salud del sistema"""
            uptime = time.time() - self.start_time
            
            # Verificar estado de componentes
            components = {
                "config_manager": "healthy",
                "session_manager": "healthy" if self.session_manager else "not_initialized",
                "queue_manager": "healthy" if self.queue_manager else "not_initialized",
                "tts_engine": "healthy" if self.tts_engine else "not_initialized"
            }
            
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now().isoformat(),
                uptime_seconds=uptime,
                components=components
            )
        
        @self.app.get("/api/v1/status", response_model=StatusResponse)
        async def get_status():
            """Obtener estado detallado del sistema"""
            uptime = time.time() - self.start_time
            
            # Estado del servidor
            server_status = {
                "uptime_seconds": uptime,
                "host": self.config.server.host,
                "http_port": self.config.server.http_port,
                "websocket_port": self.config.server.websocket_port,
                "max_connections": self.config.server.max_connections
            }
            
            # Estado del motor TTS
            tts_status = {
                "engine": self.config.tts.engine,
                "device": self.config.tts.device,
                "default_language": self.config.tts.default_language,
                "supported_languages": self.config.tts.supported_languages,
                "preload_languages": self.config.tts.preload_languages
            }
            
            # Estado del procesador de audio
            audio_status = {
                "default_format": self.config.audio.default_format,
                "supported_formats": self.config.audio.supported_formats,
                "buffer_size": self.config.audio.buffer_size
            }
            
            # Estado de la cola
            queue_status = {
                "max_size": self.config.performance.max_queue_size,
                "current_size": 0,  # TODO: obtener del queue_manager real
                "worker_processes": self.config.performance.worker_processes
            }
            
            return StatusResponse(
                status="running",
                timestamp=datetime.now().isoformat(),
                server=server_status,
                tts_engine=tts_status,
                audio_processor=audio_status,
                active_connections=0,  # TODO: obtener número real
                queue_status=queue_status
            )
        
        @self.app.get("/api/v1/metrics", response_model=MetricsResponse)
        async def get_metrics():
            """Obtener métricas de rendimiento del sistema"""
            uptime = time.time() - self.start_time
            avg_latency = (self.total_latency / self.request_count) if self.request_count > 0 else 0.0
            
            # TODO: Obtener métricas reales del sistema
            import psutil
            memory_usage = psutil.virtual_memory().used / (1024 * 1024)  # MB
            cpu_usage = psutil.cpu_percent()
            
            return MetricsResponse(
                timestamp=datetime.now().isoformat(),
                uptime_seconds=uptime,
                active_sessions=0,  # TODO: obtener del session_manager
                total_requests=self.request_count,
                average_latency_ms=avg_latency,
                queue_size=0,  # TODO: obtener del queue_manager
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage
            )
        
        # Rutas de configuración
        @self.app.get("/api/v1/config")
        async def get_config():
            """Obtener configuración actual del sistema"""
            return self.config.dict()
        
        @self.app.post("/api/v1/config")
        async def update_config(request: ConfigUpdateRequest):
            """Actualizar configuración del sistema"""
            try:
                # Convertir request a dict
                updates = {}
                if request.server:
                    updates["server"] = request.server
                if request.tts:
                    updates["tts"] = request.tts
                if request.audio:
                    updates["audio"] = request.audio
                if request.logging:
                    updates["logging"] = request.logging
                
                # Actualizar configuración
                self.config_manager.update_config(updates)
                self.config = self.config_manager.get_config()
                
                return {"status": "success", "message": "Configuration updated successfully"}
                
            except Exception as e:
                logger.error(f"Error updating configuration: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error updating configuration: {str(e)}"
                )
        
        @self.app.post("/api/v1/config/reload")
        async def reload_config():
            """Recargar configuración desde archivo"""
            try:
                self.config_manager.reload_config()
                self.config = self.config_manager.get_config()
                return {"status": "success", "message": "Configuration reloaded successfully"}
            except Exception as e:
                logger.error(f"Error reloading configuration: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error reloading configuration: {str(e)}"
                )
        
        @self.app.post("/api/v1/config/save")
        async def save_config():
            """Guardar configuración actual a archivo"""
            try:
                self.config_manager.save_config()
                return {"status": "success", "message": "Configuration saved successfully"}
            except Exception as e:
                logger.error(f"Error saving configuration: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving configuration: {str(e)}"
                )
        
        # Rutas de voces e idiomas
        @self.app.get("/api/v1/voices", response_model=List[LanguageInfo])
        async def get_voices():
            """Obtener lista de voces disponibles por idioma"""
            voices_config = self.config_manager.get_voices_config()
            
            languages = []
            for lang_code, lang_data in voices_config.get("voices", {}).items():
                speakers = []
                for speaker in lang_data.get("speakers", []):
                    speakers.append(VoiceInfo(
                        id=speaker.get("id", 0),
                        name=speaker.get("name", "Unknown"),
                        gender=speaker.get("gender", "unknown"),
                        description=speaker.get("description", ""),
                        sample_rate=speaker.get("sample_rate", 22050),
                        quality=speaker.get("quality", "medium")
                    ))
                
                languages.append(LanguageInfo(
                    code=lang_code,
                    name=lang_data.get("name", lang_code),
                    speakers=speakers
                ))
            
            return languages
        
        @self.app.get("/api/v1/languages")
        async def get_languages():
            """Obtener lista de idiomas soportados"""
            return {
                "supported_languages": self.config.tts.supported_languages,
                "preload_languages": self.config.tts.preload_languages,
                "default_language": self.config.tts.default_language
            }
        
        # Rutas de sesiones (placeholder - se implementarán cuando tengamos SessionManager)
        @self.app.post("/api/v1/sessions", response_model=SessionResponse)
        async def create_session(request: SessionCreateRequest):
            """Crear nueva sesión TTS"""
            # TODO: Implementar cuando tengamos SessionManager
            session_id = f"session_{int(time.time())}"
            
            return SessionResponse(
                session_id=session_id,
                created_at=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat(),
                config=request.dict(),
                is_active=True
            )
        
        @self.app.get("/api/v1/sessions/{session_id}", response_model=SessionResponse)
        async def get_session(session_id: str):
            """Obtener información de una sesión específica"""
            # TODO: Implementar cuando tengamos SessionManager
            return SessionResponse(
                session_id=session_id,
                created_at=datetime.now().isoformat(),
                last_activity=datetime.now().isoformat(),
                config={"language": "es", "voice_id": 0},
                is_active=True
            )
        
        @self.app.delete("/api/v1/sessions/{session_id}")
        async def delete_session(session_id: str):
            """Cerrar una sesión específica"""
            # TODO: Implementar cuando tengamos SessionManager
            return {"status": "success", "message": f"Session {session_id} closed"}
        
        @self.app.get("/api/v1/sessions")
        async def list_sessions():
            """Listar todas las sesiones activas"""
            # TODO: Implementar cuando tengamos SessionManager
            return {"sessions": [], "total": 0}
        
        # Rutas de control
        @self.app.post("/api/v1/interrupt/{session_id}")
        async def interrupt_session(session_id: str):
            """Interrumpir síntesis en una sesión específica"""
            # TODO: Implementar cuando tengamos QueueManager
            return {"status": "success", "message": f"Session {session_id} interrupted"}
        
        @self.app.post("/api/v1/interrupt/all")
        async def interrupt_all():
            """Interrumpir todas las síntesis activas"""
            # TODO: Implementar cuando tengamos QueueManager
            return {"status": "success", "message": "All sessions interrupted"}
        
        # Manejo de errores
        @self.app.exception_handler(404)
        async def not_found_handler(request: Request, exc):
            return JSONResponse(
                status_code=404,
                content={"error": "Endpoint not found", "path": str(request.url)}
            )
        
        @self.app.exception_handler(500)
        async def internal_error_handler(request: Request, exc):
            logger.error(f"Internal server error: {exc}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "message": str(exc)}
            )
    
    async def start(self):
        """Iniciar el servidor HTTP"""
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, HTTP server cannot start")
            return
        
        logger.info(f"HTTP server starting on {self.config.server.host}:{self.config.server.http_port}")
        # En un entorno real, aquí iniciaríamos uvicorn o similar
        # Por ahora, solo registramos que el servidor está "iniciado"
        logger.info("HTTP server started (FastAPI app ready)")
    
    async def stop(self):
        """Detener el servidor HTTP"""
        if not FASTAPI_AVAILABLE:
            return
        
        logger.info("HTTP server stopping...")
        # En un entorno real, aquí detendríamos uvicorn
        logger.info("HTTP server stopped")
    
    def get_status(self):
        """Obtener estado del servidor HTTP"""
        return {
            "status": "running" if FASTAPI_AVAILABLE else "unavailable",
            "fastapi_available": FASTAPI_AVAILABLE,
            "host": self.config.server.host,
            "port": self.config.server.http_port,
            "request_count": self.request_count,
            "uptime_seconds": time.time() - self.start_time
        }


def create_http_app(config_manager, session_manager=None, queue_manager=None, tts_engine=None, config=None):
    """
    Factory function para crear la aplicación HTTP
    
    Args:
        config_manager: Gestor de configuración
        session_manager: Gestor de sesiones (opcional)
        queue_manager: Gestor de colas (opcional)
        tts_engine: Motor TTS (opcional)
        config: Configuración del sistema (opcional)
    
    Returns:
        FastAPI app instance o None si FastAPI no está disponible
    """
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, cannot create HTTP server")
        return None
    
    server = HTTPServer(config_manager, session_manager, queue_manager, tts_engine)
    return server.app