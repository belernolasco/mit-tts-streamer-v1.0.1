"""
TTS Engine Module for MIT-TTS-Streamer

Módulo de motores TTS con soporte para múltiples engines y idiomas.
"""

from .base_engine import BaseTTSEngine, TTSEngineError
from .engine_manager import TTSEngineManager

__all__ = [
    'BaseTTSEngine',
    'TTSEngineError', 
    'TTSEngineManager'
]