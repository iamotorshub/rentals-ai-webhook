from flask import Flask, request, jsonify
import os
import re
import requests

app = Flask(__name__)

# 🔐 Telegram Config
TELEGRAM_BOT_TOKEN = "8334312092:AAGiK-6DEkboJHfEBFrv893SqfYBf09mps0"
TELEGRAM_CHAT_ID = "5392151099"

# 🧠 Función para extraer datos del resumen
def extraer_datos_del_resumen(transcript: str):
    datos = {
        'nombre': 'No especificado',
        'email': 'No especificado',
        'telefono': 'No especificado',
        'dia': 'No especificado',
        'hora': 'No especificado'
    }

    if not transcript:
        return datos

    # Busca tanto "RESUMEN DEMO" como "TUS DATOS" sin depender del emoji
    patron = re.compile(r'(RESUMEN\s*DEMO|TUS\s*DATOS)\s*:?\s*(.*)', re.IGNORECASE | re.DOTALL)
    match = patron.search(transcript)

    if match:
        contenido = match.group(2)
        for line in contenido.split('\n'):
            line = line.strip()
            if line.lower().startswith('- nombre'):
                datos['nombre'] = line.split(':', 1)[1].strip()
            elif line.lower().startswith('- email'):
                datos['email'] = line.split(':', 1)[1].strip()
            elif line.lower().startswith('- teléfono') or line.lower().startswith('- telefono'):
                datos['telefono'] = line.split(':', 1)[1].strip()
            elif line.lower().startswith('- demo agendada'):
                resto = line.split(':', 1)[1].strip()
                partes = resto.split(' a las ')
                if len(partes) == 2:
                    datos['dia'] = partes[0].strip()
                    datos['hora'] = partes[1].strip()
    return datos


# 📩 Envío a Telegram
def enviar_mensaje_telegram(nombre, email, telefono, dia, hora):
    mensaje = (
        f"📋 *Nuevo Lead Rentals AI*\n\n"
        f"- *Nombre:* {nombre}\n"
        f"- *Email:* {email}\n"
        f"- *Teléfono:* {telefono}\n"
        f"- *Día:* {dia}\n"
        f"- *Hora:* {hora}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})


# 🧩 Ruta principal del webhook
@app.route('/webhook/elevenlabs', methods=['POST'])
def webhook():
    # Lee datos JSON o form-data
    data = request.get_json(force=True, silent=True) or {}
    transcript = data.get('transcript', '')

    # Extrae del resumen como respaldo
    datos_resumen = extraer_datos_del_resumen(transcript)

    # Si vienen datos directos en el JSON, priorizalos
    nombre = data.get('nombre') or datos_resumen['nombre']
    email_val = data.get('email') or datos_resumen['email']
    telefono = data.get('telefono') or datos_resumen['telefono']
    dia = data.get('dia') or datos_resumen['dia']
    hora = data.get('hora') or datos_resumen['hora']

    # Envía mensaje
    enviar_mensaje_telegram(nombre, email_val, telefono, dia, hora)

    # Devuelve respuesta al caller
    return jsonify({
        "status": "ok",
        "nombre": nombre,
        "email": email_val,
        "telefono": telefono,
        "dia": dia,
        "hora": hora
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
