# 🚀 MIT-TTS-Streamer - Inicio Rápido

## Instalación y Ejecución Inmediata

### 1. Instalación Automática
```bash
# Navegar al directorio del proyecto
cd mit-tts-streamer

# Ejecutar script de instalación
chmod +x install.sh
./install.sh
```

### 2. Instalación Manual (si prefieres)
```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Crear directorios
mkdir -p logs data cache

# Copiar configuración
cp config/default.json config/local.json
```

### 3. Ejecutar el Servidor

#### Opción A: Script Simple (Recomendado)
```bash
# Ejecutar con script simple
python3 run.py

# Con opciones
python3 run.py --debug
python3 run.py --test-config
python3 run.py --help
```

#### Opción B: Como Módulo Python
```bash
# Desde el directorio del proyecto
python3 -m src.main

# Con debug
python3 -m src.main --debug
```

#### Opción C: Ejecución Directa
```bash
# Ejecutar archivo directamente
python3 src/main.py

# Con opciones
python3 src/main.py --debug --test-config
```

## 🎯 Estado Actual del Proyecto

### ✅ Funcionando
- ✅ **Sistema de configuración** completo con validación
- ✅ **Logging avanzado** con métricas de rendimiento
- ✅ **Estructura base** del proyecto
- ✅ **CLI completo** con opciones de configuración
- ✅ **Validación de configuración** automática
- ✅ **Múltiples formas de ejecución**

### 🚧 En Desarrollo
- 🚧 **Servidor HTTP REST** (próximo)
- 🚧 **Servidor WebSocket** (próximo)
- 🚧 **Motor TTS** con MeloTTS (próximo)
- 🚧 **Sistema de colas** con prioridades (próximo)
- 🚧 **Gestión de sesiones** multi-usuario (próximo)

## 📋 Comandos Útiles

### Configuración
```bash
# Ver ayuda completa
python3 run.py --help

# Probar configuración
python3 run.py --test-config

# Ejecutar con debug
python3 run.py --debug

# Cambiar puertos
python3 run.py --http-port 9080 --websocket-port 9081
```

### Desarrollo
```bash
# Modo desarrollo con recarga automática
python3 run.py --reload --debug

# Verificar código (si tienes las herramientas instaladas)
python3 -m flake8 src/ 2>/dev/null || echo "flake8 no instalado"
python3 -m black src/ 2>/dev/null || echo "black no instalado"
python3 -m mypy src/ 2>/dev/null || echo "mypy no instalado"
```

### Docker
```bash
# Construir imagen
docker build -t mit-tts-streamer .

# Ejecutar contenedor
docker run -p 8080:8080 -p 8081:8081 mit-tts-streamer

# Con docker-compose
docker-compose up
```

## 🔧 Configuración Personalizada

### Editar Configuración Local
```bash
# Editar configuración
nano config/local.json

# Ejemplo de cambios comunes:
{
  "server": {
    "host": "0.0.0.0",
    "http_port": 8080,
    "websocket_port": 8081
  },
  "tts": {
    "device": "cpu",  # o "cuda" si tienes GPU
    "default_language": "es",
    "preload_languages": ["es", "en"]
  },
  "logging": {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "console": true,
    "file": "logs/mit-tts-streamer.log"
  }
}
```

## 🐛 Solución de Problemas

### Error: ModuleNotFoundError
```bash
# Asegúrate de que las dependencias están instaladas
pip install -r requirements.txt

# Verifica el entorno virtual
which python3
pip list | grep fastapi
```

### Error: ImportError (relative imports)
```bash
# Usa el script run.py en lugar de ejecutar main.py directamente
python3 run.py

# O ejecuta como módulo
python3 -m src.main
```

### Error: Permission denied
```bash
# Dar permisos al script de instalación
chmod +x install.sh

# Crear directorios manualmente si es necesario
mkdir -p logs data cache
```

### Error: Config file not found
```bash
# Copiar configuración por defecto
cp config/default.json config/local.json

# O especificar ruta manualmente
python3 run.py --config config/default.json
```

## 📊 Verificar Funcionamiento

### Salida Esperada
```
🚀 Inicializando MIT-TTS-Streamer...
✅ Componentes básicos inicializados
⚠️ Nota: Algunos componentes aún no están implementados

============================================================
🎤 MIT-TTS-STREAMER v0.1.0
============================================================
🌐 HTTP REST API: http://0.0.0.0:8080 (pendiente)
🔌 WebSocket Server: ws://0.0.0.0:8081 (pendiente)
🧠 TTS Engine: melo (cpu) (pendiente)
🗣️ Idiomas: es, en
🎵 Formatos: wav, mp3, ogg, flac
⚡ Max Conexiones: 100
📊 Cola Máxima: 1000
============================================================
🚧 MODO DEMO - Componentes principales en desarrollo
📋 Estado: Configuración y logging funcionando
============================================================

🎤 Servidor iniciado en modo demo
📝 Presiona Ctrl+C para detener
```

## 🎯 Formas de Ejecutar

### 1. Script Simple (Más Fácil)
```bash
python3 run.py
```
✅ **Ventajas**: Más simple, maneja imports automáticamente  
❌ **Desventajas**: Ninguna

### 2. Como Módulo Python (Estándar)
```bash
python3 -m src.main
```
✅ **Ventajas**: Forma estándar de Python  
❌ **Desventajas**: Requiere estar en el directorio correcto

### 3. Ejecución Directa (Funciona)
```bash
python3 src/main.py
```
✅ **Ventajas**: Directo  
❌ **Desventajas**: Maneja imports internamente

## 🎯 Próximos Pasos

1. **Verificar instalación**: `python3 run.py --test-config`
2. **Ejecutar modo demo**: `python3 run.py`
3. **Personalizar configuración**: Editar `config/local.json`
4. **Seguir desarrollo**: Los próximos componentes se implementarán progresivamente

## 📞 Soporte

Si encuentras problemas:

1. **Verifica Python 3.8+**: `python3 --version`
2. **Verifica dependencias**: `pip list | grep -E "(fastapi|pydantic|rich|click)"`
3. **Revisa logs**: `tail -f logs/mit-tts-streamer.log`
4. **Modo debug**: `python3 run.py --debug`
5. **Prueba configuración**: `python3 run.py --test-config`

## 🚀 Comandos de Prueba Rápida

```bash
# Instalación completa
cd mit-tts-streamer && chmod +x install.sh && ./install.sh

# Prueba rápida
python3 run.py --test-config

# Ejecutar servidor
python3 run.py

# Con debug
python3 run.py --debug
```

¡El proyecto está funcionando correctamente en modo demo! 🎉