"""
Performance Monitor for MIT-TTS-Streamer

Monitor de rendimiento que rastrea métricas críticas del sistema
y proporciona alertas en tiempo real sobre problemas de rendimiento.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Niveles de alerta"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceAlert:
    """Alerta de rendimiento"""
    level: AlertLevel
    component: str
    message: str
    timestamp: float
    metric_value: float
    threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "component": self.component,
            "message": self.message,
            "timestamp": self.timestamp,
            "metric_value": self.metric_value,
            "threshold": self.threshold
        }


@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_available_mb: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    open_files: int = 0
    threads_count: int = 0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_available_mb": self.memory_available_mb,
            "disk_io_read_mb": self.disk_io_read_mb,
            "disk_io_write_mb": self.disk_io_write_mb,
            "network_sent_mb": self.network_sent_mb,
            "network_recv_mb": self.network_recv_mb,
            "open_files": self.open_files,
            "threads_count": self.threads_count
        }


@dataclass
class ApplicationMetrics:
    """Métricas de la aplicación"""
    active_sessions: int = 0
    queued_tasks: int = 0
    synthesis_requests_per_minute: float = 0.0
    average_synthesis_latency_ms: float = 0.0
    average_interrupt_latency_ms: float = 0.0
    websocket_connections: int = 0
    http_requests_per_minute: float = 0.0
    error_rate_percent: float = 0.0
    cache_hit_rate_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "active_sessions": self.active_sessions,
            "queued_tasks": self.queued_tasks,
            "synthesis_requests_per_minute": self.synthesis_requests_per_minute,
            "average_synthesis_latency_ms": self.average_synthesis_latency_ms,
            "average_interrupt_latency_ms": self.average_interrupt_latency_ms,
            "websocket_connections": self.websocket_connections,
            "http_requests_per_minute": self.http_requests_per_minute,
            "error_rate_percent": self.error_rate_percent,
            "cache_hit_rate_percent": self.cache_hit_rate_percent
        }


@dataclass
class PerformanceThresholds:
    """Umbrales de rendimiento"""
    # Umbrales del sistema
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 80.0
    memory_critical: float = 95.0
    
    # Umbrales de la aplicación
    synthesis_latency_warning_ms: float = 400.0
    synthesis_latency_critical_ms: float = 600.0
    interrupt_latency_warning_ms: float = 15.0
    interrupt_latency_critical_ms: float = 25.0
    error_rate_warning_percent: float = 5.0
    error_rate_critical_percent: float = 10.0
    queue_size_warning: int = 500
    queue_size_critical: int = 800
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "cpu_warning": self.cpu_warning,
            "cpu_critical": self.cpu_critical,
            "memory_warning": self.memory_warning,
            "memory_critical": self.memory_critical,
            "synthesis_latency_warning_ms": self.synthesis_latency_warning_ms,
            "synthesis_latency_critical_ms": self.synthesis_latency_critical_ms,
            "interrupt_latency_warning_ms": self.interrupt_latency_warning_ms,
            "interrupt_latency_critical_ms": self.interrupt_latency_critical_ms,
            "error_rate_warning_percent": self.error_rate_warning_percent,
            "error_rate_critical_percent": self.error_rate_critical_percent,
            "queue_size_warning": self.queue_size_warning,
            "queue_size_critical": self.queue_size_critical
        }


class PerformanceMonitor:
    """
    Monitor de rendimiento del sistema
    
    Características:
    - Monitoreo en tiempo real de métricas del sistema
    - Alertas automáticas por umbrales
    - Historial de métricas
    - Predicción de problemas de rendimiento
    - Integración con optimizador de latencia
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Configuración de monitoreo
        self.monitoring_interval = self.config.get("monitoring_interval", 5.0)  # segundos
        self.history_size = self.config.get("history_size", 1000)
        self.enable_system_monitoring = self.config.get("enable_system_monitoring", True)
        self.enable_predictions = self.config.get("enable_predictions", True)
        
        # Umbrales de rendimiento
        thresholds_config = self.config.get("thresholds", {})
        self.thresholds = PerformanceThresholds(**thresholds_config)
        
        # Métricas actuales
        self.current_system_metrics = SystemMetrics()
        self.current_app_metrics = ApplicationMetrics()
        
        # Historial de métricas (usando deque para eficiencia)
        self.system_metrics_history: deque = deque(maxlen=self.history_size)
        self.app_metrics_history: deque = deque(maxlen=self.history_size)
        
        # Alertas
        self.active_alerts: List[PerformanceAlert] = []
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        self.max_alerts = self.config.get("max_alerts", 100)
        
        # Estado
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.last_disk_io = None
        self.last_network_io = None
        
        # Lock para thread safety
        self._metrics_lock = threading.Lock()
        
        logger.info("PerformanceMonitor initialized")
    
    async def start_monitoring(self):
        """Iniciar monitoreo de rendimiento"""
        if self.is_monitoring:
            logger.warning("Performance monitoring is already running")
            return
        
        try:
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Performance monitoring started")
            
        except Exception as e:
            logger.error(f"Failed to start performance monitoring: {e}")
            self.is_monitoring = False
            raise
    
    async def stop_monitoring(self):
        """Detener monitoreo de rendimiento"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        while self.is_monitoring:
            try:
                # Recopilar métricas del sistema
                if self.enable_system_monitoring:
                    await self._collect_system_metrics()
                
                # Las métricas de la aplicación se actualizan externamente
                # mediante update_app_metrics()
                
                # Verificar umbrales y generar alertas
                await self._check_thresholds()
                
                # Guardar en historial
                self._save_to_history()
                
                # Predicciones (si están habilitadas)
                if self.enable_predictions:
                    await self._run_predictions()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self):
        """Recopilar métricas del sistema"""
        try:
            # Ejecutar en thread pool para no bloquear
            loop = asyncio.get_event_loop()
            metrics = await loop.run_in_executor(None, self._collect_system_metrics_sync)
            
            with self._metrics_lock:
                self.current_system_metrics = metrics
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_system_metrics_sync(self) -> SystemMetrics:
        """Recopilar métricas del sistema (síncrono)"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # I/O de disco
            disk_io = psutil.disk_io_counters()
            disk_read_mb = 0.0
            disk_write_mb = 0.0
            
            if disk_io and self.last_disk_io:
                read_bytes = disk_io.read_bytes - self.last_disk_io.read_bytes
                write_bytes = disk_io.write_bytes - self.last_disk_io.write_bytes
                disk_read_mb = read_bytes / (1024 * 1024)
                disk_write_mb = write_bytes / (1024 * 1024)
            
            if disk_io:
                self.last_disk_io = disk_io
            
            # I/O de red
            network_io = psutil.net_io_counters()
            network_sent_mb = 0.0
            network_recv_mb = 0.0
            
            if network_io and self.last_network_io:
                sent_bytes = network_io.bytes_sent - self.last_network_io.bytes_sent
                recv_bytes = network_io.bytes_recv - self.last_network_io.bytes_recv
                network_sent_mb = sent_bytes / (1024 * 1024)
                network_recv_mb = recv_bytes / (1024 * 1024)
            
            if network_io:
                self.last_network_io = network_io
            
            # Proceso actual
            process = psutil.Process()
            open_files = len(process.open_files())
            threads_count = process.num_threads()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                open_files=open_files,
                threads_count=threads_count
            )
            
        except Exception as e:
            logger.error(f"Error in sync metrics collection: {e}")
            return SystemMetrics()
    
    def update_app_metrics(self, metrics: ApplicationMetrics):
        """Actualizar métricas de la aplicación"""
        with self._metrics_lock:
            self.current_app_metrics = metrics
    
    async def _check_thresholds(self):
        """Verificar umbrales y generar alertas"""
        current_time = time.time()
        
        with self._metrics_lock:
            system_metrics = self.current_system_metrics
            app_metrics = self.current_app_metrics
        
        # Verificar umbrales del sistema
        if system_metrics.cpu_percent >= self.thresholds.cpu_critical:
            await self._create_alert(
                AlertLevel.CRITICAL, "system", 
                f"CPU usage critical: {system_metrics.cpu_percent:.1f}%",
                system_metrics.cpu_percent, self.thresholds.cpu_critical
            )
        elif system_metrics.cpu_percent >= self.thresholds.cpu_warning:
            await self._create_alert(
                AlertLevel.WARNING, "system",
                f"CPU usage high: {system_metrics.cpu_percent:.1f}%",
                system_metrics.cpu_percent, self.thresholds.cpu_warning
            )
        
        if system_metrics.memory_percent >= self.thresholds.memory_critical:
            await self._create_alert(
                AlertLevel.CRITICAL, "system",
                f"Memory usage critical: {system_metrics.memory_percent:.1f}%",
                system_metrics.memory_percent, self.thresholds.memory_critical
            )
        elif system_metrics.memory_percent >= self.thresholds.memory_warning:
            await self._create_alert(
                AlertLevel.WARNING, "system",
                f"Memory usage high: {system_metrics.memory_percent:.1f}%",
                system_metrics.memory_percent, self.thresholds.memory_warning
            )
        
        # Verificar umbrales de la aplicación
        if app_metrics.average_synthesis_latency_ms >= self.thresholds.synthesis_latency_critical_ms:
            await self._create_alert(
                AlertLevel.CRITICAL, "application",
                f"Synthesis latency critical: {app_metrics.average_synthesis_latency_ms:.1f}ms",
                app_metrics.average_synthesis_latency_ms, self.thresholds.synthesis_latency_critical_ms
            )
        elif app_metrics.average_synthesis_latency_ms >= self.thresholds.synthesis_latency_warning_ms:
            await self._create_alert(
                AlertLevel.WARNING, "application",
                f"Synthesis latency high: {app_metrics.average_synthesis_latency_ms:.1f}ms",
                app_metrics.average_synthesis_latency_ms, self.thresholds.synthesis_latency_warning_ms
            )
        
        if app_metrics.average_interrupt_latency_ms >= self.thresholds.interrupt_latency_critical_ms:
            await self._create_alert(
                AlertLevel.CRITICAL, "application",
                f"Interrupt latency critical: {app_metrics.average_interrupt_latency_ms:.1f}ms",
                app_metrics.average_interrupt_latency_ms, self.thresholds.interrupt_latency_critical_ms
            )
        elif app_metrics.average_interrupt_latency_ms >= self.thresholds.interrupt_latency_warning_ms:
            await self._create_alert(
                AlertLevel.WARNING, "application",
                f"Interrupt latency high: {app_metrics.average_interrupt_latency_ms:.1f}ms",
                app_metrics.average_interrupt_latency_ms, self.thresholds.interrupt_latency_warning_ms
            )
        
        if app_metrics.error_rate_percent >= self.thresholds.error_rate_critical_percent:
            await self._create_alert(
                AlertLevel.CRITICAL, "application",
                f"Error rate critical: {app_metrics.error_rate_percent:.1f}%",
                app_metrics.error_rate_percent, self.thresholds.error_rate_critical_percent
            )
        elif app_metrics.error_rate_percent >= self.thresholds.error_rate_warning_percent:
            await self._create_alert(
                AlertLevel.WARNING, "application",
                f"Error rate high: {app_metrics.error_rate_percent:.1f}%",
                app_metrics.error_rate_percent, self.thresholds.error_rate_warning_percent
            )
        
        if app_metrics.queued_tasks >= self.thresholds.queue_size_critical:
            await self._create_alert(
                AlertLevel.CRITICAL, "application",
                f"Queue size critical: {app_metrics.queued_tasks} tasks",
                app_metrics.queued_tasks, self.thresholds.queue_size_critical
            )
        elif app_metrics.queued_tasks >= self.thresholds.queue_size_warning:
            await self._create_alert(
                AlertLevel.WARNING, "application",
                f"Queue size high: {app_metrics.queued_tasks} tasks",
                app_metrics.queued_tasks, self.thresholds.queue_size_warning
            )
    
    async def _create_alert(self, level: AlertLevel, component: str, message: str, 
                          metric_value: float, threshold: float):
        """Crear nueva alerta"""
        alert = PerformanceAlert(
            level=level,
            component=component,
            message=message,
            timestamp=time.time(),
            metric_value=metric_value,
            threshold=threshold
        )
        
        # Evitar alertas duplicadas recientes (últimos 60 segundos)
        recent_alerts = [
            a for a in self.active_alerts 
            if a.component == component and a.message == message and 
               (alert.timestamp - a.timestamp) < 60
        ]
        
        if not recent_alerts:
            self.active_alerts.append(alert)
            
            # Mantener solo las alertas más recientes
            if len(self.active_alerts) > self.max_alerts:
                self.active_alerts = self.active_alerts[-self.max_alerts:]
            
            # Notificar callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
            
            # Log de la alerta
            log_func = logger.critical if level == AlertLevel.CRITICAL else logger.warning
            log_func(f"Performance alert: {message}")
    
    def _save_to_history(self):
        """Guardar métricas actuales al historial"""
        with self._metrics_lock:
            timestamp = time.time()
            
            # Agregar timestamp a las métricas
            system_entry = {
                "timestamp": timestamp,
                **self.current_system_metrics.to_dict()
            }
            app_entry = {
                "timestamp": timestamp,
                **self.current_app_metrics.to_dict()
            }
            
            self.system_metrics_history.append(system_entry)
            self.app_metrics_history.append(app_entry)
    
    async def _run_predictions(self):
        """Ejecutar predicciones de rendimiento"""
        try:
            # Predicciones simples basadas en tendencias
            if len(self.system_metrics_history) >= 10:
                await self._predict_system_issues()
            
            if len(self.app_metrics_history) >= 10:
                await self._predict_app_issues()
                
        except Exception as e:
            logger.error(f"Error in predictions: {e}")
    
    async def _predict_system_issues(self):
        """Predecir problemas del sistema"""
        # Obtener últimas 10 métricas
        recent_metrics = list(self.system_metrics_history)[-10:]
        
        # Calcular tendencia de CPU
        cpu_values = [m["cpu_percent"] for m in recent_metrics]
        if len(cpu_values) >= 5:
            cpu_trend = (cpu_values[-1] - cpu_values[0]) / len(cpu_values)
            if cpu_trend > 2.0 and cpu_values[-1] > 60:  # Incremento de 2% por medición
                await self._create_alert(
                    AlertLevel.WARNING, "prediction",
                    f"CPU usage trending upward: {cpu_trend:.1f}% per interval",
                    cpu_values[-1], 70.0
                )
        
        # Calcular tendencia de memoria
        memory_values = [m["memory_percent"] for m in recent_metrics]
        if len(memory_values) >= 5:
            memory_trend = (memory_values[-1] - memory_values[0]) / len(memory_values)
            if memory_trend > 1.0 and memory_values[-1] > 70:  # Incremento de 1% por medición
                await self._create_alert(
                    AlertLevel.WARNING, "prediction",
                    f"Memory usage trending upward: {memory_trend:.1f}% per interval",
                    memory_values[-1], 80.0
                )
    
    async def _predict_app_issues(self):
        """Predecir problemas de la aplicación"""
        # Obtener últimas 10 métricas
        recent_metrics = list(self.app_metrics_history)[-10:]
        
        # Calcular tendencia de latencia de síntesis
        latency_values = [m["average_synthesis_latency_ms"] for m in recent_metrics]
        if len(latency_values) >= 5:
            latency_trend = (latency_values[-1] - latency_values[0]) / len(latency_values)
            if latency_trend > 10.0 and latency_values[-1] > 200:  # Incremento de 10ms por medición
                await self._create_alert(
                    AlertLevel.WARNING, "prediction",
                    f"Synthesis latency trending upward: {latency_trend:.1f}ms per interval",
                    latency_values[-1], 300.0
                )
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Agregar callback para alertas"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Remover callback de alertas"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales"""
        with self._metrics_lock:
            return {
                "system": self.current_system_metrics.to_dict(),
                "application": self.current_app_metrics.to_dict(),
                "timestamp": time.time()
            }
    
    def get_metrics_history(self, minutes: int = 60) -> Dict[str, List[Dict[str, Any]]]:
        """Obtener historial de métricas"""
        cutoff_time = time.time() - (minutes * 60)
        
        system_history = [
            m for m in self.system_metrics_history 
            if m["timestamp"] >= cutoff_time
        ]
        app_history = [
            m for m in self.app_metrics_history 
            if m["timestamp"] >= cutoff_time
        ]
        
        return {
            "system": system_history,
            "application": app_history
        }
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Dict[str, Any]]:
        """Obtener alertas activas"""
        alerts = self.active_alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return [alert.to_dict() for alert in alerts]
    
    def clear_alerts(self, older_than_minutes: int = 60):
        """Limpiar alertas antiguas"""
        cutoff_time = time.time() - (older_than_minutes * 60)
        self.active_alerts = [
            alert for alert in self.active_alerts 
            if alert.timestamp >= cutoff_time
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen de rendimiento"""
        with self._metrics_lock:
            current_metrics = self.get_current_metrics()
        
        active_alerts_count = len(self.active_alerts)
        critical_alerts_count = len([a for a in self.active_alerts if a.level == AlertLevel.CRITICAL])
        
        return {
            "monitoring_active": self.is_monitoring,
            "current_metrics": current_metrics,
            "active_alerts": active_alerts_count,
            "critical_alerts": critical_alerts_count,
            "thresholds": self.thresholds.to_dict(),
            "history_size": {
                "system": len(self.system_metrics_history),
                "application": len(self.app_metrics_history)
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del monitor"""
        try:
            if not self.is_monitoring:
                return {
                    "status": "unhealthy",
                    "reason": "Performance monitoring not active"
                }
            
            # Verificar si hay alertas críticas
            critical_alerts = [a for a in self.active_alerts if a.level == AlertLevel.CRITICAL]
            if critical_alerts:
                return {
                    "status": "critical",
                    "reason": f"{len(critical_alerts)} critical performance alerts active",
                    "critical_alerts": len(critical_alerts)
                }
            
            # Verificar métricas básicas
            with self._metrics_lock:
                if (self.current_system_metrics.cpu_percent > 90 or 
                    self.current_system_metrics.memory_percent > 95):
                    return {
                        "status": "degraded",
                        "reason": "System resources critically low"
                    }
            
            return {
                "status": "healthy",
                "monitoring_interval": self.monitoring_interval,
                "active_alerts": len(self.active_alerts),
                "history_entries": len(self.system_metrics_history)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "reason": f"Health check error: {str(e)}"
            }