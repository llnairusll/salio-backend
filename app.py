import json
import logging
import os
import signal
import sys
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/salio.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("salio-backend")

# Asegurar que exista el directorio de logs
os.makedirs("logs", exist_ok=True)

# Cargar configuración
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except Exception as e:
    logger.error(f"Error cargando configuración: {e}")
    config = {
        "lidar_port": "/dev/lidar",
        "rfid_device": "/dev/rfid",
        "server_port": 5000,
        "api_endpoint": "/api",
        "enable_cors": True
    }

# Importar controladores
try:
    from modules.lidar_controller import LidarController
    from modules.rfid_controller import RfidController
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)

# Inicializar Flask
app = Flask(__name__)
if config.get("enable_cors", True):
    CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Instanciar controladores
lidar = LidarController(config["lidar_port"])
rfid = RfidController(config["rfid_device"])

# Estado del sistema
system_state = {
    "running": False,
    "rfid_tags": 0,
    "lidar_connected": False,
    "rfid_connected": False,
    "last_updated": time.time()
}

# API Endpoints
@app.route(f"{config['api_endpoint']}/status", methods=['GET'])
def get_status():
    """Retorna el estado actual del sistema"""
    system_state["last_updated"] = time.time()
    return jsonify(system_state)

@app.route(f"{config['api_endpoint']}/connect", methods=['POST'])
def connect():
    """Conecta con los dispositivos LIDAR y RFID"""
    try:
        lidar_success = lidar.connect()
        rfid_success = rfid.connect()
        
        system_state["lidar_connected"] = lidar_success
        system_state["rfid_connected"] = rfid_success
        system_state["running"] = lidar_success or rfid_success
        
        logger.info(f"Conexión establecida - LIDAR: {lidar_success}, RFID: {rfid_success}")
        
        return jsonify({
            "success": lidar_success or rfid_success,
            "lidar": lidar_success,
            "rfid": rfid_success
        })
    except Exception as e:
        logger.error(f"Error al conectar: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route(f"{config['api_endpoint']}/disconnect", methods=['POST'])
def disconnect():
    """Desconecta los dispositivos"""
    try:
        lidar.disconnect()
        rfid.disconnect()
        
        system_state["lidar_connected"] = False
        system_state["rfid_connected"] = False
        system_state["running"] = False
        
        logger.info("Dispositivos desconectados")
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error al desconectar: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route(f"{config['api_endpoint']}/escaneo", methods=['POST'])
def start_scan():
    """Inicia un escaneo con LIDAR y RFID"""
    if not system_state["running"]:
        return jsonify({
            "success": False,
            "error": "El sistema no está conectado"
        }), 400
    
    try:
        # Iniciar escaneo asíncrono
        lidar.start_scan()
        socketio.emit('scan_started', {'timestamp': time.time()})
        
        logger.info("Escaneo iniciado")
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error al iniciar escaneo: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Eventos Socket.IO
@socketio.on('connect')
def handle_connect():
    """Manejar conexión de socket"""
    logger.info(f"Cliente conectado: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Manejar desconexión de socket"""
    logger.info(f"Cliente desconectado: {request.sid}")

# Manejador de cierre
def signal_handler(sig, frame):
    """Manejar señales de cierre"""
    logger.info("Cerrando aplicación...")
    lidar.disconnect()
    rfid.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# RFID event callback
def rfid_detected(tag_id):
    """Callback para detección de tags RFID"""
    system_state["rfid_tags"] += 1
    detection = {
        "tagId": tag_id,
        "timestamp": time.time()
    }
    socketio.emit('rfid_detection', detection)
    logger.info(f"RFID detectado: {tag_id}")

# Asignar callback
rfid.set_detection_callback(rfid_detected)

# LIDAR data callback
def lidar_data(scan_data):
    """Callback para datos del LIDAR"""
    socketio.emit('lidar_data', {
        'timestamp': time.time(),
        'points': scan_data
    })

# Asignar callback
lidar.set_data_callback(lidar_data)

if __name__ == "__main__":
    logger.info(f"Iniciando SALÍO Backend en puerto {config['server_port']}...")
    socketio.run(app, host='0.0.0.0', port=config['server_port'])