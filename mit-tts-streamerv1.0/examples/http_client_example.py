#!/usr/bin/env python3
"""
MIT-TTS-Streamer HTTP REST Client Example

Ejemplo de cliente para la API REST de MIT-TTS-Streamer.
Demuestra cómo usar todos los endpoints disponibles.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class TTSHTTPClient:
    """Cliente HTTP para MIT-TTS-Streamer API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MIT-TTS-Streamer-Client/0.1.0'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar salud del servidor"""
        response = self.session.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado detallado del sistema"""
        response = self.session.get(f"{self.base_url}/api/v1/status")
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento"""
        response = self.session.get(f"{self.base_url}/api/v1/metrics")
        response.raise_for_status()
        return response.json()
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        response = self.session.get(f"{self.base_url}/api/v1/config")
        response.raise_for_status()
        return response.json()
    
    def update_config(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar configuración"""
        response = self.session.post(
            f"{self.base_url}/api/v1/config",
            json=config_updates
        )
        response.raise_for_status()
        return response.json()
    
    def reload_config(self) -> Dict[str, Any]:
        """Recargar configuración desde archivo"""
        response = self.session.post(f"{self.base_url}/api/v1/config/reload")
        response.raise_for_status()
        return response.json()
    
    def save_config(self) -> Dict[str, Any]:
        """Guardar configuración actual"""
        response = self.session.post(f"{self.base_url}/api/v1/config/save")
        response.raise_for_status()
        return response.json()
    
    def get_voices(self) -> Dict[str, Any]:
        """Obtener voces disponibles"""
        response = self.session.get(f"{self.base_url}/api/v1/voices")
        response.raise_for_status()
        return response.json()
    
    def get_languages(self) -> Dict[str, Any]:
        """Obtener idiomas soportados"""
        response = self.session.get(f"{self.base_url}/api/v1/languages")
        response.raise_for_status()
        return response.json()
    
    def create_session(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nueva sesión TTS"""
        response = self.session.post(
            f"{self.base_url}/api/v1/sessions",
            json=config
        )
        response.raise_for_status()
        return response.json()
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Obtener información de sesión"""
        response = self.session.get(f"{self.base_url}/api/v1/sessions/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Cerrar sesión"""
        response = self.session.delete(f"{self.base_url}/api/v1/sessions/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def list_sessions(self) -> Dict[str, Any]:
        """Listar todas las sesiones"""
        response = self.session.get(f"{self.base_url}/api/v1/sessions")
        response.raise_for_status()
        return response.json()
    
    def interrupt_session(self, session_id: str) -> Dict[str, Any]:
        """Interrumpir sesión específica"""
        response = self.session.post(f"{self.base_url}/api/v1/interrupt/{session_id}")
        response.raise_for_status()
        return response.json()
    
    def interrupt_all(self) -> Dict[str, Any]:
        """Interrumpir todas las sesiones"""
        response = self.session.post(f"{self.base_url}/api/v1/interrupt/all")
        response.raise_for_status()
        return response.json()


def demo_basic_operations():
    """Demostración de operaciones básicas"""
    print("🚀 MIT-TTS-Streamer HTTP Client Demo")
    print("=" * 50)
    
    client = TTSHTTPClient()
    
    try:
        # 1. Health Check
        print("\n1. 🏥 Health Check")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Uptime: {health['uptime_seconds']:.1f}s")
        print(f"   Components: {health['components']}")
        
        # 2. System Status
        print("\n2. 📊 System Status")
        status = client.get_status()
        print(f"   Status: {status['status']}")
        print(f"   HTTP Port: {status['server']['http_port']}")
        print(f"   TTS Engine: {status['tts_engine']['engine']}")
        print(f"   Languages: {', '.join(status['tts_engine']['supported_languages'])}")
        
        # 3. Metrics
        print("\n3. 📈 Metrics")
        metrics = client.get_metrics()
        print(f"   Total Requests: {metrics['total_requests']}")
        print(f"   Average Latency: {metrics['average_latency_ms']:.2f}ms")
        print(f"   Memory Usage: {metrics['memory_usage_mb']:.1f}MB")
        print(f"   CPU Usage: {metrics['cpu_usage_percent']:.1f}%")
        
        # 4. Configuration
        print("\n4. ⚙️ Configuration")
        config = client.get_config()
        print(f"   TTS Device: {config['tts']['device']}")
        print(f"   Default Language: {config['tts']['default_language']}")
        print(f"   Audio Formats: {', '.join(config['audio']['supported_formats'])}")
        
        # 5. Voices and Languages
        print("\n5. 🗣️ Voices and Languages")
        voices = client.get_voices()
        print(f"   Available Languages: {len(voices)}")
        for lang in voices:
            print(f"     - {lang['name']} ({lang['code']}): {len(lang['speakers'])} voices")
        
        languages = client.get_languages()
        print(f"   Supported: {', '.join(languages['supported_languages'])}")
        print(f"   Preloaded: {', '.join(languages['preload_languages'])}")
        
        # 6. Session Management
        print("\n6. 👥 Session Management")
        
        # Crear sesión
        session_config = {
            "language": "es",
            "voice_id": 0,
            "format": "wav",
            "sample_rate": 22050,
            "speed": 1.0
        }
        
        session = client.create_session(session_config)
        session_id = session['session_id']
        print(f"   Created Session: {session_id}")
        
        # Obtener información de sesión
        session_info = client.get_session(session_id)
        print(f"   Session Active: {session_info['is_active']}")
        print(f"   Session Config: {session_info['config']}")
        
        # Listar sesiones
        sessions = client.list_sessions()
        print(f"   Total Sessions: {sessions['total']}")
        
        # Cerrar sesión
        result = client.delete_session(session_id)
        print(f"   Session Closed: {result['status']}")
        
        print("\n✅ Demo completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to MIT-TTS-Streamer server")
        print("   Make sure the server is running on http://localhost:8080")
        print("   Start with: python3 run.py")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_config_management():
    """Demostración de gestión de configuración"""
    print("\n🔧 Configuration Management Demo")
    print("=" * 40)
    
    client = TTSHTTPClient()
    
    try:
        # Obtener configuración actual
        print("1. Getting current configuration...")
        original_config = client.get_config()
        original_level = original_config['logging']['level']
        print(f"   Current log level: {original_level}")
        
        # Actualizar configuración
        print("2. Updating configuration...")
        updates = {
            "logging": {
                "level": "DEBUG" if original_level != "DEBUG" else "INFO"
            }
        }
        
        result = client.update_config(updates)
        print(f"   Update result: {result['status']}")
        
        # Verificar cambio
        new_config = client.get_config()
        new_level = new_config['logging']['level']
        print(f"   New log level: {new_level}")
        
        # Revertir cambio
        print("3. Reverting configuration...")
        revert_updates = {
            "logging": {
                "level": original_level
            }
        }
        
        client.update_config(revert_updates)
        print("   Configuration reverted")
        
        print("✅ Configuration management demo completed!")
        
    except Exception as e:
        print(f"❌ Error in config demo: {e}")


def demo_interruption_system():
    """Demostración del sistema de interrupciones"""
    print("\n⏹️ Interruption System Demo")
    print("=" * 35)
    
    client = TTSHTTPClient()
    
    try:
        # Crear sesión de prueba
        session_config = {
            "language": "es",
            "voice_id": 0,
            "format": "wav"
        }
        
        session = client.create_session(session_config)
        session_id = session['session_id']
        print(f"1. Created test session: {session_id}")
        
        # Simular interrupción de sesión específica
        print("2. Testing session interruption...")
        result = client.interrupt_session(session_id)
        print(f"   Interrupt result: {result['status']}")
        
        # Simular interrupción global
        print("3. Testing global interruption...")
        result = client.interrupt_all()
        print(f"   Global interrupt result: {result['status']}")
        
        # Limpiar
        client.delete_session(session_id)
        print("4. Cleaned up test session")
        
        print("✅ Interruption system demo completed!")
        
    except Exception as e:
        print(f"❌ Error in interruption demo: {e}")


def interactive_demo():
    """Demo interactivo"""
    print("\n🎮 Interactive Demo")
    print("=" * 25)
    
    client = TTSHTTPClient()
    
    while True:
        print("\nAvailable commands:")
        print("1. health    - Check server health")
        print("2. status    - Get system status")
        print("3. metrics   - Get performance metrics")
        print("4. config    - Show configuration")
        print("5. voices    - List available voices")
        print("6. sessions  - List active sessions")
        print("7. create    - Create new session")
        print("8. quit      - Exit demo")
        
        choice = input("\nEnter command (1-8): ").strip()
        
        try:
            if choice == "1" or choice.lower() == "health":
                health = client.health_check()
                print(f"Server Status: {health['status']}")
                print(f"Uptime: {health['uptime_seconds']:.1f} seconds")
                
            elif choice == "2" or choice.lower() == "status":
                status = client.get_status()
                print(json.dumps(status, indent=2))
                
            elif choice == "3" or choice.lower() == "metrics":
                metrics = client.get_metrics()
                print(f"Requests: {metrics['total_requests']}")
                print(f"Avg Latency: {metrics['average_latency_ms']:.2f}ms")
                print(f"Memory: {metrics['memory_usage_mb']:.1f}MB")
                
            elif choice == "4" or choice.lower() == "config":
                config = client.get_config()
                print("Current Configuration:")
                print(f"  TTS Engine: {config['tts']['engine']}")
                print(f"  Device: {config['tts']['device']}")
                print(f"  Languages: {', '.join(config['tts']['supported_languages'])}")
                
            elif choice == "5" or choice.lower() == "voices":
                voices = client.get_voices()
                print("Available Voices:")
                for lang in voices:
                    print(f"  {lang['name']} ({lang['code']}):")
                    for speaker in lang['speakers']:
                        print(f"    - {speaker['name']} ({speaker['gender']})")
                
            elif choice == "6" or choice.lower() == "sessions":
                sessions = client.list_sessions()
                print(f"Active Sessions: {sessions['total']}")
                
            elif choice == "7" or choice.lower() == "create":
                session = client.create_session({
                    "language": "es",
                    "voice_id": 0,
                    "format": "wav"
                })
                print(f"Created session: {session['session_id']}")
                
            elif choice == "8" or choice.lower() == "quit":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure it's running.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🎤 MIT-TTS-Streamer HTTP Client Examples")
    print("========================================")
    
    # Verificar si el servidor está disponible
    try:
        client = TTSHTTPClient()
        client.health_check()
        print("✅ Server is running and accessible")
    except:
        print("❌ Server is not accessible at http://localhost:8080")
        print("   Start the server with: python3 run.py")
        print("   Make sure FastAPI and uvicorn are installed:")
        print("   pip install fastapi uvicorn")
        exit(1)
    
    print("\nChoose demo type:")
    print("1. Basic operations demo")
    print("2. Configuration management demo")
    print("3. Interruption system demo")
    print("4. Interactive demo")
    print("5. Run all demos")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        demo_basic_operations()
    elif choice == "2":
        demo_config_management()
    elif choice == "3":
        demo_interruption_system()
    elif choice == "4":
        interactive_demo()
    elif choice == "5":
        demo_basic_operations()
        demo_config_management()
        demo_interruption_system()
    else:
        print("Invalid choice")