#!/usr/bin/env python3
"""
Script de prueba para MIT-TTS-Streamer
Ejecuta el servidor con uvicorn para pruebas
"""

import sys
import asyncio
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import uvicorn
    from src.core.config_manager import ConfigManager
    from src.server.http_server import create_http_app
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False
    print("uvicorn no está disponible. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn"])
    import uvicorn
    UVICORN_AVAILABLE = True

def main():
    """Ejecutar servidor de prueba"""
    if not UVICORN_AVAILABLE:
        print("Error: uvicorn no está disponible")
        return
    
    print("Iniciando servidor de prueba MIT-TTS-Streamer...")
    
    # Crear configuración
    config_manager = ConfigManager()
    
    # Crear aplicación FastAPI
    app = create_http_app(config_manager)
    
    if app is None:
        print("Error: No se pudo crear la aplicación FastAPI")
        return
    
    # Ejecutar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()