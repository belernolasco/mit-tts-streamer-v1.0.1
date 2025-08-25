"""
Base TTS Engine for MIT-TTS-Streamer

Clase base abstracta para todos los motores TTS.
Define la interfaz común que deben implementar todos los engines.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, AsyncGenerator, Any, Tuple
import time

logger = logging.getLogger(__name__)


class TTSEngineError(Exception):
    """Excepción base para errores del motor TTS"""
    pass


class AudioFormat(Enum):
    """Formatos de audio soportados"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"


class VoiceGender(Enum):
    """Géneros de voz"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass
class VoiceInfo:
    """Información de una voz TTS"""
    id: str
    name: str
    language: str
    gender: VoiceGender
    sample_rate: int
    description: Optional[str] = None
    model_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "gender": self.gender.value,
            "sample_rate": self.sample_rate,
            "description": self.description,
            "model_path": self.model_path
        }


@dataclass
class SynthesisConfig:
    """Configuración para síntesis TTS"""
    voice_id: str
    language: str = "es"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    format: AudioFormat = AudioFormat.WAV
    sample_rate: int = 22050
    chunk_size: int = 1024
    
    def __post_init__(self):
        # Validar rangos
        self.speed = max(0.1, min(3.0, self.speed))
        self.pitch = max(0.1, min(3.0, self.pitch))
        self.volume = max(0.0, min(2.0, self.volume))
        self.chunk_size = max(256, min(8192, self.chunk_size))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "voice_id": self.voice_id,
            "language": self.language,
            "speed": self.speed,
            "pitch": self.pitch,
            "volume": self.volume,
            "format": self.format.value,
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size
        }


@dataclass
class AudioChunk:
    """Chunk de audio con metadatos"""
    data: bytes
    index: int
    total_chunks: int
    format: AudioFormat
    sample_rate: int
    duration_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data.hex(),
            "index": self.index,
            "total_chunks": self.total_chunks,
            "format": self.format.value,
            "sample_rate": self.sample_rate,
            "duration_ms": self.duration_ms,
            "size_bytes": len(self.data)
        }


@dataclass
class SynthesisResult:
    """Resultado de síntesis TTS"""
    text: str
    audio_chunks: List[AudioChunk]
    total_duration_ms: float
    synthesis_time_ms: float
    config: SynthesisConfig
    
    @property
    def total_audio_bytes(self) -> int:
        return sum(len(chunk.data) for chunk in self.audio_chunks)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "total_chunks": len(self.audio_chunks),
            "total_duration_ms": self.total_duration_ms,
            "synthesis_time_ms": self.synthesis_time_ms,
            "total_audio_bytes": self.total_audio_bytes,
            "config": self.config.to_dict()
        }


class BaseTTSEngine(ABC):
    """
    Clase base abstracta para motores TTS
    
    Define la interfaz común que deben implementar todos los engines TTS.
    Incluye métodos para síntesis, gestión de voces y configuración.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_initialized = False
        self.supported_languages: List[str] = []
        self.available_voices: Dict[str, VoiceInfo] = {}
        self.synthesis_stats = {
            "total_requests": 0,
            "total_synthesis_time": 0.0,
            "total_audio_bytes": 0,
            "average_latency": 0.0
        }
        
        logger.info(f"TTS Engine '{name}' created")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Inicializar el motor TTS
        
        Returns:
            True si la inicialización fue exitosa
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Limpiar recursos del motor TTS"""
        pass
    
    @abstractmethod
    async def get_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        Obtener lista de voces disponibles
        
        Args:
            language: Filtrar por idioma (opcional)
            
        Returns:
            Lista de voces disponibles
        """
        pass
    
    @abstractmethod
    async def synthesize_streaming(
        self, 
        text: str, 
        config: SynthesisConfig
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        Sintetizar texto con streaming de audio
        
        Args:
            text: Texto a sintetizar
            config: Configuración de síntesis
            
        Yields:
            Chunks de audio conforme se generan
        """
        pass
    
    async def synthesize(self, text: str, config: SynthesisConfig) -> SynthesisResult:
        """
        Sintetizar texto completo
        
        Args:
            text: Texto a sintetizar
            config: Configuración de síntesis
            
        Returns:
            Resultado completo de síntesis
        """
        start_time = time.time()
        chunks = []
        
        async for chunk in self.synthesize_streaming(text, config):
            chunks.append(chunk)
        
        synthesis_time = (time.time() - start_time) * 1000
        total_duration = sum(chunk.duration_ms for chunk in chunks)
        
        # Actualizar estadísticas
        self._update_stats(synthesis_time, sum(len(chunk.data) for chunk in chunks))
        
        return SynthesisResult(
            text=text,
            audio_chunks=chunks,
            total_duration_ms=total_duration,
            synthesis_time_ms=synthesis_time,
            config=config
        )
    
    @abstractmethod
    async def is_voice_available(self, voice_id: str, language: str) -> bool:
        """
        Verificar si una voz está disponible
        
        Args:
            voice_id: ID de la voz
            language: Idioma
            
        Returns:
            True si la voz está disponible
        """
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """
        Obtener idiomas soportados
        
        Returns:
            Lista de códigos de idioma soportados
        """
        pass
    
    @abstractmethod
    async def get_supported_formats(self) -> List[AudioFormat]:
        """
        Obtener formatos de audio soportados
        
        Returns:
            Lista de formatos soportados
        """
        pass
    
    async def validate_config(self, config: SynthesisConfig) -> bool:
        """
        Validar configuración de síntesis
        
        Args:
            config: Configuración a validar
            
        Returns:
            True si la configuración es válida
        """
        try:
            # Verificar voz disponible
            if not await self.is_voice_available(config.voice_id, config.language):
                return False
            
            # Verificar idioma soportado
            supported_languages = await self.get_supported_languages()
            if config.language not in supported_languages:
                return False
            
            # Verificar formato soportado
            supported_formats = await self.get_supported_formats()
            if config.format not in supported_formats:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return False
    
    def _update_stats(self, synthesis_time_ms: float, audio_bytes: int):
        """Actualizar estadísticas del motor"""
        self.synthesis_stats["total_requests"] += 1
        self.synthesis_stats["total_synthesis_time"] += synthesis_time_ms
        self.synthesis_stats["total_audio_bytes"] += audio_bytes
        
        # Calcular latencia promedio
        self.synthesis_stats["average_latency"] = (
            self.synthesis_stats["total_synthesis_time"] / 
            self.synthesis_stats["total_requests"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del motor"""
        return {
            "name": self.name,
            "is_initialized": self.is_initialized,
            "supported_languages": self.supported_languages,
            "available_voices_count": len(self.available_voices),
            "stats": self.synthesis_stats.copy()
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Obtener información del motor"""
        return {
            "name": self.name,
            "is_initialized": self.is_initialized,
            "supported_languages": self.supported_languages,
            "available_voices": [voice.to_dict() for voice in self.available_voices.values()],
            "config": self.config
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verificar salud del motor TTS
        
        Returns:
            Estado de salud del motor
        """
        try:
            if not self.is_initialized:
                return {
                    "status": "unhealthy",
                    "reason": "Engine not initialized"
                }
            
            # Verificar voces disponibles
            voices = await self.get_voices()
            if not voices:
                return {
                    "status": "unhealthy", 
                    "reason": "No voices available"
                }
            
            # Verificar idiomas soportados
            languages = await self.get_supported_languages()
            if not languages:
                return {
                    "status": "unhealthy",
                    "reason": "No languages supported"
                }
            
            return {
                "status": "healthy",
                "voices_count": len(voices),
                "languages_count": len(languages),
                "stats": self.synthesis_stats
            }
            
        except Exception as e:
            logger.error(f"Health check failed for engine {self.name}: {e}")
            return {
                "status": "unhealthy",
                "reason": f"Health check error: {str(e)}"
            }
    
    def __str__(self) -> str:
        return f"TTSEngine({self.name}, initialized={self.is_initialized})"
    
    def __repr__(self) -> str:
        return self.__str__()