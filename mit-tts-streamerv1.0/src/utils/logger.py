"""
Logging utilities for MIT-TTS-Streamer

Sistema de logging avanzado con soporte para métricas de rendimiento,
logging estructurado y múltiples handlers.
"""

import logging
import logging.handlers
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger
from rich.console import Console
from rich.logging import RichHandler

console = Console()


class PerformanceLogger:
    """
    Logger especializado para métricas de rendimiento
    
    Registra métricas de latencia, throughput y otros indicadores
    de rendimiento críticos para el sistema TTS.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"performance.{name}")
        self.metrics = {}
    
    def log_latency(self, operation: str, duration_ms: float, session_id: str, **kwargs):
        """Registrar latencia de operación"""
        extra = {
            "metric_type": "latency",
            "operation": operation,
            "duration_ms": duration_ms,
            "session_id": session_id,
            **kwargs
        }
        
        self.logger.info(
            f"LATENCY: {operation} took {duration_ms:.2f}ms for session {session_id}",
            extra=extra
        )
        
        # Actualizar métricas en memoria
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration_ms)
    
    def log_throughput(self, operation: str, items_per_second: float, **kwargs):
        """Registrar throughput de operación"""
        extra = {
            "metric_type": "throughput",
            "operation": operation,
            "items_per_second": items_per_second,
            **kwargs
        }
        
        self.logger.info(
            f"THROUGHPUT: {operation} processed {items_per_second:.2f} items/sec",
            extra=extra
        )
    
    def log_queue_size(self, queue_name: str, size: int, max_size: int, **kwargs):
        """Registrar tamaño de cola"""
        extra = {
            "metric_type": "queue_size",
            "queue_name": queue_name,
            "size": size,
            "max_size": max_size,
            "utilization": size / max_size if max_size > 0 else 0,
            **kwargs
        }
        
        self.logger.info(
            f"QUEUE: {queue_name} size={size}/{max_size} ({size/max_size*100:.1f}%)",
            extra=extra
        )
    
    def log_interruption(self, session_id: str, reason: str, response_time_ms: float, **kwargs):
        """Registrar interrupción"""
        extra = {
            "metric_type": "interruption",
            "session_id": session_id,
            "reason": reason,
            "response_time_ms": response_time_ms,
            **kwargs
        }
        
        self.logger.warning(
            f"INTERRUPT: Session {session_id} interrupted ({reason}) - response: {response_time_ms:.2f}ms",
            extra=extra
        )
    
    def log_synthesis_stats(self, session_id: str, text_length: int, audio_duration_ms: float, 
                           synthesis_time_ms: float, **kwargs):
        """Registrar estadísticas de síntesis"""
        chars_per_second = text_length / (synthesis_time_ms / 1000) if synthesis_time_ms > 0 else 0
        real_time_factor = audio_duration_ms / synthesis_time_ms if synthesis_time_ms > 0 else 0
        
        extra = {
            "metric_type": "synthesis",
            "session_id": session_id,
            "text_length": text_length,
            "audio_duration_ms": audio_duration_ms,
            "synthesis_time_ms": synthesis_time_ms,
            "chars_per_second": chars_per_second,
            "real_time_factor": real_time_factor,
            **kwargs
        }
        
        self.logger.info(
            f"SYNTHESIS: {text_length} chars -> {audio_duration_ms:.0f}ms audio in {synthesis_time_ms:.2f}ms "
            f"(RTF: {real_time_factor:.2f}x, {chars_per_second:.1f} chars/sec)",
            extra=extra
        )
    
    def get_average_latency(self, operation: str) -> Optional[float]:
        """Obtener latencia promedio para una operación"""
        if operation in self.metrics and self.metrics[operation]:
            return sum(self.metrics[operation]) / len(self.metrics[operation])
        return None
    
    def reset_metrics(self):
        """Resetear métricas en memoria"""
        self.metrics.clear()


class TimingContext:
    """Context manager para medir tiempo de operaciones"""
    
    def __init__(self, performance_logger: PerformanceLogger, operation: str, 
                 session_id: str, **kwargs):
        self.performance_logger = performance_logger
        self.operation = operation
        self.session_id = session_id
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.performance_logger.log_latency(
                self.operation, duration_ms, self.session_id, **self.kwargs
            )


def setup_logging(config) -> Dict[str, logging.Logger]:
    """
    Configurar sistema de logging completo
    
    Args:
        config: Configuración de logging
        
    Returns:
        Dict con loggers configurados
    """
    
    # Crear directorio de logs si no existe
    log_file = Path(config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level))
    
    # Limpiar handlers existentes
    root_logger.handlers.clear()
    
    # Formatter para logs de texto
    text_formatter = logging.Formatter(
        config.format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formatter para logs JSON
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    if config.console:
        if config.level == "DEBUG":
            # Usar RichHandler para debug con mejor formato
            console_handler = RichHandler(
                console=console,
                rich_tracebacks=True,
                tracebacks_show_locals=True
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(text_formatter)
        
        console_handler.setLevel(getattr(logging, config.level))
        root_logger.addHandler(console_handler)
    
    # Handler para archivo
    if config.file:
        # Convertir tamaño máximo
        max_bytes = _parse_size(config.max_size)
        
        file_handler = logging.handlers.RotatingFileHandler(
            config.file,
            maxBytes=max_bytes,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        
        if config.json_format:
            file_handler.setFormatter(json_formatter)
        else:
            file_handler.setFormatter(text_formatter)
        
        file_handler.setLevel(getattr(logging, config.level))
        root_logger.addHandler(file_handler)
    
    # Configurar loggers específicos
    loggers = {}
    
    # Logger principal de la aplicación
    app_logger = logging.getLogger("mit_tts_streamer")
    loggers["app"] = app_logger
    
    # Logger para requests HTTP
    if config.log_requests:
        request_logger = logging.getLogger("uvicorn.access")
        request_logger.setLevel(logging.INFO)
        loggers["requests"] = request_logger
    
    # Logger para performance
    if config.log_performance:
        perf_logger = logging.getLogger("performance")
        perf_logger.setLevel(logging.INFO)
        loggers["performance"] = perf_logger
    
    # Logger para WebSocket
    ws_logger = logging.getLogger("websockets")
    ws_logger.setLevel(logging.WARNING)  # Reducir verbosidad por defecto
    loggers["websocket"] = ws_logger
    
    # Logger para TTS
    tts_logger = logging.getLogger("tts")
    loggers["tts"] = tts_logger
    
    # Logger para audio
    audio_logger = logging.getLogger("audio")
    loggers["audio"] = audio_logger
    
    # Configurar niveles específicos para librerías externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Suprimir logs muy verbosos en producción
    if config.level != "DEBUG":
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info(f"Logging system configured - Level: {config.level}, File: {config.file}")
    
    return loggers


def _parse_size(size_str: str) -> int:
    """Convertir string de tamaño a bytes"""
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # Asumir bytes si no hay sufijo
        return int(size_str)


class StructuredLogger:
    """
    Logger estructurado para eventos específicos del sistema
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_session_event(self, event_type: str, session_id: str, **kwargs):
        """Registrar evento de sesión"""
        extra = {
            "event_type": "session",
            "session_event": event_type,
            "session_id": session_id,
            **kwargs
        }
        
        self.logger.info(f"SESSION {event_type}: {session_id}", extra=extra)
    
    def log_tts_event(self, event_type: str, session_id: str, text_preview: str = "", **kwargs):
        """Registrar evento TTS"""
        # Limitar preview del texto
        if len(text_preview) > 50:
            text_preview = text_preview[:47] + "..."
        
        extra = {
            "event_type": "tts",
            "tts_event": event_type,
            "session_id": session_id,
            "text_preview": text_preview,
            **kwargs
        }
        
        self.logger.info(f"TTS {event_type}: {session_id} - '{text_preview}'", extra=extra)
    
    def log_audio_event(self, event_type: str, session_id: str, **kwargs):
        """Registrar evento de audio"""
        extra = {
            "event_type": "audio",
            "audio_event": event_type,
            "session_id": session_id,
            **kwargs
        }
        
        self.logger.info(f"AUDIO {event_type}: {session_id}", extra=extra)
    
    def log_error_event(self, error_type: str, session_id: str, error_msg: str, **kwargs):
        """Registrar evento de error"""
        extra = {
            "event_type": "error",
            "error_type": error_type,
            "session_id": session_id,
            "error_message": error_msg,
            **kwargs
        }
        
        self.logger.error(f"ERROR {error_type}: {session_id} - {error_msg}", extra=extra)


# Instancia global de performance logger
performance_logger = PerformanceLogger("global")

# Context manager para timing
def time_operation(operation: str, session_id: str, **kwargs):
    """Context manager para medir tiempo de operaciones"""
    return TimingContext(performance_logger, operation, session_id, **kwargs)