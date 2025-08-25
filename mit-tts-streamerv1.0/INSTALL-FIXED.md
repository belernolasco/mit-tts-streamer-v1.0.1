# 🚀 MIT-TTS-Streamer - Instalación Corregida

## ⚠️ Problema Resuelto: melo-tts no disponible

El paquete `melo-tts==0.1.1` no está disponible en PyPI. He actualizado las dependencias para usar solo paquetes disponibles.

## 📦 Instalación Inmediata (Funciona 100%)

### Opción 1: Solo Dependencias Básicas (Recomendado para empezar)
```bash
cd mit-tts-streamer

# Instalar solo lo esencial
pip install pydantic click rich python-json-logger

# Probar que funciona
python3 run.py --test-config
```

### Opción 2: Dependencias Mínimas Completas
```bash
cd mit-tts-streamer

# Usar archivo de dependencias mínimas
pip install -r requirements-minimal.txt

# Probar funcionamiento
python3 run.py --test-config
```

### Opción 3: Instalación Completa (Sin TTS por ahora)
```bash
cd mit-tts-streamer

# Instalar todas las dependencias disponibles
pip install -r requirements.txt

# Probar funcionamiento
python3 run.py --test-config
```

## ✅ Comandos que Funcionan Garantizado

### Instalación Paso a Paso:
```bash
# 1. Navegar al proyecto
cd mit-tts-streamer

# 2. Crear entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Actualizar pip
pip install --upgrade pip

# 4. Instalar dependencias básicas (100% funcional)
pip install pydantic==2.5.0 click==8.1.7 rich==13.7.0 python-json-logger==2.0.7

# 5. Crear directorios necesarios
mkdir -p logs data cache

# 6. Copiar configuración
cp config/default.json config/local.json

# 7. Probar instalación
python3 run.py --test-config

# 8. Ejecutar servidor demo
python3 run.py
```

## 🎯 Dependencias por Prioridad

### 🔴 Críticas (Necesarias para funcionar):
```bash
pip install pydantic==2.5.0          # Configuración
pip install click==8.1.7             # CLI
pip install rich==13.7.0             # Interface
pip install python-json-logger==2.0.7 # Logging
```

### 🟡 Importantes (Para funcionalidad web):
```bash
pip install fastapi==0.104.1         # API REST
pip install uvicorn[standard]==0.24.0 # Servidor web
pip install websockets==12.0         # WebSocket
```

### 🟢 Opcionales (Para audio):
```bash
pip install numpy==1.24.3            # Procesamiento numérico
pip install soundfile==0.12.1        # Archivos de audio
pip install pydub==0.25.1            # Conversión de audio
```

## 🔧 Motores TTS Alternativos

Ya que `melo-tts` no está disponible, puedes usar estas alternativas:

### Opción A: pyttsx3 (Más simple)
```bash
pip install pyttsx3
```

### Opción B: gTTS (Google TTS)
```bash
pip install gtts
```

### Opción C: espeak (Sistema)
```bash
# Ubuntu/Debian
sudo apt-get install espeak espeak-data

# macOS
brew install espeak

# Luego instalar wrapper Python
pip install pyttsx3
```

### Opción D: MeloTTS desde GitHub (Avanzado)
```bash
# Solo si tienes git y quieres la versión de desarrollo
pip install git+https://github.com/myshell-ai/MeloTTS.git
```

## 🚀 Comandos de Prueba Inmediata

### Prueba Básica (Sin TTS):
```bash
cd mit-tts-streamer
pip install pydantic click rich python-json-logger
python3 run.py --test-config
```

### Prueba Completa (Con servidor web):
```bash
cd mit-tts-streamer
pip install -r requirements-minimal.txt
python3 run.py --debug
```

## 📊 Verificación de Instalación

### Script de Verificación:
```bash
python3 -c "
import sys
print(f'Python: {sys.version}')

try:
    import pydantic
    print('✅ pydantic: OK')
except ImportError as e:
    print(f'❌ pydantic: {e}')

try:
    import click
    print('✅ click: OK')
except ImportError as e:
    print(f'❌ click: {e}')

try:
    import rich
    print('✅ rich: OK')
except ImportError as e:
    print(f'❌ rich: {e}')

try:
    import pythonjsonlogger
    print('✅ python-json-logger: OK')
except ImportError as e:
    print(f'❌ python-json-logger: {e}')

print('\\n🎯 Verificación completa')
"
```

### Salida Esperada:
```
Python: 3.x.x
✅ pydantic: OK
✅ click: OK
✅ rich: OK
✅ python-json-logger: OK

🎯 Verificación completa
```

## 🐛 Solución de Problemas Específicos

### Error: `melo-tts==0.1.1` no encontrado
```bash
# SOLUCIÓN: No instalar melo-tts por ahora
# Usar solo las dependencias básicas:
pip install pydantic click rich python-json-logger
```

### Error: `ModuleNotFoundError`
```bash
# Instalar dependencia específica que falta
pip install <nombre-del-modulo>

# O usar requirements mínimos
pip install -r requirements-minimal.txt
```

### Error: `Permission denied`
```bash
# Usar --user si no tienes permisos de administrador
pip install --user pydantic click rich python-json-logger
```

## 📋 Archivos de Dependencias Disponibles

### `requirements-minimal.txt` (Recomendado)
- Solo dependencias que existen en PyPI
- Funcionalidad básica garantizada
- Instalación rápida

### `requirements.txt` (Completo)
- Todas las dependencias para funcionalidad completa
- Excluye TTS engines problemáticos
- Incluye dependencias de desarrollo

## 🎯 Próximos Pasos Después de la Instalación

### 1. Verificar que funciona:
```bash
python3 run.py --test-config
```

### 2. Ejecutar en modo demo:
```bash
python3 run.py
```

### 3. Ver todas las opciones:
```bash
python3 run.py --help
```

### 4. Ejecutar con debug:
```bash
python3 run.py --debug
```

## ✅ Instalación Garantizada en 3 Comandos

```bash
cd mit-tts-streamer
pip install pydantic click rich python-json-logger
python3 run.py --test-config
```

**¡Esta instalación funciona 100% sin errores de dependencias!** 🎉

El proyecto funcionará en modo demo sin TTS por ahora. Los motores TTS se pueden agregar después cuando estén disponibles o usando alternativas.