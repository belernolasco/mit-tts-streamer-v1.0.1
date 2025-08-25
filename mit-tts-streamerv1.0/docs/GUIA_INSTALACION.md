# 🛠️ Guía de Instalación Completa - MIT-TTS-Streamer

**Autor:** Beler Nolasco Almonte

Esta guía cubre todos los métodos de instalación posibles para MIT-TTS-Streamer, desde instalación básica hasta despliegue en producción.

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Sistema Operativo**: Linux, macOS, Windows 10+
- **Python**: 3.8 o superior
- **RAM**: 2GB mínimo, 4GB recomendado
- **Almacenamiento**: 1GB libre
- **Red**: Acceso a internet para descargar dependencias

### Requisitos Recomendados
- **Sistema Operativo**: Ubuntu 20.04+ / CentOS 8+ / macOS 11+
- **Python**: 3.9 o 3.10
- **RAM**: 8GB o más
- **CPU**: 4 núcleos o más
- **Almacenamiento**: 5GB libre (incluyendo modelos TTS)
- **Red**: Conexión estable para streaming

### Dependencias del Sistema

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    libffi-dev \
    libssl-dev
```

#### CentOS/RHEL/Fedora
```bash
sudo dnf update
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    gcc-c++ \
    make \
    git \
    curl \
    wget \
    ffmpeg \
    portaudio-devel \
    alsa-lib-devel \
    libsndfile-devel \
    libffi-devel \
    openssl-devel
```

#### macOS
```bash
# Instalar Homebrew si no está instalado
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias
brew install python@3.9 git curl wget ffmpeg portaudio libsndfile
```

#### Windows
```powershell
# Instalar Python desde python.org
# Instalar Git desde git-scm.com
# Instalar Visual Studio Build Tools

# Usando chocolatey (opcional)
choco install python git curl wget ffmpeg
```

## 🚀 Métodos de Instalación

### Método 1: Instalación Automática (Recomendado)

#### Paso 1: Descargar el Proyecto
```bash
# Opción A: Con git
git clone <repository-url>
cd mit-tts-streamer

# Opción B: Descargar ZIP
wget <download-url>
unzip mit-tts-streamer.zip
cd mit-tts-streamer
```

#### Paso 2: Ejecutar Script de Instalación
```bash
# Dar permisos de ejecución
chmod +x scripts/install.sh

# Instalación automática
sudo ./scripts/install.sh

# O instalación en directorio personalizado
sudo ./scripts/install.sh --install-dir /opt/mit-tts-streamer
```

#### Paso 3: Verificar Instalación
```bash
# Verificar que el servicio está instalado
systemctl status mit-tts-streamer

# Verificar archivos de configuración
ls -la /etc/mit-tts-streamer/
```

### Método 2: Instalación Manual

#### Paso 1: Preparar Entorno Virtual
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Paso 2: Instalar Dependencias Python
```bash
# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependencias básicas
pip install -r requirements.txt

# Instalar dependencias TTS (opcional pero recomendado)
pip install -r requirements-tts.txt

# Instalar dependencias de desarrollo (opcional)
pip install -r requirements-test.txt
```

#### Paso 3: Configurar el Sistema
```bash
# Crear directorios necesarios
mkdir -p logs data cache models backups

# Configurar permisos
chmod +x scripts/*.sh

# Generar configuración inicial
./scripts/configure.sh --non-interactive
```

#### Paso 4: Probar la Instalación
```bash
# Ejecutar servidor de prueba
python3 test_server.py

# En otra terminal, probar
curl http://localhost:8000/api/v1/health
```

### Método 3: Instalación con Docker

#### Paso 1: Instalar Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Paso 2: Construir Imagen Docker
```bash
# Construir imagen
docker build -t mit-tts-streamer:latest .

# O usar docker-compose
docker-compose build
```

#### Paso 3: Ejecutar con Docker
```bash
# Ejecutar contenedor individual
docker run -d \
  --name mit-tts-streamer \
  -p 8000:8000 \
  -p 8001:8001 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  mit-tts-streamer:latest

# O usar docker-compose
docker-compose up -d
```

#### Paso 4: Verificar Contenedor
```bash
# Ver logs del contenedor
docker logs mit-tts-streamer

# Probar el servicio
curl http://localhost:8000/api/v1/health
```

### Método 4: Instalación desde Código Fuente

#### Paso 1: Clonar Repositorio
```bash
git clone <repository-url>
cd mit-tts-streamer
```

#### Paso 2: Instalar como Paquete Python
```bash
# Instalación en modo desarrollo
pip install -e .

# O instalación normal
pip install .
```

#### Paso 3: Usar como Comando del Sistema
```bash
# Ahora puedes usar el comando directamente
mit-tts-streamer --help
mit-tts-streamer --port 8000
```

## 🔧 Configuración Post-Instalación

### Configuración Básica

#### Paso 1: Generar Configuración
```bash
# Configuración interactiva
./scripts/configure.sh

# Configuración automática
./scripts/configure.sh --non-interactive
```

#### Paso 2: Personalizar Configuración
```bash
# Editar configuración principal
nano config/config.json

# Editar configuración de voces
nano config/voices.json

# Configurar variables de entorno
nano .env
```

#### Paso 3: Configurar Logging
```bash
# Crear directorio de logs
mkdir -p logs

# Configurar rotación de logs (opcional)
sudo nano /etc/logrotate.d/mit-tts-streamer
```

### Configuración de Producción

#### Paso 1: Configurar Servicio Systemd
```bash
# El script de instalación ya crea esto, pero puedes personalizarlo
sudo nano /etc/systemd/system/mit-tts-streamer.service

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar inicio automático
sudo systemctl enable mit-tts-streamer
```

#### Paso 2: Configurar Proxy Reverso (Nginx)
```bash
# Instalar nginx
sudo apt install nginx

# Configurar sitio
sudo nano /etc/nginx/sites-available/mit-tts-streamer

# Contenido del archivo:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/mit-tts-streamer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Paso 3: Configurar SSL con Let's Encrypt
```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d your-domain.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

### Configuración de Monitoreo

#### Paso 1: Configurar Prometheus (Opcional)
```bash
# Usar docker-compose con perfil de monitoreo
docker-compose --profile monitoring up -d

# O instalar manualmente
wget https://github.com/prometheus/prometheus/releases/latest/download/prometheus-*.tar.gz
tar xvf prometheus-*.tar.gz
sudo mv prometheus-* /opt/prometheus
```

#### Paso 2: Configurar Grafana (Opcional)
```bash
# Ya incluido en docker-compose con monitoreo
# Acceder a http://localhost:3000
# Usuario: admin, Contraseña: admin
```

## 🧪 Verificación de la Instalación

### Tests Básicos
```bash
# 1. Verificar que Python puede importar el módulo
python3 -c "import src.main; print('Import OK')"

# 2. Verificar configuración
python3 -c "from src.core.config_manager import ConfigManager; cm = ConfigManager(); print('Config OK')"

# 3. Verificar dependencias
pip check

# 4. Ejecutar tests unitarios (si están disponibles)
python3 -m pytest tests/ -v
```

### Tests de Funcionalidad
```bash
# 1. Iniciar servidor
python3 test_server.py &
SERVER_PID=$!

# 2. Esperar a que inicie
sleep 5

# 3. Probar endpoints
curl -f http://localhost:8000/api/v1/health
curl -f http://localhost:8000/api/v1/status
curl -f http://localhost:8000/api/v1/voices

# 4. Probar cliente de ejemplo
echo "1" | python3 examples/http_client_example.py

# 5. Detener servidor
kill $SERVER_PID
```

### Tests de Rendimiento
```bash
# Usar script de utilidades
./scripts/utils.sh performance localhost 8000 10 100

# O usar herramientas externas
ab -n 100 -c 10 http://localhost:8000/api/v1/health
```

## 🚨 Solución de Problemas de Instalación

### Problema 1: Dependencias Python Faltantes
```bash
# Error: ModuleNotFoundError
# Solución: Reinstalar dependencias
pip install --force-reinstall -r requirements.txt
```

### Problema 2: Permisos Insuficientes
```bash
# Error: Permission denied
# Solución: Usar sudo o cambiar permisos
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

### Problema 3: Puerto en Uso
```bash
# Error: Address already in use
# Solución: Cambiar puerto o matar proceso
sudo lsof -i :8000
sudo kill -9 <PID>
# O cambiar puerto
python3 run.py --port 8080
```

### Problema 4: Dependencias del Sistema Faltantes
```bash
# Error: Failed building wheel for <package>
# Solución: Instalar dependencias del sistema
# Ver sección "Dependencias del Sistema" arriba
```

### Problema 5: Problemas con Docker
```bash
# Error: Docker daemon not running
sudo systemctl start docker

# Error: Permission denied (Docker)
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

## 🔄 Actualización del Sistema

### Actualización Manual
```bash
# 1. Hacer backup
./scripts/utils.sh backup

# 2. Detener servicio
sudo systemctl stop mit-tts-streamer

# 3. Actualizar código
git pull origin main

# 4. Actualizar dependencias
pip install --upgrade -r requirements.txt

# 5. Migrar configuración si es necesario
./scripts/configure.sh --upgrade

# 6. Reiniciar servicio
sudo systemctl start mit-tts-streamer
```

### Actualización con Docker
```bash
# 1. Hacer backup
docker-compose exec mit-tts-streamer ./scripts/utils.sh backup

# 2. Actualizar imágenes
docker-compose pull

# 3. Reconstruir y reiniciar
docker-compose up -d --build
```

## 📊 Verificación Final

### Checklist de Instalación Exitosa
- [ ] Python 3.8+ instalado
- [ ] Dependencias del sistema instaladas
- [ ] Dependencias Python instaladas
- [ ] Configuración generada
- [ ] Servidor inicia sin errores
- [ ] Health check responde OK
- [ ] API documentation accesible
- [ ] Cliente de ejemplo funciona
- [ ] Logs se generan correctamente
- [ ] Servicio systemd configurado (producción)

### Comandos de Verificación Final
```bash
# Verificación completa
./scripts/utils.sh status
./scripts/utils.sh health localhost 8000
echo "1" | python3 examples/http_client_example.py
curl http://localhost:8000/docs
```

## 📞 Soporte de Instalación

### Logs de Instalación
- **Script de instalación**: `/var/log/mit-tts-streamer-install.log`
- **Logs del sistema**: `logs/mit-tts-streamer.log`
- **Logs de systemd**: `journalctl -u mit-tts-streamer`

### Información del Sistema
```bash
# Generar reporte de sistema
./scripts/utils.sh status > system-report.txt
python3 --version >> system-report.txt
pip list >> system-report.txt
```

### Contacto
- **Autor**: Beler Nolasco Almonte
- **Email**: beler.nolasco@example.com
- **Documentación**: Ver `docs/DOCUMENTACION_TECNICA.md`

---

**¡Instalación completada!** 🎉

Para comenzar a usar el sistema, consulta la `GUIA_USO.md`.