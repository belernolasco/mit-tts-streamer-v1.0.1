"""
Audio Processing Module for MIT-TTS-Streamer

Módulo de procesamiento de audio con soporte para múltiples formatos
y optimizaciones de baja latencia.
"""

from .audio_processor import AudioProcessor, AudioFormat
from .format_converter import FormatConverter

__all__ = [
    'AudioProcessor',
    'AudioFormat',
    'FormatConverter'
]