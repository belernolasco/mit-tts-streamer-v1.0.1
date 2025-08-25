"""
Audio Processor for MIT-TTS-Streamer

Procesador de audio principal que integra conversión de formatos,
optimizaciones de latencia y procesamiento en tiempo real.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from .format_converter import FormatConverter, AudioFormat, AudioQuality
from ..tts.base_engine import AudioChunk

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Modos de procesamiento de audio"""
    REALTIME = "realtime"      # Procesamiento en tiempo real
    BATCH = "batch"            # Procesamiento por lotes
    STREAMING = "streaming"    # Procesamiento de streaming


@dataclass
class AudioProcessingConfig:
    """Configuración de procesamiento de audio"""
    target_format: AudioFormat = AudioFormat.WAV
    quality: AudioQuality = AudioQuality.MEDIUM
    sample_rate: int = 22050
    channels: int = 1
    chunk_size: int = 1024
    processing_mode: ProcessingMode = ProcessingMode.STREAMING
    enable_optimization: bool = True
    target_latency_ms: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_format": self.target_format.value,
            "quality": self.quality.value,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
            "processing_mode": self.processing_mode.value,
            "enable_optimization": self.enable_optimization,
            "target_latency_ms": self.target_latency_ms
        }


@dataclass
class ProcessingResult:
    """Resultado de procesamiento de audio"""
    processed_chunks: List[AudioChunk]
    processing_time_ms: float
    original_format: AudioFormat
    target_format: AudioFormat
    total_bytes: int
    compression_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_count": len(self.processed_chunks),
            "processing_time_ms": self.processing_time_ms,
            "original_format": self.original_format.value,
            "target_format": self.target_format.value,
            "total_bytes": self.total_bytes,
            "compression_ratio": self.compression_ratio,
            "average_chunk_size": self.total_bytes / len(self.processed_chunks) if self.processed_chunks else 0
        }


class AudioProcessor:
    """
    Procesador de audio principal
    
    Características:
    - Conversión de formatos en tiempo real
    - Optimizaciones de latencia
    - Procesamiento por chunks para streaming
    - Métricas de rendimiento
    - Fallbacks automáticos
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Inicializar convertidor de formatos
        self.format_converter = FormatConverter(self.config.get("converter", {}))
        
        # Configuración de procesamiento
        self.default_config = AudioProcessingConfig(
            target_format=AudioFormat(self.config.get("default_format", "wav")),
            quality=AudioQuality(self.config.get("default_quality", "medium")),
            sample_rate=self.config.get("default_sample_rate", 22050),
            channels=self.config.get("default_channels", 1),
            chunk_size=self.config.get("chunk_size", 1024),
            processing_mode=ProcessingMode(self.config.get("processing_mode", "streaming")),
            enable_optimization=self.config.get("enable_optimization", True),
            target_latency_ms=self.config.get("target_latency_ms", 100.0)
        )
        
        # Métricas
        self.metrics = {
            "total_processed": 0,
            "total_processing_time": 0.0,
            "total_bytes_processed": 0,
            "average_latency_ms": 0.0,
            "format_conversions": {},
            "errors": 0
        }
        
        logger.info("AudioProcessor initialized")
    
    async def process_audio_chunks(
        self,
        audio_chunks: List[AudioChunk],
        processing_config: Optional[AudioProcessingConfig] = None
    ) -> ProcessingResult:
        """
        Procesar lista de chunks de audio
        
        Args:
            audio_chunks: Lista de chunks de audio
            processing_config: Configuración de procesamiento
            
        Returns:
            Resultado del procesamiento
        """
        config = processing_config or self.default_config
        start_time = time.time()
        
        try:
            if not audio_chunks:
                raise ValueError("No audio chunks provided")
            
            original_format = audio_chunks[0].format
            original_bytes = sum(len(chunk.data) for chunk in audio_chunks)
            
            # Procesar según el modo
            if config.processing_mode == ProcessingMode.STREAMING:
                processed_chunks = await self._process_streaming(audio_chunks, config)
            elif config.processing_mode == ProcessingMode.BATCH:
                processed_chunks = await self._process_batch(audio_chunks, config)
            else:  # REALTIME
                processed_chunks = await self._process_realtime(audio_chunks, config)
            
            # Calcular métricas
            processing_time = (time.time() - start_time) * 1000
            processed_bytes = sum(len(chunk.data) for chunk in processed_chunks)
            compression_ratio = processed_bytes / original_bytes if original_bytes > 0 else 1.0
            
            # Actualizar métricas globales
            self._update_metrics(processing_time, processed_bytes, original_format, config.target_format)
            
            result = ProcessingResult(
                processed_chunks=processed_chunks,
                processing_time_ms=processing_time,
                original_format=original_format,
                target_format=config.target_format,
                total_bytes=processed_bytes,
                compression_ratio=compression_ratio
            )
            
            logger.debug(f"Audio processing completed: {result.to_dict()}")
            return result
            
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Audio processing failed: {e}")
            raise
    
    async def process_streaming(
        self,
        audio_chunks: AsyncGenerator[AudioChunk, None],
        processing_config: Optional[AudioProcessingConfig] = None
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        Procesar chunks de audio en streaming
        
        Args:
            audio_chunks: Generador de chunks de audio
            processing_config: Configuración de procesamiento
            
        Yields:
            Chunks de audio procesados
        """
        config = processing_config or self.default_config
        
        try:
            async for chunk in audio_chunks:
                start_time = time.time()
                
                # Procesar chunk individual
                processed_chunk = await self._process_single_chunk(chunk, config)
                
                # Verificar latencia objetivo
                processing_time = (time.time() - start_time) * 1000
                if processing_time > config.target_latency_ms:
                    logger.warning(f"Processing latency exceeded target: {processing_time:.1f}ms > {config.target_latency_ms}ms")
                
                # Actualizar métricas
                self._update_metrics(processing_time, len(processed_chunk.data), chunk.format, config.target_format)
                
                yield processed_chunk
                
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Streaming processing failed: {e}")
            raise
    
    async def _process_streaming(
        self,
        audio_chunks: List[AudioChunk],
        config: AudioProcessingConfig
    ) -> List[AudioChunk]:
        """Procesamiento en modo streaming"""
        processed_chunks = []
        
        for chunk in audio_chunks:
            processed_chunk = await self._process_single_chunk(chunk, config)
            processed_chunks.append(processed_chunk)
            
            # Pequeña pausa para simular streaming real
            await asyncio.sleep(0.001)
        
        return processed_chunks
    
    async def _process_batch(
        self,
        audio_chunks: List[AudioChunk],
        config: AudioProcessingConfig
    ) -> List[AudioChunk]:
        """Procesamiento en modo batch"""
        # Combinar todos los chunks
        combined_data = b''.join(chunk.data for chunk in audio_chunks)
        
        # Convertir formato si es necesario
        if audio_chunks[0].format != config.target_format:
            converted_data = await self.format_converter.convert_audio(
                combined_data,
                audio_chunks[0].format,
                config.target_format,
                config.sample_rate,
                config.channels,
                config.quality
            )
        else:
            converted_data = combined_data
        
        # Dividir en chunks del tamaño objetivo
        return self._split_into_chunks(
            converted_data,
            config.target_format,
            config.sample_rate,
            config.chunk_size
        )
    
    async def _process_realtime(
        self,
        audio_chunks: List[AudioChunk],
        config: AudioProcessingConfig
    ) -> List[AudioChunk]:
        """Procesamiento en modo tiempo real"""
        processed_chunks = []
        
        # Procesar chunks en paralelo para máxima velocidad
        tasks = [
            self._process_single_chunk(chunk, config)
            for chunk in audio_chunks
        ]
        
        processed_chunks = await asyncio.gather(*tasks)
        return processed_chunks
    
    async def _process_single_chunk(
        self,
        chunk: AudioChunk,
        config: AudioProcessingConfig
    ) -> AudioChunk:
        """Procesar un chunk individual"""
        try:
            # Convertir formato si es necesario
            if chunk.format != config.target_format:
                converted_data = await self.format_converter.convert_audio(
                    chunk.data,
                    chunk.format,
                    config.target_format,
                    config.sample_rate,
                    config.channels,
                    config.quality
                )
            else:
                converted_data = chunk.data
            
            # Aplicar optimizaciones si están habilitadas
            if config.enable_optimization:
                converted_data = await self._apply_optimizations(
                    converted_data,
                    config.target_format,
                    config
                )
            
            # Crear nuevo chunk procesado
            processed_chunk = AudioChunk(
                data=converted_data,
                index=chunk.index,
                total_chunks=chunk.total_chunks,
                format=config.target_format,
                sample_rate=config.sample_rate,
                duration_ms=chunk.duration_ms
            )
            
            return processed_chunk
            
        except Exception as e:
            logger.error(f"Error processing single chunk: {e}")
            # Retornar chunk original en caso de error
            return chunk
    
    async def _apply_optimizations(
        self,
        audio_data: bytes,
        format: AudioFormat,
        config: AudioProcessingConfig
    ) -> bytes:
        """Aplicar optimizaciones de audio"""
        try:
            # Optimizar para streaming si el formato lo soporta
            if format in [AudioFormat.MP3, AudioFormat.OGG]:
                return await self.format_converter.optimize_for_streaming(
                    audio_data,
                    format,
                    self._get_target_bitrate(config.quality)
                )
            
            return audio_data
            
        except Exception as e:
            logger.warning(f"Optimization failed, using original data: {e}")
            return audio_data
    
    def _get_target_bitrate(self, quality: AudioQuality) -> str:
        """Obtener bitrate objetivo según la calidad"""
        bitrate_map = {
            AudioQuality.LOW: "64k",
            AudioQuality.MEDIUM: "128k",
            AudioQuality.HIGH: "192k",
            AudioQuality.LOSSLESS: "320k"
        }
        return bitrate_map.get(quality, "128k")
    
    def _split_into_chunks(
        self,
        audio_data: bytes,
        format: AudioFormat,
        sample_rate: int,
        chunk_size: int
    ) -> List[AudioChunk]:
        """Dividir audio en chunks"""
        chunks = []
        total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size
        
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(audio_data))
            chunk_data = audio_data[start:end]
            
            # Calcular duración aproximada
            bytes_per_second = sample_rate * 2  # 16-bit mono
            duration_ms = (len(chunk_data) / bytes_per_second) * 1000
            
            chunk = AudioChunk(
                data=chunk_data,
                index=i,
                total_chunks=total_chunks,
                format=format,
                sample_rate=sample_rate,
                duration_ms=duration_ms
            )
            chunks.append(chunk)
        
        return chunks
    
    def _update_metrics(
        self,
        processing_time: float,
        bytes_processed: int,
        original_format: AudioFormat,
        target_format: AudioFormat
    ):
        """Actualizar métricas de procesamiento"""
        self.metrics["total_processed"] += 1
        self.metrics["total_processing_time"] += processing_time
        self.metrics["total_bytes_processed"] += bytes_processed
        
        # Calcular latencia promedio
        self.metrics["average_latency_ms"] = (
            self.metrics["total_processing_time"] / self.metrics["total_processed"]
        )
        
        # Contar conversiones de formato
        conversion_key = f"{original_format.value}_to_{target_format.value}"
        self.metrics["format_conversions"][conversion_key] = (
            self.metrics["format_conversions"].get(conversion_key, 0) + 1
        )
    
    def get_supported_formats(self) -> List[AudioFormat]:
        """Obtener formatos soportados"""
        return self.format_converter.available_formats
    
    def is_format_supported(self, format: AudioFormat) -> bool:
        """Verificar si un formato está soportado"""
        return self.format_converter.is_format_supported(format)
    
    def get_format_info(self, format: AudioFormat) -> Dict[str, Any]:
        """Obtener información sobre un formato"""
        return self.format_converter.get_format_info(format)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento"""
        return {
            "processor_metrics": self.metrics.copy(),
            "converter_stats": self.format_converter.get_stats(),
            "supported_formats": [f.value for f in self.get_supported_formats()],
            "default_config": self.default_config.to_dict()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del procesador de audio"""
        try:
            # Verificar convertidor de formatos
            supported_formats = self.get_supported_formats()
            
            if not supported_formats:
                return {
                    "status": "unhealthy",
                    "reason": "No audio formats supported"
                }
            
            # Verificar si al menos WAV está soportado
            if AudioFormat.WAV not in supported_formats:
                return {
                    "status": "unhealthy",
                    "reason": "WAV format not supported"
                }
            
            return {
                "status": "healthy",
                "supported_formats": len(supported_formats),
                "total_processed": self.metrics["total_processed"],
                "average_latency_ms": self.metrics["average_latency_ms"],
                "error_rate": self.metrics["errors"] / max(self.metrics["total_processed"], 1)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": f"Health check error: {str(e)}"
            }
    
    def reset_metrics(self):
        """Reiniciar métricas"""
        self.metrics = {
            "total_processed": 0,
            "total_processing_time": 0.0,
            "total_bytes_processed": 0,
            "average_latency_ms": 0.0,
            "format_conversions": {},
            "errors": 0
        }
        logger.info("Audio processor metrics reset")