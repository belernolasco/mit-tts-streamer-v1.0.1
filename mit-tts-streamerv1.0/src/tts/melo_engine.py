"""
MeloTTS Engine for MIT-TTS-Streamer

Implementación del motor TTS basado en MeloTTS para síntesis multi-idioma
con streaming en tiempo real y baja latencia.
"""

import asyncio
import io
import logging
import numpy as np
import time
import wave
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator, Any

from .base_engine import (
    BaseTTSEngine, TTSEngineError, AudioFormat, VoiceGender,
    VoiceInfo, SynthesisConfig, AudioChunk
)

# Importar MeloTTS si está disponible
try:
    from melo.api import TTS
    from melo.download_utils import load_or_download_model
    MELO_AVAILABLE = True
except ImportError:
    MELO_AVAILABLE = False
    TTS = None

logger = logging.getLogger(__name__)


class MeloTTSEngine(BaseTTSEngine):
    """
    Motor TTS basado en MeloTTS
    
    Características:
    - Soporte multi-idioma (ES, EN, FR, ZH, JP, KR)
    - Streaming de audio en tiempo real
    - Múltiples voces por idioma
    - Baja latencia optimizada
    - Calidad de audio alta
    """
    
    # Configuración de idiomas y voces soportadas
    SUPPORTED_LANGUAGES = {
        "es": {
            "name": "Spanish",
            "voices": {
                "es-0": {"name": "Spanish Female", "gender": VoiceGender.FEMALE},
                "es-1": {"name": "Spanish Male", "gender": VoiceGender.MALE}
            }
        },
        "en": {
            "name": "English", 
            "voices": {
                "en-us-0": {"name": "English US Female", "gender": VoiceGender.FEMALE},
                "en-us-1": {"name": "English US Male", "gender": VoiceGender.MALE},
                "en-br-0": {"name": "English BR Female", "gender": VoiceGender.FEMALE},
                "en-au-0": {"name": "English AU Female", "gender": VoiceGender.FEMALE}
            }
        },
        "fr": {
            "name": "French",
            "voices": {
                "fr-0": {"name": "French Female", "gender": VoiceGender.FEMALE},
                "fr-1": {"name": "French Male", "gender": VoiceGender.MALE}
            }
        },
        "zh": {
            "name": "Chinese",
            "voices": {
                "zh-0": {"name": "Chinese Female", "gender": VoiceGender.FEMALE},
                "zh-1": {"name": "Chinese Male", "gender": VoiceGender.MALE}
            }
        },
        "ja": {
            "name": "Japanese",
            "voices": {
                "ja-0": {"name": "Japanese Female", "gender": VoiceGender.FEMALE},
                "ja-1": {"name": "Japanese Male", "gender": VoiceGender.MALE}
            }
        },
        "ko": {
            "name": "Korean",
            "voices": {
                "ko-0": {"name": "Korean Female", "gender": VoiceGender.FEMALE},
                "ko-1": {"name": "Korean Male", "gender": VoiceGender.MALE}
            }
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("MeloTTS", config)
        
        if not MELO_AVAILABLE:
            raise TTSEngineError("MeloTTS library not available. Install with: pip install melo-tts")
        
        # Configuración específica de MeloTTS
        self.device = config.get("device", "auto")
        self.model_cache_dir = Path(config.get("model_cache_dir", "./models/melo"))
        self.preload_languages = config.get("preload_languages", ["es", "en"])
        self.chunk_duration_ms = config.get("chunk_duration_ms", 200)  # Duración de chunk para streaming
        
        # Modelos TTS por idioma
        self.tts_models: Dict[str, TTS] = {}
        self.model_loading_lock = asyncio.Lock()
        
        # Configuración de audio
        self.default_sample_rate = 44100
        self.supported_formats = [AudioFormat.WAV, AudioFormat.MP3, AudioFormat.OGG]
        
        logger.info(f"MeloTTS engine initialized - device: {self.device}")
    
    async def initialize(self) -> bool:
        """Inicializar el motor MeloTTS"""
        try:
            logger.info("Initializing MeloTTS engine...")
            
            # Crear directorio de cache de modelos
            self.model_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Precargar idiomas especificados
            for language in self.preload_languages:
                if language in self.SUPPORTED_LANGUAGES:
                    await self._load_language_model(language)
                else:
                    logger.warning(f"Language {language} not supported, skipping preload")
            
            # Configurar voces disponibles
            await self._setup_available_voices()
            
            # Configurar idiomas soportados
            self.supported_languages = list(self.SUPPORTED_LANGUAGES.keys())
            
            self.is_initialized = True
            logger.info(f"MeloTTS engine initialized successfully - {len(self.tts_models)} models loaded")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MeloTTS engine: {e}")
            self.is_initialized = False
            return False
    
    async def cleanup(self):
        """Limpiar recursos del motor MeloTTS"""
        logger.info("Cleaning up MeloTTS engine...")
        
        # Limpiar modelos cargados
        self.tts_models.clear()
        self.available_voices.clear()
        self.is_initialized = False
        
        logger.info("MeloTTS engine cleanup completed")
    
    async def _load_language_model(self, language: str) -> bool:
        """
        Cargar modelo TTS para un idioma específico
        
        Args:
            language: Código de idioma
            
        Returns:
            True si se cargó exitosamente
        """
        if language in self.tts_models:
            return True
        
        async with self.model_loading_lock:
            # Verificar nuevamente por si otro hilo ya lo cargó
            if language in self.tts_models:
                return True
            
            try:
                logger.info(f"Loading MeloTTS model for language: {language}")
                
                # Ejecutar carga de modelo en thread pool para no bloquear
                loop = asyncio.get_event_loop()
                tts_model = await loop.run_in_executor(
                    None, 
                    self._load_model_sync, 
                    language
                )
                
                if tts_model:
                    self.tts_models[language] = tts_model
                    logger.info(f"MeloTTS model loaded successfully for language: {language}")
                    return True
                else:
                    logger.error(f"Failed to load MeloTTS model for language: {language}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error loading MeloTTS model for {language}: {e}")
                return False
    
    def _load_model_sync(self, language: str) -> Optional[TTS]:
        """Cargar modelo de forma síncrona (ejecutado en thread pool)"""
        try:
            # Mapear códigos de idioma a modelos MeloTTS
            model_mapping = {
                "es": "ES",
                "en": "EN",
                "fr": "FR", 
                "zh": "ZH",
                "ja": "JP",
                "ko": "KR"
            }
            
            model_name = model_mapping.get(language)
            if not model_name:
                logger.error(f"No model mapping for language: {language}")
                return None
            
            # Crear instancia TTS
            tts = TTS(language=model_name, device=self.device)
            return tts
            
        except Exception as e:
            logger.error(f"Error in _load_model_sync for {language}: {e}")
            return None
    
    async def _setup_available_voices(self):
        """Configurar voces disponibles basadas en modelos cargados"""
        self.available_voices.clear()
        
        for language, lang_info in self.SUPPORTED_LANGUAGES.items():
            if language in self.tts_models:
                for voice_id, voice_info in lang_info["voices"].items():
                    voice = VoiceInfo(
                        id=voice_id,
                        name=voice_info["name"],
                        language=language,
                        gender=voice_info["gender"],
                        sample_rate=self.default_sample_rate,
                        description=f"{voice_info['name']} - {lang_info['name']}"
                    )
                    self.available_voices[voice_id] = voice
        
        logger.info(f"Setup {len(self.available_voices)} available voices")
    
    async def get_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """Obtener lista de voces disponibles"""
        voices = list(self.available_voices.values())
        
        if language:
            voices = [voice for voice in voices if voice.language == language]
        
        return voices
    
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
        if not self.is_initialized:
            raise TTSEngineError("MeloTTS engine not initialized")
        
        # Validar configuración
        if not await self.validate_config(config):
            raise TTSEngineError("Invalid synthesis configuration")
        
        # Obtener idioma de la voz
        voice_language = self._get_voice_language(config.voice_id)
        if not voice_language:
            raise TTSEngineError(f"Voice {config.voice_id} not found")
        
        # Cargar modelo si no está cargado
        if voice_language not in self.tts_models:
            success = await self._load_language_model(voice_language)
            if not success:
                raise TTSEngineError(f"Failed to load model for language: {voice_language}")
        
        try:
            # Ejecutar síntesis en thread pool
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text,
                config,
                voice_language
            )
            
            if not audio_data:
                raise TTSEngineError("Synthesis failed - no audio data generated")
            
            # Dividir audio en chunks para streaming
            async for chunk in self._create_audio_chunks(audio_data, config):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in MeloTTS synthesis: {e}")
            raise TTSEngineError(f"Synthesis failed: {str(e)}")
    
    def _synthesize_sync(self, text: str, config: SynthesisConfig, language: str) -> Optional[bytes]:
        """Síntesis síncrona (ejecutada en thread pool)"""
        try:
            tts_model = self.tts_models[language]
            
            # Configurar parámetros de síntesis
            speaker_id = self._get_speaker_id(config.voice_id)
            
            # Generar audio
            audio_array = tts_model.tts_to_file(
                text=text,
                speaker_id=speaker_id,
                speed=config.speed,
                output_path=None,  # Retornar array en lugar de guardar archivo
                format='wav'
            )
            
            if audio_array is None:
                return None
            
            # Convertir a bytes WAV
            audio_bytes = self._array_to_wav_bytes(
                audio_array, 
                config.sample_rate
            )
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error in _synthesize_sync: {e}")
            return None
    
    def _get_voice_language(self, voice_id: str) -> Optional[str]:
        """Obtener idioma de una voz"""
        voice = self.available_voices.get(voice_id)
        return voice.language if voice else None
    
    def _get_speaker_id(self, voice_id: str) -> int:
        """Obtener speaker ID para MeloTTS basado en voice_id"""
        # Mapear voice_id a speaker_id
        # Por simplicidad, usar el último carácter como speaker_id
        try:
            return int(voice_id.split('-')[-1])
        except (ValueError, IndexError):
            return 0  # Default speaker
    
    def _array_to_wav_bytes(self, audio_array: np.ndarray, sample_rate: int) -> bytes:
        """Convertir array numpy a bytes WAV"""
        try:
            # Normalizar audio si es necesario
            if audio_array.dtype != np.int16:
                # Convertir a int16
                audio_array = (audio_array * 32767).astype(np.int16)
            
            # Crear archivo WAV en memoria
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_array.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            logger.error(f"Error converting array to WAV bytes: {e}")
            return b""
    
    async def _create_audio_chunks(
        self, 
        audio_data: bytes, 
        config: SynthesisConfig
    ) -> AsyncGenerator[AudioChunk, None]:
        """Crear chunks de audio para streaming"""
        try:
            # Calcular tamaño de chunk basado en duración deseada
            bytes_per_ms = (config.sample_rate * 2) / 1000  # 16-bit mono
            chunk_size_bytes = int(self.chunk_duration_ms * bytes_per_ms)
            
            # Ajustar al chunk_size de configuración si es menor
            if config.chunk_size < chunk_size_bytes:
                chunk_size_bytes = config.chunk_size
            
            # Dividir audio en chunks
            total_chunks = (len(audio_data) + chunk_size_bytes - 1) // chunk_size_bytes
            
            for i in range(total_chunks):
                start_idx = i * chunk_size_bytes
                end_idx = min(start_idx + chunk_size_bytes, len(audio_data))
                
                chunk_data = audio_data[start_idx:end_idx]
                chunk_duration = (len(chunk_data) / (config.sample_rate * 2)) * 1000
                
                chunk = AudioChunk(
                    data=chunk_data,
                    index=i,
                    total_chunks=total_chunks,
                    format=config.format,
                    sample_rate=config.sample_rate,
                    duration_ms=chunk_duration
                )
                
                yield chunk
                
                # Pequeña pausa para simular streaming real
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error creating audio chunks: {e}")
            raise TTSEngineError(f"Failed to create audio chunks: {str(e)}")
    
    async def is_voice_available(self, voice_id: str, language: str) -> bool:
        """Verificar si una voz está disponible"""
        voice = self.available_voices.get(voice_id)
        return voice is not None and voice.language == language
    
    async def get_supported_languages(self) -> List[str]:
        """Obtener idiomas soportados"""
        return self.supported_languages.copy()
    
    async def get_supported_formats(self) -> List[AudioFormat]:
        """Obtener formatos de audio soportados"""
        return self.supported_formats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del motor MeloTTS"""
        base_health = await super().health_check()
        
        # Agregar información específica de MeloTTS
        melo_info = {
            "loaded_models": list(self.tts_models.keys()),
            "model_cache_dir": str(self.model_cache_dir),
            "device": self.device,
            "chunk_duration_ms": self.chunk_duration_ms
        }
        
        base_health.update(melo_info)
        return base_health
    
    def get_info(self) -> Dict[str, Any]:
        """Obtener información del motor MeloTTS"""
        base_info = super().get_info()
        
        melo_info = {
            "loaded_models": list(self.tts_models.keys()),
            "preload_languages": self.preload_languages,
            "device": self.device,
            "model_cache_dir": str(self.model_cache_dir),
            "chunk_duration_ms": self.chunk_duration_ms,
            "supported_formats": [fmt.value for fmt in self.supported_formats]
        }
        
        base_info.update(melo_info)
        return base_info