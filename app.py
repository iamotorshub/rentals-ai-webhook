from flask import Flask, request, jsonify
import os
import re
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# 🔐 Configuración Telegram
TELEGRAM_BOT_TOKEN = "8334312092:AAGiK-6DEkboJHfEBFrv893SqfYBf09mps0"
TELEGRAM_CHAT_ID = "5392151099"

# 🔐 Configuración Email
REMITENTE = "contacto@iamotorshub.com"
COPIA_OCULTA = "contacto@iamotorshub.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "motorhub2024!")  # o App Password si Gmail usa 2FA

# 🖼️ Logo IA MotorHub (Drive público)
LOGO_URL = "https://drive.google.com/uc?export=view&id=13G29FFEEI8oK4zC1oSpgwA_-LM_T4KfL"

# 🧠 Extraer datos del resumen
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


# 📧 Envío de correo con plantilla HTML elegante
def enviar_mail_confirmacion(nombre, email_cliente, telefono, dia, hora):
    try:
        evento_text = "Demo Rentals AI"
        detalles = f"Confirmación de demo con Matías de Rentals AI. Teléfono: {telefono}"
        link_calendar = (
            "https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={evento_text.replace(' ', '+')}"
            f"&details={detalles.replace(' ', '+')}"
            f"&dates={dia.replace('-', '')}T{hora.replace(':', '')}00Z/{dia.replace('-', '')}T{hora.replace(':', '')}00Z"
        )

        html_body = f"""
        <html>
        <body style="font-family: 'Segoe UI', Roboto, sans-serif; background-color: #ffffff; color: #333; padding: 40px;">
            <div style="max-width:600px;margin:auto;border:1px solid #eee;border-radius:14px;box-shadow:0 4px 15px rgba(0,0,0,0.08);">
                <div style="text-align:center;padding:20px 20px 0;">
                    <img src="{LOGO_URL}" alt="IA MotorHub" style="width:160px;"/>
                </div>
                <div style="padding:30px 40px 40px;">
                    <h2 style="color:#1e3c57;">Confirmación de tu demo con Rentals AI</h2>
                    <p style="font-size:16px;color:#555;">Hola <strong>{nombre}</strong>,</p>
                    <p style="font-size:15px;color:#555;">
                        ¡Gracias por agendar tu demo con <strong>Rentals AI</strong>!<br>
                        Te confirmamos los detalles:
                    </p>
                    <div style="background:#f7f9fb;padding:15px;border-radius:10px;margin-top:15px;">
                        <p style="margin:0;color:#333;">📅 <strong>Día:</strong> {dia}</p>
                        <p style="margin:0;color:#333;">🕐 <strong>Hora:</strong> {hora}</p>
                        <p style="margin:0;color:#333;">📞 <strong>Teléfono:</strong> {telefono}</p>
                    </div>
                    <p style="margin-top:25px;font-size:15px;">
                        Podés agendarlo directamente en tu calendario desde este enlace:<br><br>
                        <a href="{link_calendar}" style="background-color:#0078d7;color:#fff;padding:12px 22px;border-radius:6px;text-decoration:none;">
                            📆 Agendar en Google Calendar
                        </a>
                    </p>
                    <p style="margin-top:25px;color:#777;font-size:14px;">
                        ¡Nos vemos en la demo!<br>
                        <strong>Equipo Rentals AI</strong><br>
                        <span style="color:#1e3c57;">IA MotorHub</span>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "✅ Confirmación de demo Rentals AI"
        msg["From"] = REMITENTE
        msg["To"] = email_cliente
        msg["Bcc"] = COPIA_OCULTA

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(REMITENTE, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email HTML enviado a {email_cliente} (BCC a {COPIA_OCULTA})")

    except Exception as e:
        print("❌ Error al enviar email:", e)


# 🧩 Webhook principal
@app.route('/webhook/elevenlabs', methods=['POST'])
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    transcript = data.get('transcript', '')

    datos_resumen = extraer_datos_del_resumen(transcript)

    nombre = data.get('nombre') or datos_resumen['nombre']
    email_val = data.get('email') or datos_resumen['email']
    telefono = data.get('telefono') or datos_resumen['telefono']
    dia = data.get('dia') or datos_resumen['dia']
    hora = data.get('hora') or datos_resumen['hora']

    enviar_mensaje_telegram(nombre, email_val, telefono, dia, hora)
    enviar_mail_confirmacion(nombre, email_val, telefono, dia, hora)

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
