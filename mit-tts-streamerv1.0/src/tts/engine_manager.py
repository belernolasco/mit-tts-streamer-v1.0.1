"""
TTS Engine Manager for MIT-TTS-Streamer

Gestor centralizado de motores TTS que coordina múltiples engines,
maneja fallbacks, balanceo de carga y optimizaciones de rendimiento.
"""

import asyncio
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any, Type
from dataclasses import dataclass
from enum import Enum
import time

from .base_engine import (
    BaseTTSEngine, TTSEngineError, AudioFormat, VoiceInfo, 
    SynthesisConfig, AudioChunk, SynthesisResult
)
from .melo_engine import MeloTTSEngine

logger = logging.getLogger(__name__)


class EngineStatus(Enum):
    """Estados del motor TTS"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class EngineInfo:
    """Información de un motor TTS"""
    name: str
    engine: BaseTTSEngine
    status: EngineStatus
    priority: int
    last_error: Optional[str] = None
    error_count: int = 0
    last_health_check: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "last_health_check": self.last_health_check,
            "engine_info": self.engine.get_info() if self.engine else None
        }


class TTSEngineManager:
    """
    Gestor de motores TTS
    
    Características:
    - Múltiples engines con fallback automático
    - Balanceo de carga por prioridad
    - Health checks automáticos
    - Métricas de rendimiento
    - Gestión de errores y recuperación
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engines: Dict[str, EngineInfo] = {}
        self.default_engine: Optional[str] = None
        self.is_initialized = False
        
        # Configuración del manager
        self.health_check_interval = config.get("health_check_interval", 60)
        self.max_error_count = config.get("max_error_count", 5)
        self.fallback_enabled = config.get("fallback_enabled", True)
        
        # Tareas de background
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Métricas
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "fallback_requests": 0,
            "total_synthesis_time": 0.0,
            "average_latency": 0.0
        }
        
        logger.info("TTS Engine Manager initialized")
    
    async def initialize(self) -> bool:
        """Inicializar el gestor de motores TTS"""
        try:
            logger.info("Initializing TTS Engine Manager...")
            
            # Registrar engines disponibles
            await self._register_engines()
            
            # Inicializar engines
            await self._initialize_engines()
            
            # Seleccionar engine por defecto
            self._select_default_engine()
            
            # Iniciar health checks
            await self.start_health_checks()
            
            self.is_initialized = True
            logger.info(f"TTS Engine Manager initialized - {len(self.engines)} engines registered")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS Engine Manager: {e}")
            return False
    
    async def cleanup(self):
        """Limpiar recursos del gestor"""
        logger.info("Cleaning up TTS Engine Manager...")
        
        self.is_running = False
        
        # Detener health checks
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Limpiar engines
        for engine_info in self.engines.values():
            try:
                await engine_info.engine.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up engine {engine_info.name}: {e}")
        
        self.engines.clear()
        self.is_initialized = False
        
        logger.info("TTS Engine Manager cleanup completed")
    
    async def _register_engines(self):
        """Registrar engines disponibles"""
        engines_config = self.config.get("engines", {})
        
        # Registrar MeloTTS si está configurado
        if "melo" in engines_config:
            melo_config = engines_config["melo"]
            if melo_config.get("enabled", True):
                try:
                    melo_engine = MeloTTSEngine(melo_config)
                    engine_info = EngineInfo(
                        name="melo",
                        engine=melo_engine,
                        status=EngineStatus.UNINITIALIZED,
                        priority=melo_config.get("priority", 1)
                    )
                    self.engines["melo"] = engine_info
                    logger.info("MeloTTS engine registered")
                except Exception as e:
                    logger.error(f"Failed to register MeloTTS engine: {e}")
        
        # TODO: Registrar otros engines (piper, espeak, etc.)
        
        if not self.engines:
            logger.warning("No TTS engines registered")
    
    async def _initialize_engines(self):
        """Inicializar todos los engines registrados"""
        for name, engine_info in self.engines.items():
            try:
                logger.info(f"Initializing engine: {name}")
                engine_info.status = EngineStatus.INITIALIZING
                
                success = await engine_info.engine.initialize()
                
                if success:
                    engine_info.status = EngineStatus.READY
                    logger.info(f"Engine {name} initialized successfully")
                else:
                    engine_info.status = EngineStatus.ERROR
                    engine_info.last_error = "Initialization failed"
                    logger.error(f"Engine {name} initialization failed")
                    
            except Exception as e:
                engine_info.status = EngineStatus.ERROR
                engine_info.last_error = str(e)
                engine_info.error_count += 1
                logger.error(f"Error initializing engine {name}: {e}")
    
    def _select_default_engine(self):
        """Seleccionar engine por defecto basado en prioridad y estado"""
        ready_engines = [
            (name, info) for name, info in self.engines.items()
            if info.status == EngineStatus.READY
        ]
        
        if ready_engines:
            # Ordenar por prioridad (menor número = mayor prioridad)
            ready_engines.sort(key=lambda x: x[1].priority)
            self.default_engine = ready_engines[0][0]
            logger.info(f"Default engine selected: {self.default_engine}")
        else:
            logger.warning("No ready engines available")
    
    async def start_health_checks(self):
        """Iniciar health checks periódicos"""
        if self.health_check_task is None:
            self.is_running = True
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("Health checks started")
    
    async def _health_check_loop(self):
        """Loop de health checks"""
        while self.is_running:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def _perform_health_checks(self):
        """Realizar health checks en todos los engines"""
        for name, engine_info in self.engines.items():
            try:
                if engine_info.status in [EngineStatus.READY, EngineStatus.ERROR]:
                    health = await engine_info.engine.health_check()
                    engine_info.last_health_check = time.time()
                    
                    if health.get("status") == "healthy":
                        if engine_info.status == EngineStatus.ERROR:
                            # Engine se recuperó
                            engine_info.status = EngineStatus.READY
                            engine_info.error_count = 0
                            engine_info.last_error = None
                            logger.info(f"Engine {name} recovered")
                    else:
                        if engine_info.status == EngineStatus.READY:
                            # Engine falló
                            engine_info.status = EngineStatus.ERROR
                            engine_info.error_count += 1
                            engine_info.last_error = health.get("reason", "Health check failed")
                            logger.warning(f"Engine {name} failed health check: {engine_info.last_error}")
                    
                    # Deshabilitar engine si tiene demasiados errores
                    if engine_info.error_count >= self.max_error_count:
                        engine_info.status = EngineStatus.DISABLED
                        logger.error(f"Engine {name} disabled due to too many errors")
                        
            except Exception as e:
                logger.error(f"Error in health check for engine {name}: {e}")
    
    async def get_available_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """Obtener voces disponibles de todos los engines"""
        all_voices = []
        
        for name, engine_info in self.engines.items():
            if engine_info.status == EngineStatus.READY:
                try:
                    voices = await engine_info.engine.get_voices(language)
                    # Agregar prefijo del engine al ID de voz para evitar conflictos
                    for voice in voices:
                        voice.id = f"{name}:{voice.id}"
                    all_voices.extend(voices)
                except Exception as e:
                    logger.error(f"Error getting voices from engine {name}: {e}")
        
        return all_voices
    
    async def get_supported_languages(self) -> List[str]:
        """Obtener idiomas soportados por todos los engines"""
        all_languages = set()
        
        for name, engine_info in self.engines.items():
            if engine_info.status == EngineStatus.READY:
                try:
                    languages = await engine_info.engine.get_supported_languages()
                    all_languages.update(languages)
                except Exception as e:
                    logger.error(f"Error getting languages from engine {name}: {e}")
        
        return sorted(list(all_languages))
    
    async def synthesize_streaming(
        self, 
        text: str, 
        config: SynthesisConfig,
        preferred_engine: Optional[str] = None
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        Sintetizar texto con streaming usando el mejor engine disponible
        
        Args:
            text: Texto a sintetizar
            config: Configuración de síntesis
            preferred_engine: Engine preferido (opcional)
            
        Yields:
            Chunks de audio conforme se generan
        """
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        # Seleccionar engine
        engine_name, engine = await self._select_engine(config, preferred_engine)
        
        if not engine:
            self.metrics["failed_requests"] += 1
            raise TTSEngineError("No suitable TTS engine available")
        
        try:
            # Ajustar voice_id si tiene prefijo de engine
            original_voice_id = config.voice_id
            if ":" in config.voice_id:
                engine_prefix, voice_id = config.voice_id.split(":", 1)
                if engine_prefix == engine_name:
                    config.voice_id = voice_id
            
            # Realizar síntesis
            async for chunk in engine.synthesize_streaming(text, config):
                yield chunk
            
            # Actualizar métricas de éxito
            synthesis_time = (time.time() - start_time) * 1000
            self.metrics["successful_requests"] += 1
            self.metrics["total_synthesis_time"] += synthesis_time
            self.metrics["average_latency"] = (
                self.metrics["total_synthesis_time"] / self.metrics["successful_requests"]
            )
            
        except Exception as e:
            # Restaurar voice_id original
            config.voice_id = original_voice_id
            
            # Intentar fallback si está habilitado
            if self.fallback_enabled and engine_name != self.default_engine:
                logger.warning(f"Engine {engine_name} failed, trying fallback: {e}")
                self.metrics["fallback_requests"] += 1
                
                async for chunk in self._try_fallback_synthesis(text, config, engine_name):
                    yield chunk
            else:
                self.metrics["failed_requests"] += 1
                logger.error(f"Synthesis failed with engine {engine_name}: {e}")
                raise TTSEngineError(f"Synthesis failed: {str(e)}")
    
    async def synthesize(
        self, 
        text: str, 
        config: SynthesisConfig,
        preferred_engine: Optional[str] = None
    ) -> SynthesisResult:
        """Sintetizar texto completo"""
        chunks = []
        async for chunk in self.synthesize_streaming(text, config, preferred_engine):
            chunks.append(chunk)
        
        if not chunks:
            raise TTSEngineError("No audio chunks generated")
        
        total_duration = sum(chunk.duration_ms for chunk in chunks)
        synthesis_time = self.metrics["total_synthesis_time"] / self.metrics["total_requests"]
        
        return SynthesisResult(
            text=text,
            audio_chunks=chunks,
            total_duration_ms=total_duration,
            synthesis_time_ms=synthesis_time,
            config=config
        )
    
    async def _select_engine(
        self, 
        config: SynthesisConfig, 
        preferred_engine: Optional[str] = None
    ) -> tuple[Optional[str], Optional[BaseTTSEngine]]:
        """Seleccionar el mejor engine para la síntesis"""
        
        # Si se especifica engine preferido, intentar usarlo
        if preferred_engine and preferred_engine in self.engines:
            engine_info = self.engines[preferred_engine]
            if engine_info.status == EngineStatus.READY:
                # Verificar si el engine soporta la configuración
                if await engine_info.engine.validate_config(config):
                    return preferred_engine, engine_info.engine
        
        # Buscar engine compatible ordenado por prioridad
        compatible_engines = []
        
        for name, engine_info in self.engines.items():
            if engine_info.status == EngineStatus.READY:
                try:
                    if await engine_info.engine.validate_config(config):
                        compatible_engines.append((name, engine_info))
                except Exception as e:
                    logger.error(f"Error validating config for engine {name}: {e}")
        
        if compatible_engines:
            # Ordenar por prioridad
            compatible_engines.sort(key=lambda x: x[1].priority)
            name, engine_info = compatible_engines[0]
            return name, engine_info.engine
        
        return None, None
    
    async def _try_fallback_synthesis(
        self, 
        text: str, 
        config: SynthesisConfig, 
        failed_engine: str
    ) -> AsyncGenerator[AudioChunk, None]:
        """Intentar síntesis con engine de fallback"""
        
        # Buscar engines alternativos
        fallback_engines = [
            (name, info) for name, info in self.engines.items()
            if name != failed_engine and info.status == EngineStatus.READY
        ]
        
        # Ordenar por prioridad
        fallback_engines.sort(key=lambda x: x[1].priority)
        
        for name, engine_info in fallback_engines:
            try:
                # Ajustar configuración para el engine de fallback
                fallback_config = await self._adapt_config_for_engine(config, engine_info.engine)
                
                if fallback_config:
                    logger.info(f"Trying fallback synthesis with engine: {name}")
                    async for chunk in engine_info.engine.synthesize_streaming(text, fallback_config):
                        yield chunk
                    return
                    
            except Exception as e:
                logger.warning(f"Fallback engine {name} also failed: {e}")
                continue
        
        raise TTSEngineError("All fallback engines failed")
    
    async def _adapt_config_for_engine(
        self, 
        config: SynthesisConfig, 
        engine: BaseTTSEngine
    ) -> Optional[SynthesisConfig]:
        """Adaptar configuración para un engine específico"""
        try:
            # Obtener voces disponibles del engine
            voices = await engine.get_voices(config.language)
            
            if voices:
                # Usar la primera voz compatible
                adapted_config = SynthesisConfig(
                    voice_id=voices[0].id,
                    language=config.language,
                    speed=config.speed,
                    pitch=config.pitch,
                    volume=config.volume,
                    format=config.format,
                    sample_rate=config.sample_rate,
                    chunk_size=config.chunk_size
                )
                
                if await engine.validate_config(adapted_config):
                    return adapted_config
            
            return None
            
        except Exception as e:
            logger.error(f"Error adapting config for engine: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del gestor de engines"""
        return {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "default_engine": self.default_engine,
            "engines": {name: info.to_dict() for name, info in self.engines.items()},
            "metrics": self.metrics.copy(),
            "config": {
                "health_check_interval": self.health_check_interval,
                "max_error_count": self.max_error_count,
                "fallback_enabled": self.fallback_enabled
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del gestor"""
        return self.metrics.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check del gestor completo"""
        ready_engines = sum(1 for info in self.engines.values() if info.status == EngineStatus.READY)
        total_engines = len(self.engines)
        
        status = "healthy" if ready_engines > 0 else "unhealthy"
        
        return {
            "status": status,
            "ready_engines": ready_engines,
            "total_engines": total_engines,
            "default_engine": self.default_engine,
            "metrics": self.metrics
        }