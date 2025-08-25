"""
WebSocket Server for MIT-TTS-Streamer

Servidor WebSocket para streaming de audio TTS en tiempo real con soporte para:
- Interrupciones inmediatas (<10ms)
- Streaming de audio por chunks
- Gestión de sesiones múltiples
- Sistema de colas con prioridades
- Control de latencia ultra-baja
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Dict, Any, Optional, Set, List
from dataclasses import dataclass
from enum import Enum

try:
    import websockets
    from websockets.server import WebSocketServerProtocol, serve
    from websockets.exceptions import ConnectionClosed, WebSocketException
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = Any
    serve = None
    ConnectionClosed = Exception
    WebSocketException = Exception

from ..core.session_manager import SessionManager, Session
from ..core.queue_manager import PriorityQueueManager, TaskPriority
from ..core.config_manager import ConfigManager
from ..tts.engine_manager import TTSEngineManager
from ..tts.base_engine import SynthesisConfig, AudioFormat

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Tipos de mensajes WebSocket"""
    # Cliente -> Servidor
    SYNTHESIZE = "synthesize"
    INTERRUPT = "interrupt"
    CONFIG_UPDATE = "config_update"
    PING = "ping"
    
    # Servidor -> Cliente
    AUDIO_CHUNK = "audio_chunk"
    SYNTHESIS_START = "synthesis_start"
    SYNTHESIS_COMPLETE = "synthesis_complete"
    SYNTHESIS_ERROR = "synthesis_error"
    INTERRUPTED = "interrupted"
    CONFIG_UPDATED = "config_updated"
    PONG = "pong"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """Mensaje WebSocket estructurado"""
    type: MessageType
    data: Dict[str, Any]
    session_id: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        """Convertir a JSON"""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "session_id": self.session_id,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Crear desde JSON"""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            data=data.get("data", {}),
            session_id=data.get("session_id"),
            timestamp=data.get("timestamp", time.time())
        )


class WebSocketMetrics:
    """Métricas del servidor WebSocket"""
    
    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.total_messages_received = 0
        self.total_messages_sent = 0
        self.total_audio_chunks_sent = 0
        self.total_interruptions = 0
        self.total_errors = 0
        self.connection_durations = []
        
        # Métricas de latencia
        self.synthesis_latencies = []
        self.interrupt_latencies = []
        
    def record_connection(self):
        """Registrar nueva conexión"""
        self.total_connections += 1
        self.active_connections += 1
    
    def record_disconnection(self, duration: float):
        """Registrar desconexión"""
        self.active_connections = max(0, self.active_connections - 1)
        self.connection_durations.append(duration)
        
        # Mantener solo las últimas 1000 duraciones
        if len(self.connection_durations) > 1000:
            self.connection_durations = self.connection_durations[-1000:]
    
    def record_message_received(self):
        """Registrar mensaje recibido"""
        self.total_messages_received += 1
    
    def record_message_sent(self):
        """Registrar mensaje enviado"""
        self.total_messages_sent += 1
    
    def record_audio_chunk_sent(self):
        """Registrar chunk de audio enviado"""
        self.total_audio_chunks_sent += 1
    
    def record_interruption(self, latency: float):
        """Registrar interrupción"""
        self.total_interruptions += 1
        self.interrupt_latencies.append(latency)
        
        # Mantener solo las últimas 1000 latencias
        if len(self.interrupt_latencies) > 1000:
            self.interrupt_latencies = self.interrupt_latencies[-1000:]
    
    def record_synthesis_latency(self, latency: float):
        """Registrar latencia de síntesis"""
        self.synthesis_latencies.append(latency)
        
        # Mantener solo las últimas 1000 latencias
        if len(self.synthesis_latencies) > 1000:
            self.synthesis_latencies = self.synthesis_latencies[-1000:]
    
    def record_error(self):
        """Registrar error"""
        self.total_errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        avg_connection_duration = (
            sum(self.connection_durations) / len(self.connection_durations)
            if self.connection_durations else 0.0
        )
        
        avg_synthesis_latency = (
            sum(self.synthesis_latencies) / len(self.synthesis_latencies)
            if self.synthesis_latencies else 0.0
        )
        
        avg_interrupt_latency = (
            sum(self.interrupt_latencies) / len(self.interrupt_latencies)
            if self.interrupt_latencies else 0.0
        )
        
        return {
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "total_messages_received": self.total_messages_received,
            "total_messages_sent": self.total_messages_sent,
            "total_audio_chunks_sent": self.total_audio_chunks_sent,
            "total_interruptions": self.total_interruptions,
            "total_errors": self.total_errors,
            "average_connection_duration_seconds": avg_connection_duration,
            "average_synthesis_latency_ms": avg_synthesis_latency * 1000,
            "average_interrupt_latency_ms": avg_interrupt_latency * 1000
        }


class WebSocketServer:
    """
    Servidor WebSocket para MIT-TTS-Streamer
    
    Características:
    - Streaming de audio en tiempo real
    - Interrupciones inmediatas (<10ms)
    - Gestión de sesiones múltiples
    - Sistema de colas con prioridades
    - Métricas de rendimiento
    - Manejo robusto de errores
    """
    
    def __init__(self, config_manager: ConfigManager, tts_engine_manager: Optional[TTSEngineManager] = None):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library is required for WebSocket server")
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Componentes principales
        self.session_manager = SessionManager(
            timeout=self.config.websocket.session_timeout,
            cleanup_interval=60,
            max_sessions_per_ip=self.config.websocket.max_connections_per_ip
        )
        self.queue_manager = PriorityQueueManager(
            max_queue_size=self.config.websocket.max_queue_size
        )
        
        # Motor TTS
        self.tts_engine_manager = tts_engine_manager
        if not self.tts_engine_manager:
            # Crear motor TTS si no se proporciona
            try:
                self.tts_engine_manager = TTSEngineManager(self.config.tts)
                logger.info("TTS Engine Manager created for WebSocket server")
            except Exception as e:
                logger.warning(f"Failed to create TTS Engine Manager: {e}")
                self.tts_engine_manager = None
        
        # Estado del servidor
        self.server = None
        self.is_running = False
        self.metrics = WebSocketMetrics()
        
        # Conexiones activas
        self.active_connections: Dict[str, WebSocketServerProtocol] = {}
        self.connection_sessions: Dict[WebSocketServerProtocol, str] = {}
        
        logger.info(f"WebSocketServer initialized on port {self.config.websocket.port}")
    
    async def start(self):
        """Iniciar el servidor WebSocket"""
        if self.is_running:
            logger.warning("WebSocket server is already running")
            return
        
        try:
            # Iniciar componentes
            await self.session_manager.start()
            await self.queue_manager.start()
            
            # Inicializar motor TTS si está disponible
            if self.tts_engine_manager:
                success = await self.tts_engine_manager.initialize()
                if success:
                    logger.info("TTS Engine Manager initialized successfully")
                else:
                    logger.warning("TTS Engine Manager initialization failed - using mock synthesis")
            else:
                logger.warning("No TTS Engine Manager available - using mock synthesis")
            
            # Iniciar servidor WebSocket
            self.server = await serve(
                self._handle_connection,
                self.config.websocket.host,
                self.config.websocket.port,
                ping_interval=self.config.websocket.ping_interval,
                ping_timeout=self.config.websocket.ping_timeout,
                max_size=self.config.websocket.max_message_size,
                compression=None  # Desactivar compresión para baja latencia
            )
            
            self.is_running = True
            logger.info(f"WebSocket server started on {self.config.websocket.host}:{self.config.websocket.port}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise
    
    async def stop(self):
        """Detener el servidor WebSocket"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        try:
            # Cerrar servidor
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            # Detener componentes
            await self.session_manager.stop()
            await self.queue_manager.stop()
            
            # Limpiar motor TTS
            if self.tts_engine_manager:
                await self.tts_engine_manager.cleanup()
            
            logger.info("WebSocket server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket server: {e}")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """
        Manejar nueva conexión WebSocket
        
        Args:
            websocket: Conexión WebSocket
            path: Ruta de la conexión
        """
        connection_start = time.time()
        session_id = None
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        try:
            # Registrar conexión
            self.metrics.record_connection()
            
            # Crear sesión
            session_id = await self.session_manager.create_session(
                websocket=websocket,
                client_ip=client_ip,
                user_agent=websocket.request_headers.get("User-Agent")
            )
            
            # Registrar conexión activa
            self.active_connections[session_id] = websocket
            self.connection_sessions[websocket] = session_id
            
            logger.info(f"WebSocket connection established: {session_id} from {client_ip}")
            
            # Enviar mensaje de bienvenida
            welcome_msg = WebSocketMessage(
                type=MessageType.CONFIG_UPDATED,
                data={"message": "Connection established", "session_id": session_id},
                session_id=session_id
            )
            await self._send_message(websocket, welcome_msg)
            
            # Manejar mensajes
            async for message in websocket:
                await self._handle_message(websocket, message, session_id)
                
        except ConnectionClosed:
            logger.info(f"WebSocket connection closed: {session_id}")
        except WebSocketException as e:
            logger.warning(f"WebSocket error for session {session_id}: {e}")
            self.metrics.record_error()
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket connection {session_id}: {e}")
            logger.error(traceback.format_exc())
            self.metrics.record_error()
        finally:
            # Limpiar conexión
            await self._cleanup_connection(websocket, session_id, connection_start)
    
    async def _handle_message(self, websocket: WebSocketServerProtocol,
                            raw_message: str, session_id: str):
        """
        Manejar mensaje recibido
        
        Args:
            websocket: Conexión WebSocket
            raw_message: Mensaje crudo
            session_id: ID de la sesión
        """
        try:
            self.metrics.record_message_received()
            
            # Parsear mensaje
            message = WebSocketMessage.from_json(raw_message)
            message.session_id = session_id
            
            # Procesar según tipo
            if message.type == MessageType.SYNTHESIZE:
                await self._handle_synthesize(websocket, message)
            elif message.type == MessageType.INTERRUPT:
                await self._handle_interrupt(websocket, message)
            elif message.type == MessageType.CONFIG_UPDATE:
                await self._handle_config_update(websocket, message)
            elif message.type == MessageType.PING:
                await self._handle_ping(websocket, message)
            else:
                logger.warning(f"Unknown message type: {message.type}")
                await self._send_error(websocket, f"Unknown message type: {message.type}")
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON message from {session_id}: {e}")
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message from {session_id}: {e}")
            await self._send_error(websocket, f"Message processing error: {str(e)}")
    
    async def _handle_synthesize(self, websocket: WebSocketServerProtocol,
                               message: WebSocketMessage):
        """
        Manejar solicitud de síntesis
        
        Args:
            websocket: Conexión WebSocket
            message: Mensaje de síntesis
        """
        try:
            text = message.data.get("text", "").strip()
            if not text:
                await self._send_error(websocket, "Text is required for synthesis")
                return
            
            priority = TaskPriority(message.data.get("priority", "normal"))
            
            # Obtener sesión
            session = await self.session_manager.get_session(message.session_id)
            if not session:
                await self._send_error(websocket, "Session not found")
                return
            
            # Crear tarea de síntesis
            synthesis_start = time.time()
            
            # Enviar confirmación de inicio
            start_msg = WebSocketMessage(
                type=MessageType.SYNTHESIS_START,
                data={"text": text, "priority": priority.value},
                session_id=message.session_id
            )
            await self._send_message(websocket, start_msg)
            
            # Agregar a cola de prioridad
            task_data = {
                "text": text,
                "session_id": message.session_id,
                "websocket": websocket,
                "config": session.config.to_dict(),
                "start_time": synthesis_start
            }
            
            task_id = await self.queue_manager.add_task(
                task_data, priority, f"synthesize_{message.session_id}"
            )
            
            # Procesar tarea (simulado por ahora)
            await self._process_synthesis_task(task_id, task_data)
            
        except Exception as e:
            logger.error(f"Error in synthesis request: {e}")
            await self._send_error(websocket, f"Synthesis error: {str(e)}")
    
    async def _handle_interrupt(self, websocket: WebSocketServerProtocol,
                              message: WebSocketMessage):
        """
        Manejar solicitud de interrupción
        
        Args:
            websocket: Conexión WebSocket
            message: Mensaje de interrupción
        """
        try:
            interrupt_start = time.time()
            
            # Interrumpir tareas de la sesión
            interrupted_count = await self.queue_manager.interrupt_tasks(
                f"synthesize_{message.session_id}"
            )
            
            interrupt_latency = time.time() - interrupt_start
            self.metrics.record_interruption(interrupt_latency)
            
            # Enviar confirmación
            interrupt_msg = WebSocketMessage(
                type=MessageType.INTERRUPTED,
                data={
                    "interrupted_tasks": interrupted_count,
                    "latency_ms": interrupt_latency * 1000
                },
                session_id=message.session_id
            )
            await self._send_message(websocket, interrupt_msg)
            
            logger.debug(f"Interrupted {interrupted_count} tasks for session {message.session_id} "
                        f"in {interrupt_latency*1000:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error in interrupt request: {e}")
            await self._send_error(websocket, f"Interrupt error: {str(e)}")
    
    async def _handle_config_update(self, websocket: WebSocketServerProtocol,
                                  message: WebSocketMessage):
        """
        Manejar actualización de configuración
        
        Args:
            websocket: Conexión WebSocket
            message: Mensaje de configuración
        """
        try:
            config_data = message.data.get("config", {})
            
            # Actualizar configuración de sesión
            success = await self.session_manager.update_session_config(
                message.session_id, config_data
            )
            
            if success:
                # Enviar confirmación
                config_msg = WebSocketMessage(
                    type=MessageType.CONFIG_UPDATED,
                    data={"config": config_data, "status": "updated"},
                    session_id=message.session_id
                )
                await self._send_message(websocket, config_msg)
            else:
                await self._send_error(websocket, "Failed to update session config")
                
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            await self._send_error(websocket, f"Config update error: {str(e)}")
    
    async def _handle_ping(self, websocket: WebSocketServerProtocol,
                         message: WebSocketMessage):
        """
        Manejar ping
        
        Args:
            websocket: Conexión WebSocket
            message: Mensaje de ping
        """
        pong_msg = WebSocketMessage(
            type=MessageType.PONG,
            data={"timestamp": message.timestamp},
            session_id=message.session_id
        )
        await self._send_message(websocket, pong_msg)
    
    async def _process_synthesis_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Procesar tarea de síntesis con motor TTS real
        
        Args:
            task_id: ID de la tarea
            task_data: Datos de la tarea
        """
        try:
            websocket = task_data["websocket"]
            session_id = task_data["session_id"]
            text = task_data["text"]
            start_time = task_data["start_time"]
            config = task_data["config"]
            
            # Verificar si tenemos motor TTS disponible
            if not self.tts_engine_manager or not self.tts_engine_manager.is_initialized:
                # Fallback a síntesis simulada
                await self._process_mock_synthesis(task_id, task_data)
                return
            
            try:
                # Crear configuración de síntesis
                synthesis_config = SynthesisConfig(
                    voice_id=config.get("voice_id", "es-0"),
                    language=config.get("language", "es"),
                    speed=config.get("speed", 1.0),
                    pitch=config.get("pitch", 1.0),
                    volume=config.get("volume", 1.0),
                    format=AudioFormat(config.get("format", "wav")),
                    sample_rate=config.get("sample_rate", 22050),
                    chunk_size=config.get("chunk_size", 1024)
                )
                
                # Realizar síntesis con streaming
                chunk_count = 0
                total_audio_bytes = 0
                
                async for audio_chunk in self.tts_engine_manager.synthesize_streaming(text, synthesis_config):
                    # Verificar si la tarea fue interrumpida
                    if await self.queue_manager.is_task_cancelled(task_id):
                        logger.debug(f"Task {task_id} was cancelled during synthesis")
                        return
                    
                    # Enviar chunk de audio
                    chunk_msg = WebSocketMessage(
                        type=MessageType.AUDIO_CHUNK,
                        data=audio_chunk.to_dict(),
                        session_id=session_id
                    )
                    await self._send_message(websocket, chunk_msg)
                    self.metrics.record_audio_chunk_sent()
                    
                    chunk_count += 1
                    total_audio_bytes += len(audio_chunk.data)
                
                # Enviar mensaje de completado
                synthesis_time = time.time() - start_time
                self.metrics.record_synthesis_latency(synthesis_time)
                
                complete_msg = WebSocketMessage(
                    type=MessageType.SYNTHESIS_COMPLETE,
                    data={
                        "text": text,
                        "total_chunks": chunk_count,
                        "synthesis_time_ms": synthesis_time * 1000,
                        "audio_bytes": total_audio_bytes,
                        "engine": "real_tts"
                    },
                    session_id=session_id
                )
                await self._send_message(websocket, complete_msg)
                
                # Registrar actividad en sesión
                await self.session_manager.record_session_activity(
                    session_id,
                    total_audio_bytes,
                    synthesis_time
                )
                
                # Marcar tarea como completada
                await self.queue_manager.complete_task(task_id)
                
            except Exception as tts_error:
                logger.error(f"TTS synthesis failed for task {task_id}: {tts_error}")
                # Fallback a síntesis simulada
                await self._process_mock_synthesis(task_id, task_data)
            
        except Exception as e:
            logger.error(f"Error processing synthesis task {task_id}: {e}")
            
            # Enviar error al cliente
            error_msg = WebSocketMessage(
                type=MessageType.SYNTHESIS_ERROR,
                data={"error": str(e), "task_id": task_id},
                session_id=task_data["session_id"]
            )
            await self._send_message(task_data["websocket"], error_msg)
    
    async def _process_mock_synthesis(self, task_id: str, task_data: Dict[str, Any]):
        """
        Procesar síntesis simulada como fallback
        
        Args:
            task_id: ID de la tarea
            task_data: Datos de la tarea
        """
        try:
            websocket = task_data["websocket"]
            session_id = task_data["session_id"]
            text = task_data["text"]
            start_time = task_data["start_time"]
            config = task_data["config"]
            
            logger.debug(f"Using mock synthesis for task {task_id}")
            
            # Simular procesamiento
            await asyncio.sleep(0.1)
            
            # Simular chunks de audio
            mock_chunks = [
                b"mock_audio_chunk_1_" + text[:20].encode('utf-8'),
                b"mock_audio_chunk_2_" + text[20:40].encode('utf-8'),
                b"mock_audio_chunk_3_" + text[40:60].encode('utf-8')
            ]
            
            # Enviar chunks de audio
            for i, chunk_data in enumerate(mock_chunks):
                # Verificar si la tarea fue interrumpida
                if await self.queue_manager.is_task_cancelled(task_id):
                    logger.debug(f"Mock task {task_id} was cancelled")
                    return
                
                # Enviar chunk
                chunk_msg = WebSocketMessage(
                    type=MessageType.AUDIO_CHUNK,
                    data={
                        "data": chunk_data.hex(),
                        "index": i,
                        "total_chunks": len(mock_chunks),
                        "format": config.get("format", "wav"),
                        "sample_rate": config.get("sample_rate", 22050),
                        "duration_ms": 200.0,
                        "size_bytes": len(chunk_data)
                    },
                    session_id=session_id
                )
                await self._send_message(websocket, chunk_msg)
                self.metrics.record_audio_chunk_sent()
                
                # Pequeña pausa entre chunks
                await asyncio.sleep(0.05)
            
            # Enviar mensaje de completado
            synthesis_time = time.time() - start_time
            self.metrics.record_synthesis_latency(synthesis_time)
            
            complete_msg = WebSocketMessage(
                type=MessageType.SYNTHESIS_COMPLETE,
                data={
                    "text": text,
                    "total_chunks": len(mock_chunks),
                    "synthesis_time_ms": synthesis_time * 1000,
                    "audio_bytes": sum(len(chunk) for chunk in mock_chunks),
                    "engine": "mock_tts"
                },
                session_id=session_id
            )
            await self._send_message(websocket, complete_msg)
            
            # Registrar actividad en sesión
            await self.session_manager.record_session_activity(
                session_id,
                sum(len(chunk) for chunk in mock_chunks),
                synthesis_time
            )
            
            # Marcar tarea como completada
            await self.queue_manager.complete_task(task_id)
            
        except Exception as e:
            logger.error(f"Error in mock synthesis for task {task_id}: {e}")
            raise
    
    async def _send_message(self, websocket: WebSocketServerProtocol,
                          message: WebSocketMessage):
        """
        Enviar mensaje por WebSocket
        
        Args:
            websocket: Conexión WebSocket
            message: Mensaje a enviar
        """
        try:
            await websocket.send(message.to_json())
            self.metrics.record_message_sent()
        except ConnectionClosed:
            logger.debug("Connection closed while sending message")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.metrics.record_error()
    
    async def _send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """
        Enviar mensaje de error
        
        Args:
            websocket: Conexión WebSocket
            error_message: Mensaje de error
        """
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": error_message}
        )
        await self._send_message(websocket, error_msg)
    
    async def _cleanup_connection(self, websocket: WebSocketServerProtocol,
                                session_id: Optional[str], connection_start: float):
        """
        Limpiar conexión cerrada
        
        Args:
            websocket: Conexión WebSocket
            session_id: ID de la sesión
            connection_start: Tiempo de inicio de conexión
        """
        try:
            # Calcular duración de conexión
            connection_duration = time.time() - connection_start
            self.metrics.record_disconnection(connection_duration)
            
            # Remover de conexiones activas
            if session_id and session_id in self.active_connections:
                del self.active_connections[session_id]
            
            if websocket in self.connection_sessions:
                del self.connection_sessions[websocket]
            
            # Cerrar sesión
            if session_id:
                await self.session_manager.close_session(session_id, "connection_closed")
                
                # Interrumpir tareas pendientes
                await self.queue_manager.interrupt_tasks(f"synthesize_{session_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up connection: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del servidor WebSocket"""
        return {
            "is_running": self.is_running,
            "active_connections": len(self.active_connections),
            "host": self.config.websocket.host,
            "port": self.config.websocket.port,
            "session_manager": self.session_manager.get_status(),
            "queue_manager": self.queue_manager.get_status(),
            "metrics": self.metrics.get_stats()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del servidor"""
        return {
            "websocket": self.metrics.get_stats(),
            "sessions": self.session_manager.get_metrics(),
            "queue": self.queue_manager.get_metrics()
        }
    
    async def broadcast_message(self, message: WebSocketMessage,
                              exclude_sessions: Optional[Set[str]] = None):
        """
        Enviar mensaje a todas las conexiones activas
        
        Args:
            message: Mensaje a enviar
            exclude_sessions: Sesiones a excluir
        """
        exclude_sessions = exclude_sessions or set()
        
        for session_id, websocket in self.active_connections.items():
            if session_id not in exclude_sessions:
                await self._send_message(websocket, message)
        
        