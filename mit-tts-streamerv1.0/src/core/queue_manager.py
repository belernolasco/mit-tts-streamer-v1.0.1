"""
Priority Queue Manager for MIT-TTS-Streamer

Sistema de colas con prioridades para gestión de tareas TTS con soporte
para interrupciones inmediatas y procesamiento de baja latencia.
"""

import asyncio
import heapq
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, Callable, Any, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Niveles de prioridad para tareas TTS"""
    CRITICAL = 0  # Interrupciones inmediatas, comandos de emergencia
    HIGH = 1      # Respuestas urgentes, alertas importantes
    NORMAL = 2    # Conversación regular, respuestas estándar


@dataclass
class TTSTask:
    """Tarea de síntesis TTS con prioridad"""
    priority: Priority
    text: str
    session_id: str
    config: Dict[str, Any]
    callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __lt__(self, other):
        """Comparación para heap - prioridad más baja = más urgente"""
        if self.priority != other.priority:
            return self.priority < other.priority
        # Si tienen la misma prioridad, FIFO por tiempo de creación
        return self.created_at < other.created_at
    
    def __eq__(self, other):
        return self.task_id == other.task_id
    
    def age_seconds(self) -> float:
        """Edad de la tarea en segundos"""
        return time.time() - self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir tarea a diccionario para logging/debugging"""
        return {
            "task_id": self.task_id,
            "priority": self.priority.name,
            "session_id": self.session_id,
            "text_preview": self.text[:50] + "..." if len(self.text) > 50 else self.text,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "age_seconds": self.age_seconds(),
            "config": self.config
        }


class QueueMetrics:
    """Métricas de la cola de prioridades"""
    
    def __init__(self):
        self.total_enqueued = 0
        self.total_processed = 0
        self.total_interrupted = 0
        self.total_expired = 0
        self.processing_times = []
        self.queue_wait_times = []
        self.priority_counts = {p: 0 for p in Priority}
        
    def record_enqueue(self, priority: Priority):
        """Registrar tarea encolada"""
        self.total_enqueued += 1
        self.priority_counts[priority] += 1
    
    def record_processed(self, task: TTSTask, processing_time: float):
        """Registrar tarea procesada"""
        self.total_processed += 1
        self.processing_times.append(processing_time)
        self.queue_wait_times.append(task.age_seconds())
        
        # Mantener solo las últimas 1000 métricas
        if len(self.processing_times) > 1000:
            self.processing_times = self.processing_times[-1000:]
        if len(self.queue_wait_times) > 1000:
            self.queue_wait_times = self.queue_wait_times[-1000:]
    
    def record_interrupted(self):
        """Registrar tarea interrumpida"""
        self.total_interrupted += 1
    
    def record_expired(self):
        """Registrar tarea expirada"""
        self.total_expired += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la cola"""
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times else 0.0
        )
        
        avg_wait_time = (
            sum(self.queue_wait_times) / len(self.queue_wait_times)
            if self.queue_wait_times else 0.0
        )
        
        return {
            "total_enqueued": self.total_enqueued,
            "total_processed": self.total_processed,
            "total_interrupted": self.total_interrupted,
            "total_expired": self.total_expired,
            "average_processing_time_ms": avg_processing_time * 1000,
            "average_wait_time_ms": avg_wait_time * 1000,
            "priority_distribution": {p.name: count for p, count in self.priority_counts.items()},
            "success_rate": (
                self.total_processed / self.total_enqueued * 100
                if self.total_enqueued > 0 else 0.0
            )
        }


class PriorityQueueManager:
    """
    Gestor de cola de prioridades para tareas TTS
    
    Características:
    - Prioridades: CRITICAL, HIGH, NORMAL
    - Interrupciones inmediatas para prioridades altas
    - Métricas de rendimiento
    - Limpieza automática de tareas expiradas
    - Soporte para múltiples workers
    """
    
    def __init__(self, max_size: int = 1000, max_task_age: float = 300.0):
        self.max_size = max_size
        self.max_task_age = max_task_age  # Máximo tiempo de vida de una tarea (segundos)
        
        # Cola de prioridades (heap)
        self.queue: List[TTSTask] = []
        self.queue_lock = asyncio.Lock()
        
        # Tarea actualmente en procesamiento
        self.current_task: Optional[TTSTask] = None
        self.current_process: Optional[asyncio.Task] = None
        self.processing_lock = asyncio.Lock()
        
        # Métricas
        self.metrics = QueueMetrics()
        
        # Control de estado
        self.is_running = True
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Eventos para coordinación
        self.task_available = asyncio.Event()
        self.shutdown_event = asyncio.Event()
        
        logger.info(f"PriorityQueueManager initialized - max_size: {max_size}, max_age: {max_task_age}s")
    
    async def start(self):
        """Iniciar el gestor de colas"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_tasks())
            logger.info("PriorityQueueManager started")
    
    async def stop(self):
        """Detener el gestor de colas"""
        self.is_running = False
        self.shutdown_event.set()
        
        # Cancelar tarea de limpieza
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Interrumpir tarea actual
        await self._interrupt_current_task("system_shutdown")
        
        # Limpiar cola
        async with self.queue_lock:
            self.queue.clear()
        
        logger.info("PriorityQueueManager stopped")
    
    async def enqueue(self, task: TTSTask) -> bool:
        """
        Encolar una tarea TTS
        
        Args:
            task: Tarea TTS a encolar
            
        Returns:
            True si se encoló exitosamente, False si la cola está llena
        """
        if not self.is_running:
            logger.warning("Cannot enqueue task - queue manager is stopped")
            return False
        
        async with self.queue_lock:
            # Verificar si la cola está llena
            if len(self.queue) >= self.max_size:
                logger.warning(f"Queue is full ({len(self.queue)}/{self.max_size})")
                return False
            
            # Si es prioridad crítica o alta, verificar si debe interrumpir
            if (task.priority <= Priority.HIGH and 
                self.current_task and 
                task.priority < self.current_task.priority):
                
                logger.info(f"High priority task {task.task_id} interrupting current task")
                await self._interrupt_current_task("priority_override")
            
            # Agregar a la cola
            heapq.heappush(self.queue, task)
            self.metrics.record_enqueue(task.priority)
            
            # Notificar que hay una tarea disponible
            self.task_available.set()
            
            logger.debug(f"Task enqueued: {task.task_id} (priority: {task.priority.name}, queue_size: {len(self.queue)})")
            return True
    
    async def dequeue(self) -> Optional[TTSTask]:
        """
        Desencolar la tarea de mayor prioridad
        
        Returns:
            Tarea TTS o None si la cola está vacía
        """
        async with self.queue_lock:
            if not self.queue:
                return None
            
            task = heapq.heappop(self.queue)
            logger.debug(f"Task dequeued: {task.task_id} (priority: {task.priority.name}, queue_size: {len(self.queue)})")
            return task
    
    async def wait_for_task(self, timeout: Optional[float] = None) -> Optional[TTSTask]:
        """
        Esperar por una tarea disponible
        
        Args:
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Tarea TTS o None si timeout
        """
        try:
            await asyncio.wait_for(self.task_available.wait(), timeout=timeout)
            task = await self.dequeue()
            
            # Si no hay más tareas, limpiar el evento
            async with self.queue_lock:
                if not self.queue:
                    self.task_available.clear()
            
            return task
            
        except asyncio.TimeoutError:
            return None
    
    async def interrupt_session(self, session_id: str, reason: str = "user_request") -> int:
        """
        Interrumpir todas las tareas de una sesión específica
        
        Args:
            session_id: ID de la sesión a interrumpir
            reason: Razón de la interrupción
            
        Returns:
            Número de tareas interrumpidas
        """
        interrupted_count = 0
        
        # Interrumpir tarea actual si pertenece a la sesión
        if (self.current_task and 
            self.current_task.session_id == session_id):
            await self._interrupt_current_task(reason)
            interrupted_count += 1
        
        # Remover tareas de la cola que pertenezcan a la sesión
        async with self.queue_lock:
            remaining_tasks = []
            for task in self.queue:
                if task.session_id == session_id:
                    interrupted_count += 1
                    self.metrics.record_interrupted()
                    logger.debug(f"Removed task {task.task_id} from queue (session interrupt)")
                else:
                    remaining_tasks.append(task)
            
            # Reconstruir heap
            self.queue = remaining_tasks
            heapq.heapify(self.queue)
        
        if interrupted_count > 0:
            logger.info(f"Interrupted {interrupted_count} tasks for session {session_id} (reason: {reason})")
        
        return interrupted_count
    
    async def interrupt_all(self, reason: str = "global_interrupt") -> int:
        """
        Interrumpir todas las tareas
        
        Args:
            reason: Razón de la interrupción
            
        Returns:
            Número de tareas interrumpidas
        """
        interrupted_count = 0
        
        # Interrumpir tarea actual
        if self.current_task:
            await self._interrupt_current_task(reason)
            interrupted_count += 1
        
        # Limpiar toda la cola
        async with self.queue_lock:
            interrupted_count += len(self.queue)
            for _ in range(len(self.queue)):
                self.metrics.record_interrupted()
            self.queue.clear()
        
        logger.info(f"Interrupted all tasks ({interrupted_count} total) - reason: {reason}")
        return interrupted_count
    
    async def set_current_task(self, task: TTSTask, process: asyncio.Task):
        """
        Establecer la tarea actualmente en procesamiento
        
        Args:
            task: Tarea TTS
            process: Task asyncio que procesa la tarea
        """
        async with self.processing_lock:
            self.current_task = task
            self.current_process = process
            logger.debug(f"Current task set: {task.task_id}")
    
    async def clear_current_task(self):
        """Limpiar la tarea actual"""
        async with self.processing_lock:
            if self.current_task:
                logger.debug(f"Current task cleared: {self.current_task.task_id}")
            self.current_task = None
            self.current_process = None
    
    async def _interrupt_current_task(self, reason: str):
        """Interrumpir la tarea actualmente en procesamiento"""
        async with self.processing_lock:
            if self.current_process and not self.current_process.done():
                self.current_process.cancel()
                self.metrics.record_interrupted()
                
                if self.current_task:
                    logger.info(f"Interrupted current task {self.current_task.task_id} - reason: {reason}")
                
                try:
                    await self.current_process
                except asyncio.CancelledError:
                    pass
            
            self.current_task = None
            self.current_process = None
    
    async def _cleanup_expired_tasks(self):
        """Tarea de limpieza de tareas expiradas"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Limpiar cada 30 segundos
                
                current_time = time.time()
                expired_count = 0
                
                async with self.queue_lock:
                    remaining_tasks = []
                    for task in self.queue:
                        if current_time - task.created_at > self.max_task_age:
                            expired_count += 1
                            self.metrics.record_expired()
                            logger.debug(f"Expired task removed: {task.task_id} (age: {task.age_seconds():.1f}s)")
                        else:
                            remaining_tasks.append(task)
                    
                    if expired_count > 0:
                        self.queue = remaining_tasks
                        heapq.heapify(self.queue)
                        logger.info(f"Cleaned up {expired_count} expired tasks")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la cola"""
        current_task_info = None
        if self.current_task:
            current_task_info = self.current_task.to_dict()
        
        queue_tasks = []
        for task in self.queue[:10]:  # Solo las primeras 10 para evitar overhead
            queue_tasks.append(task.to_dict())
        
        return {
            "is_running": self.is_running,
            "queue_size": len(self.queue),
            "max_size": self.max_size,
            "current_task": current_task_info,
            "queue_preview": queue_tasks,
            "metrics": self.metrics.get_stats()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento"""
        return self.metrics.get_stats()
    
    async def clear_queue(self):
        """Limpiar toda la cola (para shutdown)"""
        async with self.queue_lock:
            cleared_count = len(self.queue)
            self.queue.clear()
            if cleared_count > 0:
                logger.info(f"Cleared {cleared_count} tasks from queue")