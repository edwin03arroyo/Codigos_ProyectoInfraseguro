import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
import pytz
import RPi.GPIO as GPIO
import json

cred = credentials.Certificate("credenciales.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://grupo5-2c61d-default-rtdb.firebaseio.com/'
})

MQTT_BROKER = "192.168.0.102"
MQTT_PORT = 2204
MQTT_TOPIC_PUERTA1 = "esp32/puerta1"
MQTT_TOPIC_PUERTA2 = "esp32/puerta2"
MQTT_TOPIC_ESTADO_SOLENOIDE = "infraseguro/estado"

days_of_week_spanish = {
    'Monday': 'Lunes',
    'Tuesday': 'Martes',
    'Wednesday': 'Miercoles',
    'Thursday': 'Jueves',
    'Friday': 'Viernes',
    'Saturday': 'Sabado',
    'Sunday': 'Domingo'
}

global_id_counter = {
    'puerta1': 1,
    'puerta2': 1
}

# GPIO setup
RELE_PIN1 = 2
RELE_PIN2 = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELE_PIN1, GPIO.OUT)
GPIO.setup(RELE_PIN2, GPIO.OUT)
GPIO.output(RELE_PIN1, GPIO.LOW)
GPIO.output(RELE_PIN2, GPIO.LOW)

def get_current_time():
    tz = pytz.timezone('America/Guayaquil')
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def generate_custom_id(puerta):
    global global_id_counter
    day_of_week = days_of_week_spanish[datetime.now(pytz.timezone('America/Guayaquil')).strftime('%A')]
    custom_id = f"{day_of_week}{global_id_counter[puerta]:02d}-{puerta[-1]}"
    global_id_counter[puerta] += 1
    return custom_id

def publish_to_firebase(puerta, estado, id_tarjeta):
    ref = db.reference(f'puertas/{puerta}')
    custom_id = generate_custom_id(puerta)
    ref.child(custom_id).set({
        'estado': estado,
        'id_tarjeta': id_tarjeta,
        'timestamp': get_current_time()
    })

def publish_solenoid_status(solenoide1, solenoide2):
    status = {
        'solenoide1_estado': 1 if solenoide1 == 'Activado' else 0,
        'solenoide2_estado': 1 if solenoide2 == 'Activado' else 0
    }
    client.publish(MQTT_TOPIC_ESTADO_SOLENOIDE, json.dumps(status))

def on_message(client, userdata, message):
    payload = message.payload.decode()
    topic = message.topic
    
    estado, id_tarjeta = payload.split(': ')
    
    if topic == MQTT_TOPIC_PUERTA1:
        puerta = "puerta1"
        rele_pin = RELE_PIN1
    elif topic == MQTT_TOPIC_PUERTA2:
        puerta = "puerta2"
        rele_pin = RELE_PIN2
    else:
        return
    
    publish_to_firebase(puerta, estado, id_tarjeta)
    print(f"Publicado en Firebase: {puerta} - {estado}: {id_tarjeta}")
    
    if "Abierta" in estado:
        GPIO.output(rele_pin, GPIO.HIGH)
    elif "Cerrada" in estado:
        GPIO.output(rele_pin, GPIO.LOW)
    
    solenoide1_estado = 'Activado' if GPIO.input(RELE_PIN1) == GPIO.HIGH else 'Desactivado'
    solenoide2_estado = 'Activado' if GPIO.input(RELE_PIN2) == GPIO.HIGH else 'Desactivado'
    publish_solenoid_status(solenoide1_estado, solenoide2_estado)

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC_PUERTA1)
client.subscribe(MQTT_TOPIC_PUERTA2)
print("Escuchando mensajes MQTT...")
client.loop_forever()