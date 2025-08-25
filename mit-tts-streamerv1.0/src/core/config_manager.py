"""
Configuration Manager for MIT-TTS-Streamer

Gestiona la configuración del sistema con soporte para múltiples fuentes
y validación de configuración.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class ServerConfig:
    """Configuración del servidor"""
    def __init__(self, **kwargs):
        self.host = kwargs.get("host", "0.0.0.0")
        self.http_port = kwargs.get("http_port", 8080)
        self.websocket_port = kwargs.get("websocket_port", 8081)
        self.max_connections = kwargs.get("max_connections", 100)
        self.timeout = kwargs.get("timeout", 30)
        self.cors_origins = kwargs.get("cors_origins", ["*"])
        self.cors_methods = kwargs.get("cors_methods", ["GET", "POST", "PUT", "DELETE"])
        self.cors_headers = kwargs.get("cors_headers", ["*"])


class TTSConfig:
    """Configuración del motor TTS"""
    def __init__(self, **kwargs):
        self.engine = kwargs.get("engine", "melo")
        self.device = kwargs.get("device", "cpu")
        self.default_language = kwargs.get("default_language", "es")
        self.default_voice_id = kwargs.get("default_voice_id", 0)
        self.default_speed = kwargs.get("default_speed", 1.0)
        self.chunk_size = kwargs.get("chunk_size", 1024)
        self.sample_rate = kwargs.get("sample_rate", 22050)
        self.supported_languages = kwargs.get("supported_languages", ["es", "en", "fr", "zh", "jp", "kr"])
        self.preload_languages = kwargs.get("preload_languages", ["es", "en"])


class AudioConfig:
    """Configuración de audio"""
    def __init__(self, **kwargs):
        self.default_format = kwargs.get("default_format", "wav")
        self.supported_formats = kwargs.get("supported_formats", ["wav", "mp3", "ogg", "flac"])
        self.buffer_size = kwargs.get("buffer_size", 4096)
        self.streaming_chunk_size = kwargs.get("streaming_chunk_size", 512)
        self.quality = kwargs.get("quality", "high")
        self.compression_level = kwargs.get("compression_level", 6)


class PerformanceConfig:
    """Configuración de rendimiento"""
    def __init__(self, **kwargs):
        self.max_queue_size = kwargs.get("max_queue_size", 1000)
        self.worker_processes = kwargs.get("worker_processes", 4)
        self.preload_models = kwargs.get("preload_models", True)
        self.cache_size = kwargs.get("cache_size", 100)
        self.cache_ttl = kwargs.get("cache_ttl", 3600)
        self.max_text_length = kwargs.get("max_text_length", 5000)
        self.chunk_timeout = kwargs.get("chunk_timeout", 5.0)
        self.synthesis_timeout = kwargs.get("synthesis_timeout", 30.0)


class PriorityConfig:
    """Configuración de una prioridad"""
    def __init__(self, **kwargs):
        self.level = kwargs.get("level", 0)
        self.interrupt_others = kwargs.get("interrupt_others", True)
        self.max_queue_time = kwargs.get("max_queue_time", 0.1)


class PrioritiesConfig:
    """Configuración de prioridades"""
    def __init__(self, **kwargs):
        priorities = kwargs.get("priorities", {})
        self.critical = PriorityConfig(**priorities.get("critical", {"level": 0, "interrupt_others": True, "max_queue_time": 0.1}))
        self.high = PriorityConfig(**priorities.get("high", {"level": 1, "interrupt_others": True, "max_queue_time": 1.0}))
        self.normal = PriorityConfig(**priorities.get("normal", {"level": 2, "interrupt_others": False, "max_queue_time": 10.0}))


class SessionConfig:
    """Configuración de sesiones"""
    def __init__(self, **kwargs):
        self.default_timeout = kwargs.get("default_timeout", 300)
        self.cleanup_interval = kwargs.get("cleanup_interval", 60)
        self.max_sessions_per_ip = kwargs.get("max_sessions_per_ip", 10)
        self.session_id_length = kwargs.get("session_id_length", 32)


class LoggingConfig:
    """Configuración de logging"""
    def __init__(self, **kwargs):
        self.level = kwargs.get("level", "INFO")
        self.format = kwargs.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.date_format = kwargs.get("date_format", "%Y-%m-%d %H:%M:%S")
        self.file = kwargs.get("file", "logs/mit-tts-streamer.log")
        self.max_size = kwargs.get("max_size", "10MB")
        self.backup_count = kwargs.get("backup_count", 5)
        self.console = kwargs.get("console", True)
        self.json_format = kwargs.get("json_format", False)
        self.log_requests = kwargs.get("log_requests", True)
        self.log_performance = kwargs.get("log_performance", True)


class MonitoringConfig:
    """Configuración de monitoreo"""
    def __init__(self, **kwargs):
        self.enabled = kwargs.get("enabled", True)
        self.metrics_endpoint = kwargs.get("metrics_endpoint", "/api/v1/metrics")
        self.health_endpoint = kwargs.get("health_endpoint", "/api/v1/health")
        self.prometheus_enabled = kwargs.get("prometheus_enabled", False)
        self.prometheus_port = kwargs.get("prometheus_port", 9090)


class RateLimitConfig:
    """Configuración de rate limiting"""
    def __init__(self, **kwargs):
        self.enabled = kwargs.get("enabled", True)
        self.requests_per_minute = kwargs.get("requests_per_minute", 100)
        self.burst_size = kwargs.get("burst_size", 20)


class SecurityConfig:
    """Configuración de seguridad"""
    def __init__(self, **kwargs):
        rate_limiting_data = kwargs.get("rate_limiting", {})
        self.api_key_required = kwargs.get("api_key_required", False)
        self.api_key_header = kwargs.get("api_key_header", "X-API-Key")
        self.rate_limiting = RateLimitConfig(**rate_limiting_data)
        self.max_request_size = kwargs.get("max_request_size", "10MB")


class DevelopmentConfig:
    """Configuración de desarrollo"""
    def __init__(self, **kwargs):
        self.debug = kwargs.get("debug", False)
        self.reload = kwargs.get("reload", False)
        self.profiling = kwargs.get("profiling", False)
        self.mock_tts = kwargs.get("mock_tts", False)


class AppConfig:
    """Configuración principal de la aplicación"""
    def __init__(self, **kwargs):
        self.server = ServerConfig(**kwargs.get("server", {}))
        self.tts = TTSConfig(**kwargs.get("tts", {}))
        self.audio = AudioConfig(**kwargs.get("audio", {}))
        self.performance = PerformanceConfig(**kwargs.get("performance", {}))
        self.priorities = PrioritiesConfig(**kwargs.get("priorities", {}))
        self.session = SessionConfig(**kwargs.get("session", {}))
        self.logging = LoggingConfig(**kwargs.get("logging", {}))
        self.monitoring = MonitoringConfig(**kwargs.get("monitoring", {}))
        self.security = SecurityConfig(**kwargs.get("security", {}))
        self.development = DevelopmentConfig(**kwargs.get("development", {}))
    
    def dict(self):
        """Convertir configuración a diccionario"""
        return {
            "server": self.server.__dict__,
            "tts": self.tts.__dict__,
            "audio": self.audio.__dict__,
            "performance": self.performance.__dict__,
            "priorities": {
                "critical": self.priorities.critical.__dict__,
                "high": self.priorities.high.__dict__,
                "normal": self.priorities.normal.__dict__
            },
            "session": self.session.__dict__,
            "logging": self.logging.__dict__,
            "monitoring": self.monitoring.__dict__,
            "security": {
                **self.security.__dict__,
                "rate_limiting": self.security.rate_limiting.__dict__
            },
            "development": self.development.__dict__
        }


class ConfigManager:
    """
    Gestor de configuración para MIT-TTS-Streamer
    
    Maneja la carga, validación y acceso a la configuración del sistema
    desde múltiples fuentes (archivos JSON, variables de entorno, etc.)
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = self._resolve_config_path(config_path)
        self._config: Optional[AppConfig] = None
        self._load_config()
    
    def _resolve_config_path(self, config_path: Optional[Union[str, Path]]) -> Path:
        """Resolver la ruta del archivo de configuración"""
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            else:
                raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # Buscar archivos de configuración en orden de prioridad
        possible_paths = [
            Path("config/local.json"),
            Path("config/default.json"),
            Path("mit-tts-streamer/config/local.json"),
            Path("mit-tts-streamer/config/default.json"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Si no se encuentra ningún archivo, usar configuración por defecto
        logger.warning("No config file found, using default configuration")
        return None
    
    def _load_config(self):
        """Cargar configuración desde archivo"""
        try:
            if self.config_path and self.config_path.exists():
                logger.info(f"Loading configuration from: {self.config_path}")
                
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                self._config = AppConfig(**config_data)
                logger.info("Configuration loaded successfully")
            else:
                logger.info("Using default configuration")
                self._config = AppConfig()
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def get_config(self) -> AppConfig:
        """Obtener la configuración actual"""
        if self._config is None:
            self._load_config()
        return self._config
    
    def reload_config(self):
        """Recargar configuración desde archivo"""
        logger.info("Reloading configuration")
        self._load_config()
    
    def update_config(self, updates: Dict[str, Any]):
        """Actualizar configuración en memoria"""
        if self._config is None:
            self._load_config()
        
        # Crear nueva configuración con actualizaciones
        config_dict = self._config.dict()
        self._deep_update(config_dict, updates)
        
        try:
            self._config = AppConfig(**config_dict)
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise
    
    def save_config(self, path: Optional[Union[str, Path]] = None):
        """Guardar configuración actual a archivo"""
        if self._config is None:
            raise ValueError("No configuration to save")
        
        save_path = Path(path) if path else self.config_path
        if save_path is None:
            raise ValueError("No path specified for saving configuration")
        
        # Crear directorio si no existe
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config.dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to: {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def get_voices_config(self) -> Dict[str, Any]:
        """Cargar configuración de voces desde archivo separado"""
        voices_path = None
        
        if self.config_path:
            voices_path = self.config_path.parent / "voices.json"
        
        if not voices_path or not voices_path.exists():
            # Buscar en ubicaciones alternativas
            possible_paths = [
                Path("config/voices.json"),
                Path("mit-tts-streamer/config/voices.json"),
            ]
            
            for path in possible_paths:
                if path.exists():
                    voices_path = path
                    break
        
        if voices_path and voices_path.exists():
            try:
                with open(voices_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading voices config: {e}")
        
        # Configuración de voces por defecto
        return {
            "voices": {
                "es": {
                    "name": "Spanish",
                    "speakers": [{"id": 0, "name": "ES-Female-1", "gender": "female"}]
                },
                "en": {
                    "name": "English", 
                    "speakers": [{"id": 0, "name": "EN-Female-1", "gender": "female"}]
                }
            }
        }
    
    def validate_config(self) -> bool:
        """Validar la configuración actual"""
        try:
            if self._config is None:
                self._load_config()
            
            # Validaciones básicas
            if self._config.server.http_port == self._config.server.websocket_port:
                raise ValueError("HTTP and WebSocket ports cannot be the same")
            
            # Validar que los idiomas preload estén en supported
            for lang in self._config.tts.preload_languages:
                if lang not in self._config.tts.supported_languages:
                    raise ValueError(f"Preload language '{lang}' not in supported languages")
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    @staticmethod
    def _deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Actualización profunda de diccionario"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                ConfigManager._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value