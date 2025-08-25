"""
Optimization Module for MIT-TTS-Streamer

Módulo de optimizaciones para baja latencia y alto rendimiento.
"""

from .latency_optimizer import LatencyOptimizer
from .performance_monitor import PerformanceMonitor

__all__ = [
    'LatencyOptimizer',
    'PerformanceMonitor'
]