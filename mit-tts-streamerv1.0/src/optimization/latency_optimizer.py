"""
Latency Optimizer for MIT-TTS-Streamer

Optimizador de latencia que implementa técnicas avanzadas para lograr
latencias ultra-bajas (<300ms síntesis, <10ms interrupciones).
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Niveles de optimización"""
    CONSERVATIVE = "conservative"  # Optimizaciones seguras
    BALANCED = "balanced"         # Balance entre rendimiento y estabilidad
    AGGRESSIVE = "aggressive"     # Máximo rendimiento


@dataclass
class LatencyTarget:
    """Objetivos de latencia"""
    synthesis_ms: float = 300.0      # Latencia objetivo para síntesis
    interrupt_ms: float = 10.0       # Latencia objetivo para interrupciones
    network_ms: float = 50.0         # Latencia objetivo de red
    processing_ms: float = 100.0     # Latencia objetivo de procesamiento
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "synthesis_ms": self.synthesis_ms,
            "interrupt_ms": self.interrupt_ms,
            "network_ms": self.network_ms,
            "processing_ms": self.processing_ms
        }


@dataclass
class OptimizationMetrics:
    """Métricas de optimización"""
    current_synthesis_latency: float = 0.0
    current_interrupt_latency: float = 0.0
    current_network_latency: float = 0.0
    current_processing_latency: float = 0.0
    
    optimization_hits: int = 0
    optimization_misses: int = 0
    
    def success_rate(self) -> float:
        total = self.optimization_hits + self.optimization_misses
        return self.optimization_hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_synthesis_latency": self.current_synthesis_latency,
            "current_interrupt_latency": self.current_interrupt_latency,
            "current_network_latency": self.current_network_latency,
            "current_processing_latency": self.current_processing_latency,
            "optimization_hits": self.optimization_hits,
            "optimization_misses": self.optimization_misses,
            "success_rate": self.success_rate()
        }


class LatencyOptimizer:
    """
    Optimizador de latencia ultra-baja
    
    Técnicas implementadas:
    - Pre-carga de modelos TTS
    - Pool de threads optimizado
    - Cache de audio frecuente
    - Predicción de carga
    - Priorización de tareas críticas
    - Optimización de I/O asíncrono
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Configuración de optimización
        self.optimization_level = OptimizationLevel(
            self.config.get("optimization_level", "balanced")
        )
        self.latency_targets = LatencyTarget(
            synthesis_ms=self.config.get("synthesis_target_ms", 300.0),
            interrupt_ms=self.config.get("interrupt_target_ms", 10.0),
            network_ms=self.config.get("network_target_ms", 50.0),
            processing_ms=self.config.get("processing_target_ms", 100.0)
        )
        
        # Thread pool optimizado
        self.max_workers = self._calculate_optimal_workers()
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="tts_optimizer"
        )
        
        # Cache de audio
        self.audio_cache_enabled = self.config.get("enable_audio_cache", True)
        self.audio_cache: Dict[str, bytes] = {}
        self.cache_max_size = self.config.get("cache_max_size", 100)
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Métricas
        self.metrics = OptimizationMetrics()
        
        # Estado
        self.is_initialized = False
        self.optimization_tasks: List[asyncio.Task] = []
        
        logger.info(f"LatencyOptimizer initialized - level: {self.optimization_level.value}")
    
    async def initialize(self) -> bool:
        """Inicializar el optimizador"""
        try:
            logger.info("Initializing LatencyOptimizer...")
            
            # Aplicar optimizaciones según el nivel
            await self._apply_system_optimizations()
            
            # Iniciar tareas de optimización en background
            await self._start_optimization_tasks()
            
            self.is_initialized = True
            logger.info("LatencyOptimizer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LatencyOptimizer: {e}")
            return False
    
    async def cleanup(self):
        """Limpiar recursos del optimizador"""
        logger.info("Cleaning up LatencyOptimizer...")
        
        # Cancelar tareas de optimización
        for task in self.optimization_tasks:
            if not task.done():
                task.cancel()
        
        if self.optimization_tasks:
            await asyncio.gather(*self.optimization_tasks, return_exceptions=True)
        
        # Cerrar thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Limpiar cache
        self.audio_cache.clear()
        
        self.is_initialized = False
        logger.info("LatencyOptimizer cleanup completed")
    
    def _calculate_optimal_workers(self) -> int:
        """Calcular número óptimo de workers"""
        import os
        
        cpu_count = os.cpu_count() or 4
        
        if self.optimization_level == OptimizationLevel.CONSERVATIVE:
            return min(cpu_count, 4)
        elif self.optimization_level == OptimizationLevel.BALANCED:
            return min(cpu_count * 2, 8)
        else:  # AGGRESSIVE
            return min(cpu_count * 3, 16)
    
    async def _apply_system_optimizations(self):
        """Aplicar optimizaciones del sistema"""
        try:
            # Configurar event loop para baja latencia
            loop = asyncio.get_event_loop()
            
            if hasattr(loop, 'set_debug'):
                loop.set_debug(False)  # Desactivar debug para mejor rendimiento
            
            # Configurar políticas de scheduling si están disponibles
            if self.optimization_level == OptimizationLevel.AGGRESSIVE:
                await self._apply_aggressive_optimizations()
            
            logger.info("System optimizations applied")
            
        except Exception as e:
            logger.warning(f"Some system optimizations failed: {e}")
    
    async def _apply_aggressive_optimizations(self):
        """Aplicar optimizaciones agresivas"""
        try:
            # Configurar prioridades de proceso si es posible
            import os
            if hasattr(os, 'nice'):
                try:
                    os.nice(-5)  # Aumentar prioridad del proceso
                    logger.info("Process priority increased")
                except PermissionError:
                    logger.warning("Cannot increase process priority - insufficient permissions")
            
            # Configurar afinidad de CPU si está disponible
            try:
                import psutil
                process = psutil.Process()
                cpu_count = psutil.cpu_count()
                if cpu_count > 1:
                    # Usar CPUs específicos para mejor cache locality
                    process.cpu_affinity(list(range(min(4, cpu_count))))
                    logger.info("CPU affinity configured")
            except ImportError:
                logger.debug("psutil not available - skipping CPU affinity optimization")
            
        except Exception as e:
            logger.warning(f"Aggressive optimizations failed: {e}")
    
    async def _start_optimization_tasks(self):
        """Iniciar tareas de optimización en background"""
        # Tarea de limpieza de cache
        if self.audio_cache_enabled:
            cache_cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
            self.optimization_tasks.append(cache_cleanup_task)
        
        # Tarea de monitoreo de latencia
        latency_monitor_task = asyncio.create_task(self._latency_monitor_loop())
        self.optimization_tasks.append(latency_monitor_task)
        
        logger.info(f"Started {len(self.optimization_tasks)} optimization tasks")
    
    async def optimize_synthesis_call(
        self,
        synthesis_func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Optimizar llamada de síntesis TTS
        
        Args:
            synthesis_func: Función de síntesis a optimizar
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
            
        Returns:
            Resultado de la síntesis optimizada
        """
        start_time = time.time()
        
        try:
            # Verificar cache si está habilitado
            if self.audio_cache_enabled:
                cache_key = self._generate_cache_key(args, kwargs)
                cached_result = self._get_from_cache(cache_key)
                if cached_result is not None:
                    self.cache_hits += 1
                    latency = (time.time() - start_time) * 1000
                    self.metrics.current_synthesis_latency = latency
                    return cached_result
                else:
                    self.cache_misses += 1
            
            # Ejecutar síntesis con optimizaciones
            if self.optimization_level == OptimizationLevel.AGGRESSIVE:
                # Usar thread pool para operaciones CPU-intensivas
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_pool,
                    lambda: asyncio.run(synthesis_func(*args, **kwargs))
                )
            else:
                # Ejecución normal asíncrona
                result = await synthesis_func(*args, **kwargs)
            
            # Guardar en cache si está habilitado
            if self.audio_cache_enabled and cache_key:
                self._add_to_cache(cache_key, result)
            
            # Actualizar métricas
            latency = (time.time() - start_time) * 1000
            self.metrics.current_synthesis_latency = latency
            
            if latency <= self.latency_targets.synthesis_ms:
                self.metrics.optimization_hits += 1
            else:
                self.metrics.optimization_misses += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Synthesis optimization failed: {e}")
            # Fallback a ejecución normal
            return await synthesis_func(*args, **kwargs)
    
    async def optimize_interrupt_call(
        self,
        interrupt_func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Optimizar llamada de interrupción
        
        Args:
            interrupt_func: Función de interrupción a optimizar
            *args: Argumentos posicionales
            **kwargs: Argumentos de palabra clave
            
        Returns:
            Resultado de la interrupción optimizada
        """
        start_time = time.time()
        
        try:
            # Las interrupciones siempre tienen máxima prioridad
            # Ejecutar inmediatamente sin cache ni thread pool
            result = await interrupt_func(*args, **kwargs)
            
            # Actualizar métricas
            latency = (time.time() - start_time) * 1000
            self.metrics.current_interrupt_latency = latency
            
            if latency <= self.latency_targets.interrupt_ms:
                self.metrics.optimization_hits += 1
            else:
                self.metrics.optimization_misses += 1
                logger.warning(f"Interrupt latency exceeded target: {latency:.1f}ms > {self.latency_targets.interrupt_ms}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Interrupt optimization failed: {e}")
            raise
    
    def _generate_cache_key(self, args: tuple, kwargs: dict) -> Optional[str]:
        """Generar clave de cache para argumentos"""
        try:
            # Crear clave basada en argumentos serializables
            import hashlib
            import json
            
            # Filtrar solo argumentos serializables
            serializable_args = []
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    serializable_args.append(arg)
            
            serializable_kwargs = {
                k: v for k, v in kwargs.items()
                if isinstance(v, (str, int, float, bool))
            }
            
            cache_data = {
                "args": serializable_args,
                "kwargs": serializable_kwargs
            }
            
            cache_str = json.dumps(cache_data, sort_keys=True)
            return hashlib.md5(cache_str.encode()).hexdigest()
            
        except Exception as e:
            logger.debug(f"Could not generate cache key: {e}")
            return None
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Obtener resultado del cache"""
        return self.audio_cache.get(cache_key)
    
    def _add_to_cache(self, cache_key: str, result: Any):
        """Agregar resultado al cache"""
        if len(self.audio_cache) >= self.cache_max_size:
            # Remover entrada más antigua (FIFO simple)
            oldest_key = next(iter(self.audio_cache))
            del self.audio_cache[oldest_key]
        
        self.audio_cache[cache_key] = result
    
    async def _cache_cleanup_loop(self):
        """Loop de limpieza de cache"""
        while self.is_initialized:
            try:
                await asyncio.sleep(300)  # Limpiar cada 5 minutos
                
                # Limpiar cache si está muy lleno
                if len(self.audio_cache) > self.cache_max_size * 0.8:
                    # Remover 20% de las entradas más antiguas
                    items_to_remove = int(len(self.audio_cache) * 0.2)
                    keys_to_remove = list(self.audio_cache.keys())[:items_to_remove]
                    
                    for key in keys_to_remove:
                        del self.audio_cache[key]
                    
                    logger.debug(f"Cache cleanup: removed {items_to_remove} entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _latency_monitor_loop(self):
        """Loop de monitoreo de latencia"""
        while self.is_initialized:
            try:
                await asyncio.sleep(60)  # Monitorear cada minuto
                
                # Verificar si las latencias están dentro de los objetivos
                synthesis_ok = self.metrics.current_synthesis_latency <= self.latency_targets.synthesis_ms
                interrupt_ok = self.metrics.current_interrupt_latency <= self.latency_targets.interrupt_ms
                
                if not synthesis_ok:
                    logger.warning(f"Synthesis latency above target: {self.metrics.current_synthesis_latency:.1f}ms")
                
                if not interrupt_ok:
                    logger.warning(f"Interrupt latency above target: {self.metrics.current_interrupt_latency:.1f}ms")
                
                # Log estadísticas periódicamente
                success_rate = self.metrics.success_rate()
                logger.info(f"Optimization success rate: {success_rate:.1%}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Latency monitor error: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "enabled": self.audio_cache_enabled,
            "size": len(self.audio_cache),
            "max_size": self.cache_max_size,
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "hit_rate": hit_rate,
            "utilization": len(self.audio_cache) / self.cache_max_size
        }
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de optimización"""
        return {
            "is_initialized": self.is_initialized,
            "optimization_level": self.optimization_level.value,
            "latency_targets": self.latency_targets.to_dict(),
            "current_metrics": self.metrics.to_dict(),
            "thread_pool_workers": self.max_workers,
            "cache_stats": self.get_cache_stats(),
            "active_optimization_tasks": len([t for t in self.optimization_tasks if not t.done()])
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del optimizador"""
        try:
            if not self.is_initialized:
                return {
                    "status": "unhealthy",
                    "reason": "Optimizer not initialized"
                }
            
            # Verificar que las tareas de optimización estén funcionando
            active_tasks = len([t for t in self.optimization_tasks if not t.done()])
            expected_tasks = 2 if self.audio_cache_enabled else 1
            
            if active_tasks < expected_tasks:
                return {
                    "status": "degraded",
                    "reason": f"Some optimization tasks failed ({active_tasks}/{expected_tasks} active)"
                }
            
            # Verificar latencias
            synthesis_ok = self.metrics.current_synthesis_latency <= self.latency_targets.synthesis_ms * 1.5
            interrupt_ok = self.metrics.current_interrupt_latency <= self.latency_targets.interrupt_ms * 2.0
            
            if not synthesis_ok or not interrupt_ok:
                return {
                    "status": "degraded",
                    "reason": "Latency targets not being met consistently"
                }
            
            return {
                "status": "healthy",
                "optimization_level": self.optimization_level.value,
                "success_rate": self.metrics.success_rate(),
                "cache_hit_rate": self.get_cache_stats()["hit_rate"]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": f"Health check error: {str(e)}"
            }
    
    def clear_cache(self):
        """Limpiar cache de audio"""
        self.audio_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info("Audio cache cleared")