#!/usr/bin/env python3
"""
WebSocket Client Example for MIT-TTS-Streamer

Ejemplos de uso del servidor WebSocket para streaming de audio TTS en tiempo real.
Demuestra todas las funcionalidades principales:
- Conexión WebSocket
- Síntesis de texto con streaming
- Interrupciones inmediatas
- Configuración de sesión
- Manejo de errores
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any
import argparse

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketTTSClient:
    """Cliente WebSocket para MIT-TTS-Streamer"""
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library is required")
        
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.is_connected = False
        
        # Estadísticas
        self.messages_sent = 0
        self.messages_received = 0
        self.audio_chunks_received = 0
        self.total_audio_bytes = 0
    
    async def connect(self) -> bool:
        """
        Conectar al servidor WebSocket
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            logger.info(f"Connecting to {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            
            # Esperar mensaje de bienvenida
            welcome_msg = await self.websocket.recv()
            welcome_data = json.loads(welcome_msg)
            
            if welcome_data.get("type") == "config_updated":
                self.session_id = welcome_data.get("session_id")
                logger.info(f"Connected successfully! Session ID: {self.session_id}")
                return True
            else:
                logger.error(f"Unexpected welcome message: {welcome_data}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Desconectar del servidor"""
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from server")
    
    async def send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """
        Enviar mensaje al servidor
        
        Args:
            message_type: Tipo de mensaje
            data: Datos del mensaje
            
        Returns:
            True si se envió exitosamente
        """
        if not self.is_connected or not self.websocket:
            logger.error("Not connected to server")
            return False
        
        try:
            message = {
                "type": message_type,
                "data": data,
                "session_id": self.session_id,
                "timestamp": time.time()
            }
            
            await self.websocket.send(json.dumps(message))
            self.messages_sent += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def synthesize_text(self, text: str, priority: str = "normal") -> bool:
        """
        Solicitar síntesis de texto
        
        Args:
            text: Texto a sintetizar
            priority: Prioridad (normal, high, critical)
            
        Returns:
            True si se envió la solicitud
        """
        logger.info(f"Synthesizing text: '{text}' (priority: {priority})")
        
        return await self.send_message("synthesize", {
            "text": text,
            "priority": priority
        })
    
    async def interrupt_synthesis(self) -> bool:
        """
        Interrumpir síntesis actual
        
        Returns:
            True si se envió la interrupción
        """
        logger.info("Sending interrupt request...")
        return await self.send_message("interrupt", {})
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """
        Actualizar configuración de sesión
        
        Args:
            config: Nueva configuración
            
        Returns:
            True si se envió la actualización
        """
        logger.info(f"Updating config: {config}")
        return await self.send_message("config_update", {"config": config})
    
    async def ping(self) -> bool:
        """
        Enviar ping al servidor
        
        Returns:
            True si se envió el ping
        """
        return await self.send_message("ping", {})
    
    async def listen_for_messages(self):
        """Escuchar mensajes del servidor"""
        if not self.is_connected or not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                await self._handle_server_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Server connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
            self.is_connected = False
    
    async def _handle_server_message(self, raw_message: str):
        """
        Manejar mensaje del servidor
        
        Args:
            raw_message: Mensaje crudo del servidor
        """
        try:
            self.messages_received += 1
            message = json.loads(raw_message)
            msg_type = message.get("type")
            data = message.get("data", {})
            
            if msg_type == "synthesis_start":
                logger.info(f"Synthesis started for: '{data.get('text')}'")
                
            elif msg_type == "audio_chunk":
                chunk_index = data.get("chunk_index", 0)
                total_chunks = data.get("total_chunks", 0)
                audio_data = data.get("audio_data", "")
                
                self.audio_chunks_received += 1
                self.total_audio_bytes += len(audio_data) // 2  # Hex encoding
                
                logger.info(f"Received audio chunk {chunk_index + 1}/{total_chunks} "
                           f"({len(audio_data)//2} bytes)")
                
            elif msg_type == "synthesis_complete":
                synthesis_time = data.get("synthesis_time_ms", 0)
                total_chunks = data.get("total_chunks", 0)
                audio_bytes = data.get("audio_bytes", 0)
                
                logger.info(f"Synthesis completed! "
                           f"Time: {synthesis_time:.1f}ms, "
                           f"Chunks: {total_chunks}, "
                           f"Audio bytes: {audio_bytes}")
                
            elif msg_type == "interrupted":
                interrupted_tasks = data.get("interrupted_tasks", 0)
                latency_ms = data.get("latency_ms", 0)
                
                logger.info(f"Synthesis interrupted! "
                           f"Tasks: {interrupted_tasks}, "
                           f"Latency: {latency_ms:.1f}ms")
                
            elif msg_type == "config_updated":
                logger.info(f"Config updated: {data}")
                
            elif msg_type == "pong":
                original_timestamp = data.get("timestamp", 0)
                latency = (time.time() - original_timestamp) * 1000
                logger.info(f"Pong received (latency: {latency:.1f}ms)")
                
            elif msg_type == "error":
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Server error: {error_msg}")
                
            elif msg_type == "synthesis_error":
                error_msg = data.get("error", "Unknown synthesis error")
                task_id = data.get("task_id", "unknown")
                logger.error(f"Synthesis error (task {task_id}): {error_msg}")
                
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from server: {e}")
        except Exception as e:
            logger.error(f"Error handling server message: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cliente"""
        return {
            "is_connected": self.is_connected,
            "session_id": self.session_id,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "audio_chunks_received": self.audio_chunks_received,
            "total_audio_bytes": self.total_audio_bytes
        }


async def demo_basic_synthesis(client: WebSocketTTSClient):
    """Demo básico de síntesis"""
    print("\n=== Demo: Síntesis Básica ===")
    
    # Síntesis simple
    await client.synthesize_text("Hola, este es un ejemplo de síntesis de voz.")
    await asyncio.sleep(2)
    
    # Síntesis con prioridad alta
    await client.synthesize_text("Este mensaje tiene prioridad alta.", "high")
    await asyncio.sleep(2)


async def demo_interruption(client: WebSocketTTSClient):
    """Demo de interrupciones"""
    print("\n=== Demo: Interrupciones ===")
    
    # Iniciar síntesis larga
    await client.synthesize_text(
        "Este es un texto muy largo que será interrumpido antes de completarse. "
        "Normalmente tomaría varios segundos en procesarse completamente, "
        "pero vamos a interrumpirlo para demostrar la funcionalidad de interrupción inmediata."
    )
    
    # Esperar un poco y luego interrumpir
    await asyncio.sleep(0.5)
    await client.interrupt_synthesis()
    await asyncio.sleep(1)


async def demo_config_update(client: WebSocketTTSClient):
    """Demo de actualización de configuración"""
    print("\n=== Demo: Actualización de Configuración ===")
    
    # Actualizar configuración
    new_config = {
        "language": "en",
        "voice_id": 1,
        "speed": 1.2,
        "format": "mp3"
    }
    
    await client.update_config(new_config)
    await asyncio.sleep(1)
    
    # Síntesis con nueva configuración
    await client.synthesize_text("This text uses the updated configuration.")
    await asyncio.sleep(2)


async def demo_ping_pong(client: WebSocketTTSClient):
    """Demo de ping/pong"""
    print("\n=== Demo: Ping/Pong ===")
    
    for i in range(3):
        await client.ping()
        await asyncio.sleep(0.5)


async def demo_concurrent_synthesis(client: WebSocketTTSClient):
    """Demo de síntesis concurrente"""
    print("\n=== Demo: Síntesis Concurrente ===")
    
    # Enviar múltiples solicitudes
    texts = [
        "Primera síntesis concurrente.",
        "Segunda síntesis concurrente.",
        "Tercera síntesis concurrente con prioridad alta."
    ]
    
    for i, text in enumerate(texts):
        priority = "high" if i == 2 else "normal"
        await client.synthesize_text(text, priority)
        await asyncio.sleep(0.1)  # Pequeña pausa entre solicitudes
    
    await asyncio.sleep(3)


async def run_interactive_mode(client: WebSocketTTSClient):
    """Modo interactivo"""
    print("\n=== Modo Interactivo ===")
    print("Comandos disponibles:")
    print("  text <mensaje>     - Sintetizar texto")
    print("  interrupt          - Interrumpir síntesis")
    print("  config <json>      - Actualizar configuración")
    print("  ping               - Enviar ping")
    print("  stats              - Mostrar estadísticas")
    print("  quit               - Salir")
    print()
    
    while client.is_connected:
        try:
            command = input(">>> ").strip()
            
            if not command:
                continue
            
            if command.startswith("text "):
                text = command[5:]
                await client.synthesize_text(text)
                
            elif command == "interrupt":
                await client.interrupt_synthesis()
                
            elif command.startswith("config "):
                try:
                    config_json = command[7:]
                    config = json.loads(config_json)
                    await client.update_config(config)
                except json.JSONDecodeError:
                    print("Error: Invalid JSON format")
                    
            elif command == "ping":
                await client.ping()
                
            elif command == "stats":
                stats = client.get_stats()
                print(f"Client stats: {json.dumps(stats, indent=2)}")
                
            elif command == "quit":
                break
                
            else:
                print("Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            break
        except EOFError:
            break


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="WebSocket TTS Client Example")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8001, help="Server port")
    parser.add_argument("--mode", choices=["demo", "interactive"], default="demo",
                       help="Run mode")
    
    args = parser.parse_args()
    
    if not WEBSOCKETS_AVAILABLE:
        print("Error: websockets library is required")
        print("Install with: pip install websockets")
        return
    
    # Crear cliente
    client = WebSocketTTSClient(args.host, args.port)
    
    try:
        # Conectar
        if not await client.connect():
            print("Failed to connect to server")
            return
        
        # Crear tarea para escuchar mensajes
        listen_task = asyncio.create_task(client.listen_for_messages())
        
        if args.mode == "demo":
            # Ejecutar demos
            await demo_basic_synthesis(client)
            await demo_interruption(client)
            await demo_config_update(client)
            await demo_ping_pong(client)
            await demo_concurrent_synthesis(client)
            
            # Mostrar estadísticas finales
            print("\n=== Estadísticas Finales ===")
            stats = client.get_stats()
            print(json.dumps(stats, indent=2))
            
        else:
            # Modo interactivo
            await run_interactive_mode(client)
        
        # Cancelar tarea de escucha
        listen_task.cancel()
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Desconectar
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())