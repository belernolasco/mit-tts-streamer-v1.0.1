#!/usr/bin/env python3
"""
MIT-TTS-Streamer - Main Entry Point

Servidor TTS de baja latencia con streaming en tiempo real.
Clon de piper-server con licencia MIT.

Autor: Beler Nolasco Almonte

Características principales:
- Latencia ultra-baja (<300ms)
- Interrupciones inmediatas (<10ms)
- Streaming de audio en tiempo real
- Soporte multi-usuario
- API REST + WebSocket
- Motor TTS multi-idioma
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Agregar el directorio src al path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigManager
from server.http_server import HTTPServer

# Importar WebSocket server si está disponible
try:
    from server.websocket_server import WebSocketServer
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    WebSocketServer = None

# Importar motor TTS si está disponible
try:
    from tts.engine_manager import TTSEngineManager
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    TTSEngineManager = None

logger = logging.getLogger(__name__)


class TTSStreamer:
    """Servidor principal MIT-TTS-Streamer"""
    
    def __init__(self, config_path: str = None):
        # Inicializar gestor de configuración
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Configurar logging
        self._setup_logging()
        
        # Inicializar motor TTS
        self.tts_engine_manager = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine_manager = TTSEngineManager(self.config.tts)
                logger.info("TTS Engine Manager initialized")
            except Exception as e:
                logger.warning(f"TTS Engine Manager initialization failed: {e}")
                self.tts_engine_manager = None
        else:
            logger.warning("TTS Engine Manager not available (missing dependencies)")
            logger.warning("Install TTS dependencies for full functionality: pip install melo-tts numpy")
        
        # Inicializar servidores
        self.http_server = HTTPServer(self.config_manager)
        self.websocket_server = None
        
        # Intentar inicializar servidor WebSocket
        if WEBSOCKET_AVAILABLE:
            try:
                self.websocket_server = WebSocketServer(self.config_manager, self.tts_engine_manager)
                logger.info("WebSocket server initialized")
            except Exception as e:
                logger.warning(f"WebSocket server initialization failed: {e}")
                self.websocket_server = None
        else:
            logger.warning("WebSocket server not available (websockets library not installed)")
            logger.warning("Install websockets library for full functionality: pip install websockets")
        
        # Estado del servidor
        self.is_running = False
        
        logger.info("MIT-TTS-Streamer initialized")
    
    def _setup_logging(self):
        """Configurar sistema de logging"""
        log_config = self.config.logging
        
        # Configurar nivel de logging
        log_level = getattr(logging, log_config.level.upper(), logging.INFO)
        
        # Configurar formato
        formatter = logging.Formatter(
            fmt=log_config.format,
            datefmt=log_config.date_format
        )
        
        # Configurar handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        
        # Configurar archivo de log si está especificado
        if log_config.file:
            try:
                file_handler = logging.FileHandler(log_config.file)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
                logger.info(f"Logging to file: {log_config.file}")
            except Exception as e:
                logger.warning(f"Could not setup file logging: {e}")
        
        logger.info(f"Logging configured - Level: {log_config.level}")
    
    async def start(self):
        """Iniciar el servidor TTS"""
        if self.is_running:
            logger.warning("Server is already running")
            return
        
        try:
            logger.info("Starting MIT-TTS-Streamer...")
            
            # Iniciar servidor HTTP
            await self.http_server.start()
            
            # Iniciar servidor WebSocket si está disponible
            if self.websocket_server:
                await self.websocket_server.start()
            
            self.is_running = True
            logger.info("MIT-TTS-Streamer started successfully")
            
            # Mostrar información de conexión
            self._show_connection_info()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Detener el servidor TTS"""
        if not self.is_running:
            return
        
        logger.info("Stopping MIT-TTS-Streamer...")
        self.is_running = False
        
        try:
            # Detener servidor WebSocket
            if self.websocket_server:
                await self.websocket_server.stop()
            
            # Detener servidor HTTP
            await self.http_server.stop()
            
            logger.info("MIT-TTS-Streamer stopped")
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
    
    def _show_connection_info(self):
        """Mostrar información de conexión"""
        server_config = self.config.server
        
        logger.info("=" * 60)
        logger.info("MIT-TTS-Streamer is running!")
        logger.info("=" * 60)
        logger.info(f"HTTP REST API: http://{server_config.host}:{server_config.http_port}")
        logger.info(f"API Documentation: http://{server_config.host}:{server_config.http_port}/docs")
        logger.info(f"Health Check: http://{server_config.host}:{server_config.http_port}/health")
        
        if self.websocket_server:
            logger.info(f"WebSocket Server: ws://{server_config.host}:{server_config.websocket_port}")
            logger.info("Real-time audio streaming available")
        else:
            logger.info("WebSocket Server: Not available (install websockets library)")
        
        logger.info("=" * 60)
    
    def get_status(self):
        """Obtener estado completo del servidor"""
        status = {
            "is_running": self.is_running,
            "http_server": self.http_server.get_status(),
            "websocket_server": self.websocket_server.get_status() if self.websocket_server else None,
            "tts_engine_manager": self.tts_engine_manager.get_status() if self.tts_engine_manager else None
        }
        return status
    
    async def run_forever(self):
        """Ejecutar servidor indefinidamente"""
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()


async def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MIT-TTS-Streamer - Low-latency TTS streaming server"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=None
    )
    parser.add_argument(
        "--host",
        help="HTTP server host (overrides config)",
        default=None
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        help="HTTP server port (overrides config)",
        default=None
    )
    parser.add_argument(
        "--websocket-port",
        type=int,
        help="WebSocket server port (overrides config)",
        default=None
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (overrides config)",
        default=None
    )
    parser.add_argument(
        "--no-websocket",
        action="store_true",
        help="Disable WebSocket server"
    )
    
    args = parser.parse_args()
    
    try:
        # Crear servidor
        server = TTSStreamer(args.config)
        
        # Aplicar overrides de línea de comandos
        if args.host:
            server.config.server.host = args.host
        if args.port:
            server.config.server.http_port = args.port
        if args.websocket_port and server.websocket_server:
            server.config.server.websocket_port = args.websocket_port
        if args.log_level:
            server.config.logging.level = args.log_level
            server._setup_logging()  # Reconfigurar logging
        if args.no_websocket:
            server.websocket_server = None
            logger.info("WebSocket server disabled by command line option")
        
        # Configurar manejo de señales
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            # El bucle principal manejará la limpieza
            server.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Iniciar servidor
        await server.start()
        
        # Ejecutar indefinidamente
        await server.run_forever()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())