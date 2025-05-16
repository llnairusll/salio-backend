# salio-backend
Backend para el sistema SALÍO RP
## Requisitos

- Raspberry Pi 4B
- Sensor LIDAR USB (compatible con RPLidar A1/A2)
- Lector RFID USB
- Conexión a internet

## Instalación rápida

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/salio-backend.git
   cd salio-backend
   ```

2. Ejecuta el script de instalación:
   ```bash
   sudo ./install.sh
   ```

3. Verifica que el servicio esté en funcionamiento:
   ```bash
   sudo systemctl status salio.service
   ```

## Instalación manual

Si prefieres instalar manualmente, sigue estos pasos:

1. Instala las dependencias:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-dev python3-numpy python3-serial
   pip3 install -r requirements.txt
   ```

2. Configura las reglas udev para los dispositivos USB:
   ```bash
   sudo nano /etc/udev/rules.d/99-salio-usb.rules
   ```
   
   Contenido:
   ```
   SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="lidar"
   SUBSYSTEM=="input", ATTRS{idVendor}=="ffff", ATTRS{idProduct}=="0035", SYMLINK+="rfid"
   ```

3. Aplica las reglas:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

4. Configura el servicio:
   ```bash
   sudo cp salio.service /etc/systemd/system/
   sudo systemctl enable salio.service
   sudo systemctl start salio.service
   ```

## Configuración

La configuración se encuentra en el archivo `config.json`:

```json
{
  "lidar_port": "/dev/lidar",
  "rfid_device": "/dev/rfid",
  "server_port": 5000,
  "api_endpoint": "/api",
  "enable_cors": true
}
```

Ajusta los valores según sea necesario para tu instalación.

## API REST

El backend expone los siguientes endpoints:

- `GET /api/status` - Obtiene el estado actual del sistema
- `POST /api/connect` - Conecta a los dispositivos LIDAR y RFID
- `POST /api/disconnect` - Desconecta los dispositivos
- `POST /api/escaneo` - Inicia un escaneo con LIDAR y RFID

## WebSockets

El backend también proporciona eventos en tiempo real mediante WebSockets:

- `rfid_detection` - Emitido cuando se detecta un tag RFID
- `lidar_data` - Emitido con datos del escaneo LIDAR
- `scan_started` - Emitido cuando comienza un escaneo

## Solución de problemas

### Los dispositivos no son detectados

Verifica que las reglas udev estén correctamente configuradas:

```bash
ls -l /dev/lidar
ls -l /dev/rfid
```

Si no existen, puedes identificar los dispositivos con:

```bash
lsusb
ls -l /dev/ttyUSB*
```

Y ajustar las reglas udev según los IDs de tus dispositivos.

### El servicio no inicia

Verifica los logs:

```bash
sudo journalctl -u salio.service
tail -f /home/pi/salio-backend/logs/salio.log
```

## Licencia

Este software se distribuye bajo la licencia MIT.
