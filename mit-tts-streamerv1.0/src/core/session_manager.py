"""
Session Manager for MIT-TTS-Streamer

Gestiona sesiones de usuarios múltiples con soporte para configuración
por sesión, timeout automático y limpieza de recursos.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Any, List
from datetime import datetime

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = Any

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """Configuración específica de una sesión"""
    language: str = "es"
    voice_id: int = 0
    format: str = "wav"
    sample_rate: int = 22050
    speed: float = 1.0
    chunk_size: int = 1024
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "voice_id": self.voice_id,
            "format": self.format,
            "sample_rate": self.sample_rate,
            "speed": self.speed,
            "chunk_size": self.chunk_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        return cls(
            language=data.get("language", "es"),
            voice_id=data.get("voice_id", 0),
            format=data.get("format", "wav"),
            sample_rate=data.get("sample_rate", 22050),
            speed=data.get("speed", 1.0),
            chunk_size=data.get("chunk_size", 1024)
        )


@dataclass
class Session:
    """Sesión de usuario TTS"""
    id: str
    websocket: Optional[WebSocketServerProtocol] = None
    config: SessionConfig = field(default_factory=SessionConfig)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Estadísticas de la sesión
    total_requests: int = 0
    total_audio_bytes: int = 0
    total_synthesis_time: float = 0.0
    
    def update_activity(self):
        """Actualizar timestamp de última actividad"""
        self.last_activity = time.time()
    
    def age_seconds(self) -> float:
        """Edad de la sesión en segundos"""
        return time.time() - self.created_at
    
    def idle_seconds(self) -> float:
        """Tiempo inactivo en segundos"""
        return time.time() - self.last_activity
    
    def record_request(self, audio_bytes: int = 0, synthesis_time: float = 0.0):
        """Registrar una solicitud de síntesis"""
        self.total_requests += 1
        self.total_audio_bytes += audio_bytes
        self.total_synthesis_time += synthesis_time
        self.update_activity()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la sesión"""
        avg_synthesis_time = (
            self.total_synthesis_time / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": self.total_requests,
            "total_audio_bytes": self.total_audio_bytes,
            "total_synthesis_time_ms": self.total_synthesis_time * 1000,
            "average_synthesis_time_ms": avg_synthesis_time * 1000,
            "age_seconds": self.age_seconds(),
            "idle_seconds": self.idle_seconds()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir sesión a diccionario"""
        return {
            "session_id": self.id,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "last_activity": datetime.fromtimestamp(self.last_activity).isoformat(),
            "is_active": self.is_active,
            "config": self.config.to_dict(),
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "stats": self.get_stats()
        }


class SessionMetrics:
    """Métricas del gestor de sesiones"""
    
    def __init__(self):
        self.total_sessions_created = 0
        self.total_sessions_closed = 0
        self.total_sessions_expired = 0
        self.peak_concurrent_sessions = 0
        self.session_durations = []
        
    def record_session_created(self):
        """Registrar sesión creada"""
        self.total_sessions_created += 1
    
    def record_session_closed(self, duration: float):
        """Registrar sesión cerrada"""
        self.total_sessions_closed += 1
        self.session_durations.append(duration)
        
        # Mantener solo las últimas 1000 duraciones
        if len(self.session_durations) > 1000:
            self.session_durations = self.session_durations[-1000:]
    
    def record_session_expired(self, duration: float):
        """Registrar sesión expirada"""
        self.total_sessions_expired += 1
        self.session_durations.append(duration)
    
    def update_peak_sessions(self, current_count: int):
        """Actualizar pico de sesiones concurrentes"""
        if current_count > self.peak_concurrent_sessions:
            self.peak_concurrent_sessions = current_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del gestor"""
        avg_duration = (
            sum(self.session_durations) / len(self.session_durations)
            if self.session_durations else 0.0
        )
        
        return {
            "total_created": self.total_sessions_created,
            "total_closed": self.total_sessions_closed,
            "total_expired": self.total_sessions_expired,
            "peak_concurrent": self.peak_concurrent_sessions,
            "average_duration_seconds": avg_duration,
            "active_sessions": self.total_sessions_created - self.total_sessions_closed - self.total_sessions_expired
        }


class SessionManager:
    """
    Gestor de sesiones para MIT-TTS-Streamer
    
    Características:
    - Gestión de múltiples sesiones concurrentes
    - Timeout automático de sesiones inactivas
    - Configuración por sesión
    - Métricas de uso
    - Limpieza automática de recursos
    - Límites por IP
    """
    
    def __init__(self, timeout: int = 300, cleanup_interval: int = 60, max_sessions_per_ip: int = 10):
        self.timeout = timeout  # Timeout de sesión en segundos
        self.cleanup_interval = cleanup_interval  # Intervalo de limpieza en segundos
        self.max_sessions_per_ip = max_sessions_per_ip
        
        # Almacenamiento de sesiones
        self.sessions: Dict[str, Session] = {}
        self.sessions_by_ip: Dict[str, Set[str]] = {}
        self.sessions_lock = asyncio.Lock()
        
        # Métricas
        self.metrics = SessionMetrics()
        
        # Control de estado
        self.is_running = True
        self.cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(f"SessionManager initialized - timeout: {timeout}s, cleanup_interval: {cleanup_interval}s")
    
    async def start(self):
        """Iniciar el gestor de sesiones"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            logger.info("SessionManager started")
    
    async def stop(self):
        """Detener el gestor de sesiones"""
        self.is_running = False
        
        # Cancelar tarea de limpieza
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cerrar todas las sesiones
        await self.cleanup_all_sessions()
        
        logger.info("SessionManager stopped")
    
    async def create_session(self, websocket: Optional[WebSocketServerProtocol] = None, 
                           config: Optional[Dict[str, Any]] = None,
                           client_ip: Optional[str] = None,
                           user_agent: Optional[str] = None) -> str:
        """
        Crear nueva sesión
        
        Args:
            websocket: Conexión WebSocket (opcional)
            config: Configuración de la sesión
            client_ip: IP del cliente
            user_agent: User agent del cliente
            
        Returns:
            ID de la sesión creada
            
        Raises:
            ValueError: Si se excede el límite de sesiones por IP
        """
        # Verificar límite por IP
        if client_ip and client_ip in self.sessions_by_ip:
            if len(self.sessions_by_ip[client_ip]) >= self.max_sessions_per_ip:
                raise ValueError(f"Maximum sessions per IP exceeded ({self.max_sessions_per_ip})")
        
        session_id = str(uuid.uuid4())
        session_config = SessionConfig.from_dict(config or {})
        
        session = Session(
            id=session_id,
            websocket=websocket,
            config=session_config,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        async with self.sessions_lock:
            self.sessions[session_id] = session
            
            # Actualizar índice por IP
            if client_ip:
                if client_ip not in self.sessions_by_ip:
                    self.sessions_by_ip[client_ip] = set()
                self.sessions_by_ip[client_ip].add(session_id)
            
            # Actualizar métricas
            self.metrics.record_session_created()
            self.metrics.update_peak_sessions(len(self.sessions))
        
        logger.info(f"Session created: {session_id} (IP: {client_ip}, total: {len(self.sessions)})")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Obtener sesión por ID
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Sesión o None si no existe
        """
        async with self.sessions_lock:
            session = self.sessions.get(session_id)
            if session and session.is_active:
                session.update_activity()
                return session
            return None
    
    async def update_session_config(self, session_id: str, config: Dict[str, Any]) -> bool:
        """
        Actualizar configuración de sesión
        
        Args:
            session_id: ID de la sesión
            config: Nueva configuración
            
        Returns:
            True si se actualizó exitosamente
        """
        session = await self.get_session(session_id)
        if session:
            session.config = SessionConfig.from_dict(config)
            logger.debug(f"Session config updated: {session_id}")
            return True
        return False
    
    async def close_session(self, session_id: str, reason: str = "user_request"):
        """
        Cerrar sesión específica
        
        Args:
            session_id: ID de la sesión
            reason: Razón del cierre
        """
        async with self.sessions_lock:
            session = self.sessions.get(session_id)
            if session:
                # Cerrar WebSocket si existe
                if session.websocket and WEBSOCKETS_AVAILABLE:
                    try:
                        await session.websocket.close()
                    except Exception as e:
                        logger.warning(f"Error closing WebSocket for session {session_id}: {e}")
                
                # Actualizar métricas
                duration = session.age_seconds()
                self.metrics.record_session_closed(duration)
                
                # Remover de índices
                if session.client_ip and session.client_ip in self.sessions_by_ip:
                    self.sessions_by_ip[session.client_ip].discard(session_id)
                    if not self.sessions_by_ip[session.client_ip]:
                        del self.sessions_by_ip[session.client_ip]
                
                # Remover sesión
                del self.sessions[session_id]
                
                logger.info(f"Session closed: {session_id} (reason: {reason}, duration: {duration:.1f}s)")
    
    async def list_sessions(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Listar sesiones
        
        Args:
            active_only: Solo sesiones activas
            
        Returns:
            Lista de información de sesiones
        """
        sessions_info = []
        
        async with self.sessions_lock:
            for session in self.sessions.values():
                if not active_only or session.is_active:
                    sessions_info.append(session.to_dict())
        
        return sessions_info
    
    async def get_sessions_by_ip(self, client_ip: str) -> List[str]:
        """
        Obtener sesiones por IP
        
        Args:
            client_ip: IP del cliente
            
        Returns:
            Lista de IDs de sesión
        """
        async with self.sessions_lock:
            return list(self.sessions_by_ip.get(client_ip, set()))
    
    async def record_session_activity(self, session_id: str, audio_bytes: int = 0, 
                                    synthesis_time: float = 0.0):
        """
        Registrar actividad de sesión
        
        Args:
            session_id: ID de la sesión
            audio_bytes: Bytes de audio generados
            synthesis_time: Tiempo de síntesis en segundos
        """
        session = await self.get_session(session_id)
        if session:
            session.record_request(audio_bytes, synthesis_time)
    
    async def cleanup_all_sessions(self):
        """Cerrar todas las sesiones"""
        async with self.sessions_lock:
            session_ids = list(self.sessions.keys())
        
        for session_id in session_ids:
            await self.close_session(session_id, "system_shutdown")
        
        logger.info(f"All sessions closed ({len(session_ids)} total)")
    
    async def _cleanup_expired_sessions(self):
        """Tarea de limpieza de sesiones expiradas"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                current_time = time.time()
                expired_sessions = []
                
                async with self.sessions_lock:
                    for session_id, session in self.sessions.items():
                        if (current_time - session.last_activity > self.timeout or
                            not session.is_active):
                            expired_sessions.append(session_id)
                
                # Cerrar sesiones expiradas
                for session_id in expired_sessions:
                    await self.close_session(session_id, "timeout")
                    self.metrics.record_session_expired(
                        self.sessions.get(session_id, Session("")).age_seconds()
                    )
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del gestor de sesiones"""
        active_sessions = len(self.sessions)
        sessions_by_ip_count = {ip: len(sessions) for ip, sessions in self.sessions_by_ip.items()}
        
        return {
            "is_running": self.is_running,
            "active_sessions": active_sessions,
            "timeout_seconds": self.timeout,
            "cleanup_interval_seconds": self.cleanup_interval,
            "max_sessions_per_ip": self.max_sessions_per_ip,
            "sessions_by_ip": sessions_by_ip_count,
            "metrics": self.metrics.get_stats()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del gestor"""
        return self.metrics.get_stats()
    
    async def get_session_count(self) -> int:
        """Obtener número de sesiones activas"""
        return len(self.sessions)