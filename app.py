from flask import Flask, request, jsonify
import requests
import os
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8334312092:AAGiK-6DEkboJHfEBFrv893SqfYBf09mps0"
TELEGRAM_CHAT_ID = "5392151099"

def extraer_datos_del_resumen(transcript):
    """
    Extrae datos del resumen estructurado que hace Matías
    Busca el patrón:
    🗛 RESUMEN DEMO:
    - Nombre: XXX
    - Email: XXX
    - Teléfono: XXX
    - Demo agendada: XXX a las XXX
    """
    datos = {
        'nombre': 'No especificado',
        'email': 'No especificado',
        'telefono': 'No especificado',
        'dia': 'No especificado',
        'hora': 'No especificado'
    }
    if not transcript:
        return datos
    resumen_match = re.search(r'🗛\\s*RESUMEN\\s*DEMO:?\\s*(.+?)(?=\\n\\n|\\Z)', transcript, re.DOTALL | re.IGNORECASE)
    if not resumen_match:
        resumen_match = re.search(r'🗛\\s*TUS\\s*DATOS:?\\s*(.+?)(?=\\n\\n|\\Z)', transcript, re.DOTALL | re.IGNORECASE)
    if resumen_match:
        bloque_resumen = resumen_match.group(1)
        nombre_match = re.search(r'-\\s*Nombre:\\s*(.+?)(?:\\n|$)', bloque_resumen, re.IGNORECASE)
        if nombre_match:
            datos['nombre'] = nombre_match.group(1).strip()
        email_match = re.search(r'-\\s*Email:\\s*(.+?)(?:\\n|$)', bloque_resumen, re.IGNORECASE)
        if email_match:
            datos['email'] = email_match.group(1).strip()
        telefono_match = re.search(r'-\\s*Tel[eé]fono:\\s*(.+?)(?:\\n|$)', bloque_resumen, re.IGNORECASE)
        if telefono_match:
            datos['telefono'] = telefono_match.group(1).strip()
        demo_match = re.search(r'-\\s*Demo\\s+agendada:\\s*(.+?)\\s+a\\s+las\\s+(.+?)(?:\\n|$)', bloque_resumen, re.IGNORECASE)
        if demo_match:
            datos['dia'] = demo_match.group(1).strip()
            datos['hora'] = demo_match.group(2).strip()
    return datos

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "Rentals AI Costa"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/test')
def test():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "🥪 TEST OK ✅"})
    return jsonify({"status": "test_sent"}), 200

@app.route('/webhook/elevenlabs', methods=['POST'])
def elevenlabs_webhook():
    try:
        # Try to get JSON data
        data = request.get_json(silent=True)
        if not data:
            # fallback to form-data
            data = request.form.to_dict()
        print("📥 WEBHOOK RECIBIDO:")
        print(f"Keys disponibles: {list(data.keys())}")
        print(f"Data completo: {data}")

        if not data:
            return jsonify({"error": "No data"}), 400

        # Try to get transcript fields from payload
        transcript = ""
        if 'transcript' in data:
            transcript = data['transcript']
        elif 'transcription' in data:
            transcript = data['transcription']
        elif 'text' in data:
            transcript = data['text']
        elif 'conversation' in data:
            transcript = data['conversation']

        print("📝 TRANSCRIPCIÓN DETECTADA: " + (transcript[:200] + "..." if transcript else ""))
        datos = extraer_datos_del_resumen(transcript)
        nombre = datos['nombre']
        telefono = datos['telefono']
        email = datos['email']
        dia = datos['dia']
        hora = datos['hora']

        conversation_id = data.get('conversation_id', 'N/A')
        print("✅ DATOS EXTRAÍDOS:")
        print(f"  - Nombre: {nombre}")
        print(f"  - Email: {email}")
        print(f"  - Teléfono: {telefono}")
        print(f"  - Día: {dia}")
        print(f"  - Hora: {hora}")

        mensaje_telegram = f"""🔥 DEMO AGENDADA - RENTALS AI

👤 Nombre: {nombre}
📝‍📞 Teléfono: {telefono}
📧 Email: {email}
📅 Fecha: {dia}
🍕 Hora: {hora}

🆚 ID: {conversation_id}
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

---
Rentals AI Costa - Monte Hermoso
Powered by IA MotorsHub"""

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        telegram_response = requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje_telegram})
        print(f"📱 Telegram enviado: {telegram_response.status_code}")

        # send email if environment variables for SMTP are set
        try:
            email_user = os.environ.get('SMTP_USER')
            email_pass = os.environ.get('SMTP_PASSWORD')
            email_to = os.environ.get('EMAIL_TO', 'contacto@iamotorshub.com')
            smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            if email_user and email_pass:
                msg = MIMEText(mensaje_telegram, "plain", "utf-8")
                msg['Subject'] = "🔥 DEMO AGENDADA - RENTALS AI"
                msg['From'] = email_user
                msg['To'] = email_to
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(email_user, email_pass)
                    server.sendmail(email_user, [email_to], msg.as_string())
                print("📧 Email enviado correctamente")
            else:
                print("⚠️ SMTP_USER o SMTP_PASSWORD no definidos; correo no enviado")
        except Exception as e:
            print(f"❌ Error al enviar correo: {e}")

        return jsonify({
            "status": "success",
            "data": {
                "nombre": nombre,
                "telefono": telefono,
                "email": email,
                "dia": dia,
                "hora": hora
            }
        }), 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
