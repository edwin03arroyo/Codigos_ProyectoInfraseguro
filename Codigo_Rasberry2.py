import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import RPi.GPIO as GPIO
import time

# Configuracion de Firebase
cred = credentials.Certificate("credenciales.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://grupo5-2c61d-default-rtdb.firebaseio.com/'
})

# Configuracion de GPIO
RELE_PIN1 = 2
RELE_PIN2 = 3
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELE_PIN1, GPIO.OUT)
GPIO.setup(RELE_PIN2, GPIO.OUT)
GPIO.output(RELE_PIN1, GPIO.LOW)
GPIO.output(RELE_PIN2, GPIO.LOW)

# Variables para almacenar el estado anterior
estado_anterior_selenoide1 = None
estado_anterior_selenoide2 = None

def controlar_rele(pin, valor):
    if valor == 1:
        GPIO.output(pin, GPIO.HIGH)
        return "Activado"
    else:
        GPIO.output(pin, GPIO.LOW)
        return "Desactivado"

def leer_datos_y_controlar_reles():
    global estado_anterior_selenoide1, estado_anterior_selenoide2
    ref = db.reference('/')
    
    selenoide1 = ref.child('Selenoide1').get()
    selenoide2 = ref.child('Selenoide2').get()
    
    # Convertir a enteros si no son None
    selenoide1 = int(selenoide1) if selenoide1 is not None else 0
    selenoide2 = int(selenoide2) if selenoide2 is not None else 0
    
    if selenoide1 != estado_anterior_selenoide1:
        estado = controlar_rele(RELE_PIN1, selenoide1)
        print(f"Cambio en Selenoide1: {estado}")
        estado_anterior_selenoide1 = selenoide1
    
    if selenoide2 != estado_anterior_selenoide2:
        estado = controlar_rele(RELE_PIN2, selenoide2)
        print(f"Cambio en Selenoide2: {estado}")
        estado_anterior_selenoide2 = selenoide2

def main():
    try:
        print("Monitoreando cambios en Firebase...")
        while True:
            leer_datos_y_controlar_reles()
            time.sleep(1)  # Revisar cada segundo
    except KeyboardInterrupt:
        print("Programa terminado por el usuario")
    finally:
        GPIO.cleanup()  

if _name_ == "_main_":
    main()