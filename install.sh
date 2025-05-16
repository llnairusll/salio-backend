#!/bin/bash
# Script de instalación para SALÍO Backend

echo "Instalando SALÍO Backend para Raspberry Pi..."

# Comprobar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
  echo "Por favor, ejecuta este script como root (usa sudo)"
  exit 1
fi

# Directorio de instalación
INSTALL_DIR="/home/pi/salio-backend"
echo "Instalando en: $INSTALL_DIR"

# Crear directorio si no existe
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Comprobar dependencias
echo "Instalando dependencias..."
apt update
apt install -y python3-pip python3-dev git libffi-dev python3-numpy python3-serial

# Instalar dependencias Python
echo "Instalando librerías Python..."
pip3 install flask flask-cors flask-socketio rplidar-roboticia evdev pyusb

# Instalar librerías adicionales desde requirements.txt
if [ -f "requirements.txt" ]; then
  pip3 install -r requirements.txt
fi

# Configurar udev rules para los dispositivos USB
echo "Configurando reglas udev para dispositivos USB..."
cat > /etc/udev/rules.d/99-salio-usb.rules << 'EOL'
# Regla para LIDAR
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="lidar"

# Regla para RFID
SUBSYSTEM=="input", ATTRS{idVendor}=="ffff", ATTRS{idProduct}=="0035", SYMLINK+="rfid"
EOL

# Aplicar reglas
echo "Aplicando reglas udev..."
udevadm control --reload-rules
udevadm trigger

# Configurar servicio systemd
echo "Configurando servicio systemd..."
cat > /etc/systemd/system/salio.service << 'EOL'
[Unit]
Description=SALIO Backend Service
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/salio-backend
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Asignar permisos
echo "Asignando permisos..."
chown -R pi:pi $INSTALL_DIR
chmod +x $INSTALL_DIR/app.py

# Habilitar servicio
echo "Habilitando servicio..."
systemctl enable salio.service
systemctl start salio.service

echo "¡Instalación completada!"
echo "Para ver el estado del servicio: sudo systemctl status salio.service"
echo "Para ver los logs: tail -f /home/pi/salio-backend/logs/salio.log"