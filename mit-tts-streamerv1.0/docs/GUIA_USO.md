# 📖 Guía Paso a Paso de Uso - MIT-TTS-Streamer

**Autor:** Beler Nolasco Almonte

Esta guía te llevará paso a paso desde la instalación hasta el uso avanzado del MIT-TTS-Streamer.

## 🚀 Inicio Rápido (5 minutos)

### Paso 1: Configuración Automática
```bash
# Navegar al directorio del proyecto
cd mit-tts-streamer

# Configurar automáticamente (modo no interactivo)
./scripts/configure.sh --non-interactive
```

### Paso 2: Ejecutar el Servidor
```bash
# Opción A: Servidor de prueba con uvicorn
python3 test_server.py

# Opción B: Servidor principal
python3 run.py --port 8000
```

### Paso 3: Verificar que Funciona
```bash
# En otra terminal, probar el health check
curl http://localhost:8000/api/v1/health
```

¡Listo! Tu servidor TTS está funcionando.

## 📋 Guía Completa Paso a Paso

### 🔧 **FASE 1: Preparación del Sistema**

#### Paso 1.1: Verificar Requisitos del Sistema
```bash
# Verificar Python 3.8+
python3 --version

# Verificar pip
pip3 --version

# Verificar git (opcional)
git --version
```

#### Paso 1.2: Clonar o Descargar el Proyecto
```bash
# Si tienes git
git clone <repository-url>
cd mit-tts-streamer

# O descomprimir si descargaste un ZIP
unzip mit-tts-streamer.zip
cd mit-tts-streamer
```

#### Paso 1.3: Verificar la Estructura del Proyecto
```bash
# Listar archivos principales
ls -la

# Deberías ver:
# - src/          (código fuente)
# - scripts/      (scripts de utilidades)
# - config/       (configuraciones)
# - docs/         (documentación)
# - requirements.txt
# - run.py
```

### ⚙️ **FASE 2: Configuración**

#### Paso 2.1: Configuración Interactiva (Recomendado)
```bash
# Ejecutar configuración interactiva
./scripts/configure.sh

# Responder las preguntas:
# - Server name: [MIT-TTS-Streamer]
# - Environment: [development/staging/production]
# - HTTP port: [8000]
# - WebSocket port: [8001]
# - Log level: [INFO]
# - TTS engine: [melo]
# - Default voice: [EN-US]
# - Audio format: [wav]
# - Enable monitoring: [y/n]
# - Enable SSL: [y/n]
```

#### Paso 2.2: Configuración No Interactiva (Automática)
```bash
# Para usar valores por defecto
./scripts/configure.sh --non-interactive
```

#### Paso 2.3: Verificar Archivos de Configuración Generados
```bash
# Verificar que se crearon los archivos
ls -la config/
ls -la .env
ls -la docker.env

# Ver la configuración generada
cat config/config.json
```

### 🏃‍♂️ **FASE 3: Ejecución**

#### Paso 3.1: Ejecutar el Servidor (Método Simple)
```bash
# Servidor de prueba con uvicorn (recomendado para desarrollo)
python3 test_server.py

# Deberías ver:
# INFO: Uvicorn running on http://0.0.0.0:8000
# INFO: Application startup complete.
```

#### Paso 3.2: Ejecutar el Servidor (Método Avanzado)
```bash
# Servidor principal con todas las funcionalidades
python3 run.py --port 8000 --log-level INFO

# Con opciones personalizadas
python3 run.py --host 0.0.0.0 --port 8000 --websocket-port 8001 --log-level DEBUG
```

#### Paso 3.3: Verificar que el Servidor Está Funcionando
```bash
# En otra terminal, probar endpoints básicos
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/status
curl http://localhost:8000/api/v1/voices
```

### 🌐 **FASE 4: Uso de la API Web**

#### Paso 4.1: Acceder a la Documentación Interactiva
```bash
# Abrir en el navegador
http://localhost:8000/docs
```

#### Paso 4.2: Probar Endpoints Básicos desde el Navegador
1. **Health Check**: `GET /api/v1/health`
2. **System Status**: `GET /api/v1/status`
3. **Available Voices**: `GET /api/v1/voices`
4. **Metrics**: `GET /api/v1/metrics`

#### Paso 4.3: Crear una Sesión TTS
```bash
# Crear sesión via curl
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "language": "es",
    "voice_id": 0,
    "format": "wav",
    "sample_rate": 22050,
    "speed": 1.0
  }'
```

### 🎯 **FASE 5: Uso con Clientes de Ejemplo**

#### Paso 5.1: Ejecutar el Cliente HTTP de Ejemplo
```bash
# Demo básico
echo "1" | python3 examples/http_client_example.py

# Demo completo (todos los demos)
echo "5" | python3 examples/http_client_example.py
```

#### Paso 5.2: Usar el Cliente WebSocket (si está disponible)
```bash
# Ejecutar cliente WebSocket
python3 examples/websocket_client_example.py
```

### 🔧 **FASE 6: Administración y Monitoreo**

#### Paso 6.1: Verificar Estado del Sistema
```bash
# Usar script de utilidades
./scripts/utils.sh status

# Health check específico
./scripts/utils.sh health localhost 8000
```

#### Paso 6.2: Ver Logs del Sistema
```bash
# Ver logs en tiempo real
tail -f logs/mit-tts-streamer.log

# Analizar logs con el script
./scripts/utils.sh logs logs/mit-tts-streamer.log 100
```

#### Paso 6.3: Monitorear Métricas
```bash
# Ver métricas via API
curl http://localhost:8000/api/v1/metrics | python3 -m json.tool

# Métricas de rendimiento
./scripts/utils.sh performance localhost 8000 10 100
```

### 🛠️ **FASE 7: Configuración Avanzada**

#### Paso 7.1: Personalizar Configuración
```bash
# Editar configuración manualmente
nano config/config.json

# Recargar configuración sin reiniciar
curl -X POST http://localhost:8000/api/v1/config/reload
```

#### Paso 7.2: Configurar Voces Personalizadas
```bash
# Editar configuración de voces
nano config/voices.json

# Verificar voces disponibles
curl http://localhost:8000/api/v1/voices
```

#### Paso 7.3: Configurar Logging Avanzado
```bash
# Cambiar nivel de logging via API
curl -X POST http://localhost:8000/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"logging": {"level": "DEBUG"}}'
```

### 🐳 **FASE 8: Despliegue con Docker (Opcional)**

#### Paso 8.1: Despliegue Básico con Docker
```bash
# Usar script de despliegue
./scripts/deploy.sh --type docker --env development
```

#### Paso 8.2: Despliegue con Monitoreo
```bash
# Despliegue con Prometheus y Grafana
./scripts/deploy.sh --type docker --env production --monitoring
```

## 🎯 **Casos de Uso Comunes**

### Caso 1: Desarrollo Local
```bash
# 1. Configuración rápida
./scripts/configure.sh --non-interactive

# 2. Ejecutar servidor de desarrollo
python3 test_server.py

# 3. Probar con cliente de ejemplo
echo "1" | python3 examples/http_client_example.py
```

### Caso 2: Servidor de Producción
```bash
# 1. Configuración para producción
./scripts/configure.sh
# Seleccionar: environment=production, SSL=yes, monitoring=yes

# 2. Desplegar con Docker
./scripts/deploy.sh --type docker --env production --ssl --monitoring

# 3. Verificar despliegue
./scripts/utils.sh health localhost 8000
```

### Caso 3: Desarrollo de Cliente Personalizado
```bash
# 1. Ejecutar servidor
python3 test_server.py

# 2. Ver documentación de API
# Navegador: http://localhost:8000/docs

# 3. Usar ejemplos como referencia
cat examples/http_client_example.py
cat examples/websocket_client_example.py
```

## 🚨 **Solución de Problemas Comunes**

### Problema 1: Puerto ya en uso
```bash
# Verificar qué está usando el puerto
sudo lsof -i :8000

# Cambiar puerto
python3 run.py --port 8080
```

### Problema 2: Dependencias faltantes
```bash
# Instalar dependencias básicas
pip3 install -r requirements.txt

# Instalar dependencias TTS (opcional)
pip3 install -r requirements-tts.txt
```

### Problema 3: Permisos de scripts
```bash
# Dar permisos de ejecución
chmod +x scripts/*.sh
```

### Problema 4: Configuración corrupta
```bash
# Regenerar configuración
rm -f config/config.json .env docker.env
./scripts/configure.sh --non-interactive
```

## 📊 **Verificación Final**

### Checklist de Funcionamiento
- [ ] Servidor inicia sin errores
- [ ] Health check responde OK
- [ ] Documentación API accesible en /docs
- [ ] Cliente de ejemplo funciona
- [ ] Logs se generan correctamente
- [ ] Métricas están disponibles

### Comandos de Verificación
```bash
# 1. Health check
curl -f http://localhost:8000/api/v1/health

# 2. Status check
curl -f http://localhost:8000/api/v1/status

# 3. Voices check
curl -f http://localhost:8000/api/v1/voices

# 4. Metrics check
curl -f http://localhost:8000/api/v1/metrics

# 5. Client example
echo "1" | python3 examples/http_client_example.py
```

## 🎓 **Próximos Pasos**

1. **Explorar la API**: Usa la documentación interactiva en `/docs`
2. **Personalizar configuración**: Edita `config/config.json`
3. **Desarrollar cliente**: Usa los ejemplos como base
4. **Monitorear rendimiento**: Usa las métricas y logs
5. **Desplegar en producción**: Usa Docker y los scripts de despliegue

## 📞 **Soporte**

- **Documentación técnica**: Ver `docs/DOCUMENTACION_TECNICA.md`
- **API Reference**: Ver `docs/http-rest-api.md`
- **Logs del sistema**: `logs/mit-tts-streamer.log`
- **Scripts de utilidades**: `./scripts/utils.sh help`

---

**¡Felicidades! Ya tienes MIT-TTS-Streamer funcionando correctamente.** 🎉

Para uso avanzado, consulta la documentación técnica completa.