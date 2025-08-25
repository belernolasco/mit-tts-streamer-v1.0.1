# 📦 MIT-TTS-Streamer - Guía de Instalación

## 🚀 Instalación Rápida (Recomendada)

### Opción 1: Script Automático
```bash
cd mit-tts-streamer
chmod +x install.sh
./install.sh
```

### Opción 2: Instalación Manual Básica
```bash
cd mit-tts-streamer

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias mínimas
pip install --upgrade pip
pip install pydantic click rich python-json-logger

# Probar funcionamiento
python3 run.py --test-config
```

## 📋 Dependencias por Categoría

### 🔧 Dependencias Básicas (Mínimas para funcionar)
```bash
pip install pydantic==2.5.0          # Validación de configuración
pip install click==8.1.7             # CLI interface
pip install rich==13.7.0             # Output colorido
pip install python-json-logger==2.0.7 # Logging estructurado
```

### 🌐 Dependencias de Servidor (Para funcionalidad completa)
```bash
pip install fastapi==0.104.1         # HTTP REST API
pip install uvicorn[standard]==0.24.0 # Servidor ASGI
pip install websockets==12.0         # WebSocket server
pip install python-multipart==0.0.6  # File uploads
pip install aiofiles==23.2.1         # Async file operations
```

### 🎵 Dependencias de Audio y TTS
```bash
pip install numpy==1.24.3            # Operaciones numéricas
pip install soundfile==0.12.1        # Procesamiento de audio
pip install librosa==0.10.1          # Análisis de audio
pip install melo-tts==0.1.1          # Motor TTS
pip install pydub==0.25.1            # Conversión de formatos
```

### 🧪 Dependencias de Desarrollo (Opcionales)
```bash
pip install pytest==7.4.3            # Testing
pip install pytest-asyncio==0.21.1   # Async testing
pip install pytest-cov==4.1.0        # Coverage
pip install black==23.11.0           # Code formatting
pip install flake8==6.1.0            # Linting
pip install mypy==1.7.1              # Type checking
```

## 🎯 Instalación Paso a Paso

### 1. Verificar Requisitos del Sistema
```bash
# Python 3.8 o superior
python3 --version

# pip actualizado
python3 -m pip --version
```

### 2. Clonar/Descargar el Proyecto
```bash
# Si tienes git
git clone <repository-url>
cd mit-tts-streamer

# O descargar y extraer el ZIP
cd mit-tts-streamer
```

### 3. Crear Entorno Virtual (Recomendado)
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Verificar activación
which python3  # Debe mostrar la ruta del venv
```

### 4. Instalar Dependencias

#### Para uso básico (solo configuración):
```bash
pip install --upgrade pip
pip install pydantic click rich python-json-logger
```

#### Para funcionalidad completa:
```bash
pip install -r requirements.txt
```

### 5. Crear Directorios Necesarios
```bash
mkdir -p logs data cache
```

### 6. Configurar el Proyecto
```bash
# Copiar configuración por defecto
cp config/default.json config/local.json

# Editar configuración si es necesario
nano config/local.json  # o tu editor preferido
```

### 7. Probar la Instalación
```bash
# Probar configuración
python3 run.py --test-config

# Si funciona, ejecutar servidor
python3 run.py
```

## 🔍 Verificación de Instalación

### Comando de Verificación Completa
```bash
python3 -c "
try:
    import pydantic
    print('✅ pydantic: OK')
except ImportError:
    print('❌ pydantic: FALTA')

try:
    import click
    print('✅ click: OK')
except ImportError:
    print('❌ click: FALTA')

try:
    import rich
    print('✅ rich: OK')
except ImportError:
    print('❌ rich: FALTA')

try:
    import pythonjsonlogger
    print('✅ python-json-logger: OK')
except ImportError:
    print('❌ python-json-logger: FALTA')

print('\\n🎯 Dependencias básicas verificadas')
"
```

### Verificación del Proyecto
```bash
# Probar importación del proyecto
python3 -c "from src.core.config_manager import ConfigManager; print('✅ Proyecto importa correctamente')"

# Probar configuración
python3 run.py --test-config

# Probar ejecución
python3 run.py --help
```

## 🐛 Solución de Problemas Comunes

### Error: `ModuleNotFoundError: No module named 'pydantic'`
```bash
pip install pydantic==2.5.0
```

### Error: `ModuleNotFoundError: No module named 'pydantic_settings'`
```bash
# Esta dependencia es opcional, pero si quieres instalarla:
pip install pydantic-settings==2.1.0
```

### Error: `ModuleNotFoundError: No module named 'rich'`
```bash
pip install rich==13.7.0
```

### Error: `ModuleNotFoundError: No module named 'click'`
```bash
pip install click==8.1.7
```

### Error: `ModuleNotFoundError: No module named 'pythonjsonlogger'`
```bash
pip install python-json-logger==2.0.7
```

### Error: `Permission denied` en install.sh
```bash
chmod +x install.sh
./install.sh
```

### Error: `Config file not found`
```bash
# Copiar configuración por defecto
cp config/default.json config/local.json
```

### Error: `Cannot create directory`
```bash
# Crear directorios manualmente
mkdir -p logs data cache
```

## 🌍 Instalación en Diferentes Sistemas

### Ubuntu/Debian
```bash
# Instalar dependencias del sistema
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Continuar con instalación normal
cd mit-tts-streamer
python3 -m venv venv
source venv/bin/activate
pip install pydantic click rich python-json-logger
```

### CentOS/RHEL/Fedora
```bash
# Instalar dependencias del sistema
sudo dnf install python3 python3-pip

# Continuar con instalación normal
cd mit-tts-streamer
python3 -m venv venv
source venv/bin/activate
pip install pydantic click rich python-json-logger
```

### macOS
```bash
# Con Homebrew
brew install python3

# Continuar con instalación normal
cd mit-tts-streamer
python3 -m venv venv
source venv/bin/activate
pip install pydantic click rich python-json-logger
```

### Windows
```cmd
# Desde PowerShell o CMD
cd mit-tts-streamer
python -m venv venv
venv\Scripts\activate
pip install pydantic click rich python-json-logger
```

## 🐳 Instalación con Docker

### Opción 1: Docker simple
```bash
cd mit-tts-streamer
docker build -t mit-tts-streamer .
docker run -p 8080:8080 -p 8081:8081 mit-tts-streamer
```

### Opción 2: Docker Compose
```bash
cd mit-tts-streamer
docker-compose up
```

## ✅ Comandos de Prueba Final

### Después de la instalación, ejecuta estos comandos:
```bash
# 1. Verificar configuración
python3 run.py --test-config

# 2. Ver ayuda
python3 run.py --help

# 3. Ejecutar en modo debug
python3 run.py --debug

# 4. Ejecutar servidor normal
python3 run.py
```

### Salida esperada del test de configuración:
```
🔧 Probando configuración...
✅ Configuración válida

📋 Resumen de configuración:
  • Host: 0.0.0.0
  • Puerto HTTP: 8080
  • Puerto WebSocket: 8081
  • Motor TTS: melo
  • Dispositivo: cpu
  • Idiomas: es, en
  • Nivel de log: INFO
```

## 📞 Soporte

Si tienes problemas con la instalación:

1. **Verifica Python**: `python3 --version` (debe ser 3.8+)
2. **Verifica pip**: `pip --version`
3. **Instala dependencias básicas**: `pip install pydantic click rich python-json-logger`
4. **Prueba el proyecto**: `python3 run.py --test-config`
5. **Revisa logs**: `tail -f logs/mit-tts-streamer.log`

¡Una vez instalado correctamente, el proyecto debería funcionar sin problemas! 🎉