from flask import Flask, request, jsonify
import os
import re
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus

app = Flask(__name__)

# ==========================
# CONFIGURACIÓN PRINCIPAL
# ==========================
TELEGRAM_BOT_TOKEN = "8334312092:AAGiK-6DEkboJHfEBFrv893SqfYBf09mps0"
TELEGRAM_CHAT_ID = "5392151099"

# ==========================
# FUNCIÓN: EXTRAER DATOS DEL RESUMEN
# ==========================
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

    patron = re.compile(r'(RESUMEN\s*DEMO|TUS\s*DATOS):?\s*(.*)', re.IGNORECASE | re.DOTALL)
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

# ==========================
# FUNCIÓN: ENVIAR MENSAJE A TELEGRAM
# ==========================
def enviar_mensaje_telegram(nombre, email, telefono, dia, hora):
    mensaje = f"Nuevo lead:\n- Nombre: {nombre}\n- Email: {email}\n- Teléfono: {telefono}\n- Día: {dia}\n- Hora: {hora}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje})
    print("✅ Mensaje enviado a Telegram")

# ==========================
# FUNCIÓN: GENERAR LINK DE GOOGLE CALENDAR
# ==========================
def generar_link_calendar(nombre, email, dia, hora):
    try:
        fecha = datetime.strptime(f"{dia} {hora}", "%Y-%m-%d %H:%M")
        fin = fecha + timedelta(minutes=30)
        titulo = f"Demo Rentals AI con {nombre}"
        descripcion = f"Demo automatizada de Rentals AI.\nConfirmación enviada a {email}."
        params = {
            "action": "TEMPLATE",
            "text": titulo,
            "dates": f"{fecha.strftime('%Y%m%dT%H%M%S')}/{fin.strftime('%Y%m%dT%H%M%S')}",
            "details": descripcion,
            "location": "Online Meeting",
        }
        return "https://www.google.com/calendar/render?" + urlencode(params, quote_via=quote_plus)
    except Exception as e:
        print(f"⚠️ Error generando link de calendar: {e}")
        return "https://calendar.google.com"

# ==========================
# FUNCIÓN: ENVIAR EMAIL AL CLIENTE + COPIA USANDO RESEND
# ==========================
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = "Rentals AI <contacto@iamotorshub.com>"

def enviar_email(nombre: str, email_cliente: str, telefono: str, dia: str, hora: str) -> None:
    """
    Envía un correo de confirmación al cliente y otro correo al equipo interno
    utilizando la API de Resend.
    """
    if not RESEND_API_KEY:
        print("⚠️ Falta RESEND_API_KEY; no se enviaron correos")
        return

    # Email para el cliente
    asunto_cliente = "Confirmación de demo - Rentals AI"
    cuerpo_cliente = f"""
    <p>Hola <strong>{nombre}</strong>,</p>
    <p>Gracias por agendar tu demo. Estos son los datos confirmados:</p>
    <ul>
      <li><b>Nombre:</b> {nombre}</li>
      <li><b>Email:</b> {email_cliente}</li>
      <li><b>Teléfono:</b> {telefono}</li>
      <li><b>Día:</b> {dia}</li>
      <li><b>Hora:</b> {hora}</li>
    </ul>
    <p>Nuestro equipo se pondrá en contacto contigo pronto.</p>
    """

    requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": [email_cliente],
            "reply_to": [FROM_EMAIL],
            "subject": asunto_cliente,
            "html": cuerpo_cliente,
        },
    )

    # Email interno al equipo
    cuerpo_equipo = f"""
    <h3>Nuevo lead de demo</h3>
    <ul>
      <li><b>Nombre:</b> {nombre}</li>
      <li><b>Email:</b> {email_cliente}</li>
      <li><b>Teléfono:</b> {telefono}</li>
      <li><b>Día:</b> {dia}</li>
      <li><b>Hora:</b> {hora}</li>
    </ul>
    """

    requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": ["contacto@iamotorshub.com"],
            "reply_to": [email_cliente],
            "subject": f"Nuevo lead: {nombre}",
            "html": cuerpo_equipo,
        },
    )

    print("✅ Correos enviados vía Resend")

# ==========================
# WEBHOOK PRINCIPAL
# ==========================
@app.route('/webhook/elevenlabs', methods=['POST'])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    transcript = data.get('transcript', '')

    datos_resumen = extraer_datos_del_resumen(transcript)
    nombre = data.get('nombre', datos_resumen['nombre'])
    email_val = data.get('email', datos_resumen['email'])
    telefono = data.get('telefono', datos_resumen['telefono'])
    dia = data.get('dia', datos_resumen['dia'])
    hora = data.get('hora', datos_resumen['hora'])

    enviar_mensaje_telegram(nombre, email_val, telefono, dia, hora)
    enviar_email(nombre, email_val, telefono, dia, hora)

    return jsonify({
        "status": "ok",
        "nombre": nombre,
        "email": email_val,
        "telefono": telefono,
        "dia": dia,
        "hora": hora
    })

# ==========================
# MAIN APP
# ==========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
