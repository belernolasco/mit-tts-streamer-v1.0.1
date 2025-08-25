"""
Audio Format Converter for MIT-TTS-Streamer

Convertidor de formatos de audio con soporte para WAV, MP3, OGG y FLAC.
Optimizado para baja latencia y streaming en tiempo real.
"""

import asyncio
import io
import logging
import wave
from enum import Enum
from typing import Dict, Any, Optional, Union
import numpy as np

# Importar librerías de audio si están disponibles
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    from pydub import AudioSegment
    from pydub.utils import make_chunks
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Formatos de audio soportados"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"


class AudioQuality(Enum):
    """Calidades de audio"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LOSSLESS = "lossless"


class FormatConverter:
    """
    Convertidor de formatos de audio
    
    Características:
    - Soporte para WAV, MP3, OGG, FLAC
    - Conversión optimizada para streaming
    - Múltiples calidades de audio
    - Procesamiento asíncrono
    - Fallbacks para dependencias faltantes
    """
    
    # Configuraciones de calidad por formato
    QUALITY_SETTINGS = {
        AudioFormat.MP3: {
            AudioQuality.LOW: {"bitrate": "64k"},
            AudioQuality.MEDIUM: {"bitrate": "128k"},
            AudioQuality.HIGH: {"bitrate": "192k"},
            AudioQuality.LOSSLESS: {"bitrate": "320k"}
        },
        AudioFormat.OGG: {
            AudioQuality.LOW: {"bitrate": "64k"},
            AudioQuality.MEDIUM: {"bitrate": "128k"},
            AudioQuality.HIGH: {"bitrate": "192k"},
            AudioQuality.LOSSLESS: {"bitrate": "320k"}
        },
        AudioFormat.FLAC: {
            AudioQuality.LOW: {"compression_level": 0},
            AudioQuality.MEDIUM: {"compression_level": 5},
            AudioQuality.HIGH: {"compression_level": 8},
            AudioQuality.LOSSLESS: {"compression_level": 8}
        }
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.default_quality = AudioQuality(self.config.get("default_quality", "medium"))
        self.chunk_size = self.config.get("chunk_size", 1024)
        
        # Verificar dependencias disponibles
        self.available_formats = self._check_available_formats()
        
        logger.info(f"FormatConverter initialized - available formats: {[f.value for f in self.available_formats]}")
    
    def _check_available_formats(self) -> list[AudioFormat]:
        """Verificar qué formatos están disponibles según las dependencias"""
        available = [AudioFormat.WAV]  # WAV siempre disponible con wave
        
        if PYDUB_AVAILABLE:
            available.extend([AudioFormat.MP3, AudioFormat.OGG])
            logger.info("Pydub available - MP3 and OGG support enabled")
        
        if SOUNDFILE_AVAILABLE:
            available.append(AudioFormat.FLAC)
            logger.info("SoundFile available - FLAC support enabled")
        
        if not PYDUB_AVAILABLE and not SOUNDFILE_AVAILABLE:
            logger.warning("Limited audio format support - install pydub and soundfile for full functionality")
        
        return list(set(available))  # Remover duplicados
    
    def is_format_supported(self, format: AudioFormat) -> bool:
        """Verificar si un formato está soportado"""
        return format in self.available_formats
    
    async def convert_audio(
        self,
        audio_data: bytes,
        source_format: AudioFormat,
        target_format: AudioFormat,
        sample_rate: int = 22050,
        channels: int = 1,
        quality: AudioQuality = None
    ) -> bytes:
        """
        Convertir audio entre formatos
        
        Args:
            audio_data: Datos de audio de origen
            source_format: Formato de origen
            target_format: Formato de destino
            sample_rate: Frecuencia de muestreo
            channels: Número de canales
            quality: Calidad de audio
            
        Returns:
            Datos de audio convertidos
        """
        if not self.is_format_supported(target_format):
            raise ValueError(f"Target format {target_format.value} not supported")
        
        if source_format == target_format:
            return audio_data  # No conversion needed
        
        quality = quality or self.default_quality
        
        try:
            # Ejecutar conversión en thread pool para no bloquear
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._convert_sync,
                audio_data,
                source_format,
                target_format,
                sample_rate,
                channels,
                quality
            )
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise
    
    def _convert_sync(
        self,
        audio_data: bytes,
        source_format: AudioFormat,
        target_format: AudioFormat,
        sample_rate: int,
        channels: int,
        quality: AudioQuality
    ) -> bytes:
        """Conversión síncrona (ejecutada en thread pool)"""
        try:
            # Cargar audio según formato de origen
            if source_format == AudioFormat.WAV:
                audio_segment = self._load_wav(audio_data)
            elif PYDUB_AVAILABLE:
                audio_segment = AudioSegment.from_file(
                    io.BytesIO(audio_data),
                    format=source_format.value
                )
            else:
                raise ValueError(f"Cannot load {source_format.value} format - pydub not available")
            
            # Ajustar propiedades de audio
            if audio_segment.frame_rate != sample_rate:
                audio_segment = audio_segment.set_frame_rate(sample_rate)
            
            if audio_segment.channels != channels:
                if channels == 1:
                    audio_segment = audio_segment.set_channels(1)
                else:
                    audio_segment = audio_segment.set_channels(channels)
            
            # Convertir a formato de destino
            return self._export_format(audio_segment, target_format, quality)
            
        except Exception as e:
            logger.error(f"Sync conversion error: {e}")
            raise
    
    def _load_wav(self, wav_data: bytes) -> 'AudioSegment':
        """Cargar archivo WAV usando wave o pydub"""
        if PYDUB_AVAILABLE:
            return AudioSegment.from_wav(io.BytesIO(wav_data))
        else:
            # Fallback usando wave + numpy
            with wave.open(io.BytesIO(wav_data), 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
            
            # Crear AudioSegment manualmente
            if PYDUB_AVAILABLE:
                return AudioSegment(
                    frames,
                    frame_rate=sample_rate,
                    sample_width=sample_width,
                    channels=channels
                )
            else:
                raise ValueError("Cannot process WAV without pydub")
    
    def _export_format(
        self,
        audio_segment: 'AudioSegment',
        target_format: AudioFormat,
        quality: AudioQuality
    ) -> bytes:
        """Exportar audio al formato de destino"""
        if not PYDUB_AVAILABLE:
            raise ValueError("Cannot export audio formats without pydub")
        
        output_buffer = io.BytesIO()
        
        # Obtener parámetros de calidad
        format_params = self.QUALITY_SETTINGS.get(target_format, {}).get(quality, {})
        
        if target_format == AudioFormat.WAV:
            audio_segment.export(output_buffer, format="wav")
        
        elif target_format == AudioFormat.MP3:
            audio_segment.export(
                output_buffer,
                format="mp3",
                bitrate=format_params.get("bitrate", "128k")
            )
        
        elif target_format == AudioFormat.OGG:
            audio_segment.export(
                output_buffer,
                format="ogg",
                bitrate=format_params.get("bitrate", "128k")
            )
        
        elif target_format == AudioFormat.FLAC:
            if SOUNDFILE_AVAILABLE:
                # Usar soundfile para FLAC
                audio_array = np.array(audio_segment.get_array_of_samples())
                if audio_segment.channels == 2:
                    audio_array = audio_array.reshape((-1, 2))
                
                sf.write(
                    output_buffer,
                    audio_array,
                    audio_segment.frame_rate,
                    format='FLAC',
                    subtype='PCM_16'
                )
            else:
                raise ValueError("FLAC format requires soundfile library")
        
        else:
            raise ValueError(f"Unsupported target format: {target_format.value}")
        
        output_buffer.seek(0)
        return output_buffer.read()
    
    async def convert_streaming(
        self,
        audio_chunks: list[bytes],
        source_format: AudioFormat,
        target_format: AudioFormat,
        sample_rate: int = 22050,
        channels: int = 1,
        quality: AudioQuality = None
    ) -> list[bytes]:
        """
        Convertir múltiples chunks de audio para streaming
        
        Args:
            audio_chunks: Lista de chunks de audio
            source_format: Formato de origen
            target_format: Formato de destino
            sample_rate: Frecuencia de muestreo
            channels: Número de canales
            quality: Calidad de audio
            
        Returns:
            Lista de chunks convertidos
        """
        if source_format == target_format:
            return audio_chunks
        
        # Concatenar chunks para conversión
        combined_audio = b''.join(audio_chunks)
        
        # Convertir audio completo
        converted_audio = await self.convert_audio(
            combined_audio,
            source_format,
            target_format,
            sample_rate,
            channels,
            quality
        )
        
        # Dividir en chunks del tamaño original
        return self._split_audio_chunks(converted_audio, len(audio_chunks))
    
    def _split_audio_chunks(self, audio_data: bytes, num_chunks: int) -> list[bytes]:
        """Dividir audio en chunks"""
        chunk_size = len(audio_data) // num_chunks
        chunks = []
        
        for i in range(num_chunks):
            start = i * chunk_size
            if i == num_chunks - 1:
                # Último chunk incluye cualquier byte restante
                end = len(audio_data)
            else:
                end = start + chunk_size
            
            chunks.append(audio_data[start:end])
        
        return chunks
    
    def get_format_info(self, format: AudioFormat) -> Dict[str, Any]:
        """Obtener información sobre un formato"""
        info = {
            "format": format.value,
            "supported": self.is_format_supported(format),
            "lossy": format in [AudioFormat.MP3, AudioFormat.OGG],
            "streaming_friendly": format != AudioFormat.FLAC,
            "qualities": list(self.QUALITY_SETTINGS.get(format, {}).keys())
        }
        
        return info
    
    def get_supported_formats(self) -> list[Dict[str, Any]]:
        """Obtener lista de formatos soportados con información"""
        return [self.get_format_info(fmt) for fmt in self.available_formats]
    
    async def optimize_for_streaming(
        self,
        audio_data: bytes,
        format: AudioFormat,
        target_bitrate: str = "128k"
    ) -> bytes:
        """
        Optimizar audio para streaming
        
        Args:
            audio_data: Datos de audio
            format: Formato de audio
            target_bitrate: Bitrate objetivo
            
        Returns:
            Audio optimizado
        """
        if format == AudioFormat.WAV:
            return audio_data  # WAV ya es óptimo para streaming
        
        if not PYDUB_AVAILABLE:
            logger.warning("Cannot optimize audio - pydub not available")
            return audio_data
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._optimize_sync,
                audio_data,
                format,
                target_bitrate
            )
        except Exception as e:
            logger.error(f"Audio optimization failed: {e}")
            return audio_data
    
    def _optimize_sync(self, audio_data: bytes, format: AudioFormat, target_bitrate: str) -> bytes:
        """Optimización síncrona"""
        try:
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format=format.value
            )
            
            # Aplicar optimizaciones para streaming
            if format == AudioFormat.MP3:
                # Usar CBR (Constant Bit Rate) para mejor streaming
                output_buffer = io.BytesIO()
                audio_segment.export(
                    output_buffer,
                    format="mp3",
                    bitrate=target_bitrate,
                    parameters=["-q:a", "2", "-ar", "22050"]
                )
                output_buffer.seek(0)
                return output_buffer.read()
            
            elif format == AudioFormat.OGG:
                # Optimizar OGG para streaming
                output_buffer = io.BytesIO()
                audio_segment.export(
                    output_buffer,
                    format="ogg",
                    bitrate=target_bitrate
                )
                output_buffer.seek(0)
                return output_buffer.read()
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Sync optimization error: {e}")
            return audio_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del convertidor"""
        return {
            "available_formats": [f.value for f in self.available_formats],
            "dependencies": {
                "pydub": PYDUB_AVAILABLE,
                "soundfile": SOUNDFILE_AVAILABLE,
                "librosa": LIBROSA_AVAILABLE
            },
            "default_quality": self.default_quality.value,
            "chunk_size": self.chunk_size
        }