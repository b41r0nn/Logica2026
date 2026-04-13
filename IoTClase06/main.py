# -*- coding: utf-8 -*-

import os
import json
import re
import smtplib
import time
from email.mime.text import MIMEText
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Cargar variables de entorno
load_dotenv()

# Configuración MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/data")
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")

# Configuración Mail
MAIL_USER = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_TO = os.getenv("MAIL_ALERT", "")
mail_to_list = [correo.strip() for correo in MAIL_TO.split(",") if correo.strip()]

# Umbrales
TEMPERATURA_UMBRAL = float(os.getenv("UMBRAL_TEMPERATURA", 25))  # alerta si >= 25°C
HUMEDAD_UMBRAL = float(os.getenv("UMBRAL_HUMEDAD", 80))          # alerta si >= 80%

# ---------------------------
#  NO MODIFICAR ESTA FUNCIÓN
# ---------------------------
def enviar_mail_alerta(temperatura):
    subject = "¡Alerta de Temperatura Alta!"
    body = (
        f"⚠️ Alerta de temperatura en Robledo:\n"
        f"🌡️ Temperatura registrada: {temperatura}°C\n\n"
        f"La temperatura ha superado el umbral de {TEMPERATURA_UMBRAL}°C."
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = MAIL_USER
    msg["To"] = ", ".join(mail_to_list)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_USER, MAIL_PASSWORD)
        server.sendmail(MAIL_USER, mail_to_list, msg.as_string())
        server.quit()
        print("📧 Alerta enviada por correo (temperatura).")
    except Exception as e:
        print(f"❌ Error al enviar correo: {str(e)}")

# Misma lógica, pero para HUMEDAD
def enviar_mail_alerta_humedad(humedad):
    subject = "¡Alerta de Humedad Alta!"
    body = (
        f"⚠️ Alerta de humedad en Fraternidad:\n"
        f"💧 Humedad registrada: {humedad}%\n\n"
        f"La humedad ha superado el umbral de {HUMEDAD_UMBRAL}%."
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = MAIL_USER
    msg["To"] = ", ".join(mail_to_list)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_USER, MAIL_PASSWORD)
        server.sendmail(MAIL_USER, mail_to_list, msg.as_string())
        server.quit()
        print("📧 Alerta enviada por correo (humedad).")
    except Exception as e:
        print(f"❌ Error al enviar correo: {str(e)}")

# ------------------ Utilidades ------------------

# Acepta números o strings con unidades, e.g. '27.5°C', '83 %'
_num_regex = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
def _to_float(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = _num_regex.search(value.replace(",", "."))
        if match:
            return float(match.group(0))
    raise ValueError("valor no numérico")

def on_connect(client, userdata, flags, rc):
    print(f"✅ Conectado al broker {MQTT_BROKER}:{MQTT_PORT}")
    client.subscribe(MQTT_TOPIC)
    print(f"🔔 Suscrito al topic: {MQTT_TOPIC}")

def _extraer_medicion(data):
    """
    Soporta ambos formatos:
      - Nuevo: {"sede","sensor_id","metric","unit","value"}
      - Legado: {"temperature": x} o {"humidity": y}
    Retorna: (sede, sensor_id, metric, unit, value)
    """
    sede = data.get("sede")
    sensor_id = data.get("sensor_id")

    # Formato nuevo
    if "metric" in data and "value" in data:
        metric = str(data.get("metric")).strip().lower()
        unit = data.get("unit")
        value = data.get("value")
        return sede, sensor_id, metric, unit, value

    # Formato legado
    if "temperature" in data:
        return sede, sensor_id or "robledo-temp-01", "temperature", "C", data.get("temperature")
    if "humidity" in data:
        return sede, sensor_id or "fraternidad-hum-01", "humidity", "%", data.get("humidity")

    return None, None, None, None, None

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        sede, sensor_id, metric, unit, value = _extraer_medicion(data)

        if metric is None or value is None:
            print(f"ℹ️ Mensaje ignorado (no es medición conocida): {data}")
            return

        print("\n📌 Mensaje recibido:")
        print(f"🏷️ sede={sede}  sensor_id={sensor_id}  metric={metric}  unit={unit}  value={value}")
        print(f"📊 JSON completo: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if metric == "temperature":
            try:
                temp = _to_float(value)
                if temp >= TEMPERATURA_UMBRAL:
                    print(f"🚨 temp {temp}°C ≥ umbral {TEMPERATURA_UMBRAL}°C → envío mail")
                    enviar_mail_alerta(temp)
                else:
                    print(f"✅ temp {temp}°C < umbral {TEMPERATURA_UMBRAL}°C → sin alerta")
            except (TypeError, ValueError):
                print("⚠️ Temperatura no numérica, se omite alerta.")
        elif metric == "humidity":
            try:
                hum = _to_float(value)
                if hum >= HUMEDAD_UMBRAL:
                    print(f"🚨 hum {hum}% ≥ umbral {HUMEDAD_UMBRAL}% → envío mail")
                    enviar_mail_alerta_humedad(hum)
                else:
                    print(f"✅ hum {hum}% < umbral {HUMEDAD_UMBRAL}% → sin alerta")
            except (TypeError, ValueError):
                print("⚠️ Humedad no numérica, se omite alerta.")
        else:
            # Otras métricas posibles: ignorar o extender aquí
            print(f"ℹ️ Métrica no soportada: {metric}")

    except json.JSONDecodeError:
        print(f"❌ Error: Mensaje no es JSON válido: {msg.payload.decode(errors='ignore')}")
    except Exception as e:
        print(f"🔥 Error inesperado: {str(e)}")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message

    # 🔍 Debug de configuración
    print("⚙️ Configuración cargada:")
    print(f"  MQTT_BROKER={MQTT_BROKER}  MQTT_PORT={MQTT_PORT}  MQTT_TOPIC={MQTT_TOPIC}")
    print(f"  UMBRAL_TEMPERATURA={TEMPERATURA_UMBRAL}°C  UMBRAL_HUMEDAD={HUMEDAD_UMBRAL}%")
    print(f"  MAILS={mail_to_list}")

    print(f"🔗 Conectando a {MQTT_BROKER}:{MQTT_PORT}...")
    for intento in range(10):
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            print(f"⏳ Broker no disponible ({e}), reintentando en 5s... ({intento+1}/10)")
            time.sleep(5)
    else:
        print("❌ No se pudo conectar al broker tras 10 intentos. Saliendo.")
        return
    print("👂 Escuchando mensajes... (Ctrl+C para salir)")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🔌 Desconectando...")
        client.disconnect()

if __name__ == "__main__":
    main()
