#!/usr/bin/env python3
"""
MIT-TTS-Streamer Runner

Script simple para ejecutar el servidor MIT-TTS-Streamer
"""

import sys
import asyncio
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar y ejecutar main
from src.main import main

if __name__ == "__main__":
    asyncio.run(main())