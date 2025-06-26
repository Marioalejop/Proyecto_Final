from flask import Flask, render_template, jsonify
import serial
from pymongo import MongoClient
from urllib.parse import quote_plus
from datetime import datetime
import pytz
import threading

# Configuración Flask
app = Flask(__name__)

# Zona horaria
timezone = pytz.timezone('America/Bogota')

# Configuración MongoDB Atlas
usuario = quote_plus("marioalejop")
clave = quote_plus("Juliana23")
cluster = "cluster0.xjiaffo.mongodb.net"
base_datos = "proyecto_final"

uri = f"mongodb+srv://{usuario}:{clave}@{cluster}/{base_datos}?retryWrites=true&w=majority&appName=Cluster0"

# Conexión MongoDB
client = MongoClient(uri, serverSelectionTimeoutMS=5000)
db = client[base_datos]
coleccion = db["arduino_uno"]

try:
    client.server_info()
    print("✅ Conexión establecida con MongoDB Atlas")
except Exception as e:
    print("❌ Error al conectar con MongoDB:", e)
    exit()

# Apertura segura del puerto serial (solo una vez)
try:
    puerto_serial = serial.Serial('COM8', 9600, timeout=1)
    print("🟢 Esperando datos desde el Arduino (COM8)...")
except serial.SerialException as e:
    print(f"❌ Error al abrir el puerto: {e}")
    exit()

# Lectura en hilo paralelo
def leer_serial():
    while True:
        try:
            linea = puerto_serial.readline().decode('utf-8').strip()
            if linea and "," in linea:
                temp_str, hum_str = linea.split(",")
                temperatura = float(temp_str)
                humedad = float(hum_str)

                dato = {
                    "sensor": "DHT11",
                    "temperatura": temperatura,
                    "humedad": humedad,
                    "fecha_hora": datetime.now(timezone),
                    "ubicacion": "Taller"
                }

                coleccion.insert_one(dato)
                print(f"📤 Subido -> Temp: {temperatura} °C | Humedad: {humedad} %")

        except Exception as error:
            print("⚠️ Error:", error)

# Iniciar hilo
hilo_serial = threading.Thread(target=leer_serial)
hilo_serial.daemon = True
hilo_serial.start()

# Rutas Flask
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/datos')
def obtener_datos():
    datos = list(coleccion.find().sort('fecha_hora', -1).limit(10))
    for dato in datos:
        dato['_id'] = str(dato['_id'])
        dato['fecha_hora'] = dato['fecha_hora'].strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(datos)

if __name__ == '__main__':
    app.run(debug=False)
