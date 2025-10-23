from flask import Flask, request, jsonify
import os
import re
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
        # Parsear la fecha y hora recibidas
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
# FUNCIÓN: ENVIAR EMAIL AL CLIENTE + COPIA
# ==========================
def enviar_email(nombre, email_cliente, telefono, dia, hora):
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASSWORD')

    if not smtp_user or not smtp_pass:
        print("⚠️ SMTP_USER o SMTP_PASSWORD no definidos; correo no enviado")
        return

    link_calendar = generar_link_calendar(nombre, email_cliente, dia, hora)
    asunto = f"Confirmación de demo - Rentals AI"
    cuerpo = f"""
    <html>
    <body style="font-family: Arial; background-color: #ffffff; color: #333;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 8px; padding: 20px;">
            <img src="https://drive.google.com/uc?export=view&id=13G29FFEEI8oK4zC1oSpgwA_-LM_T4KfL"
                 style="max-width: 150px; display:block; margin:auto;">
            <h2 style="color:#0b3d91; text-align:center;">Confirmación de tu demo en Rentals AI</h2>
            <p>Hola <strong>{nombre}</strong>,</p>
            <p>Gracias por agendar tu demo. Estos son los datos confirmados:</p>
            <ul>
                <li><b>Nombre:</b> {nombre}</li>
                <li><b>Email:</b> {email_cliente}</li>
                <li><b>Teléfono:</b> {telefono}</li>
                <li><b>Día:</b> {dia}</li>
                <li><b>Hora:</b> {hora}</li>
            </ul>
            <div style="text-align:center; margin-top:30px;">
                <a href="{link_calendar}" 
                   style="background-color:#0b3d91; color:white; padding:12px 25px; border-radius:6px; 
                          text-decoration:none; font-weight:bold;">
                   📅 Agendar en Google Calendar
                </a>
            </div>
            <p style="margin-top: 30px;">Te esperamos en tu demo. Si querés reprogramarla, respondé a este correo.</p>
            <p style="text-align:center; font-size:12px; color:#888;">© IA MOTORHUB 2025 · Rentals AI</p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = email_cliente
    msg["Bcc"] = smtp_user
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            print(f"✅ Email enviado a {email_cliente} y copia oculta a {smtp_user}")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

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
