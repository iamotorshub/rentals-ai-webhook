from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8334312092:AAGiK-6DEkboJHfEBFrv893SqfYBf09mps0"
TELEGRAM_CHAT_ID = "5392151099"

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "Rentals AI Costa"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/test')
def test():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "🧪 TEST OK ✅"})
    return jsonify({"status": "test_sent"}), 200

@app.route('/webhook/elevenlabs', methods=['POST'])
def elevenlabs_webhook():
    try:
        data = request.get_json()
        
        # Log completo para debug
        print(f"📥 WEBHOOK RECIBIDO: {data}")
        
        if not data:
            return jsonify({"error": "No data"}), 400
        
        # Extraer datos
        nombre = data.get('nombre', 'No especificado')
        telefono = data.get('telefono', 'No especificado')
        email = data.get('email', 'No especificado')
        dia = data.get('dia', 'No especificado')
        hora = data.get('hora', 'No especificado')
        conversation_id = data.get('conversation_id', 'N/A')
        
        # Mensaje para Telegram
        mensaje_telegram = f"""🔥 DEMO AGENDADA - RENTALS AI

👤 Nombre: {nombre}
📱 Teléfono: {telefono}
📧 Email: {email}
📅 Fecha: {dia}
🕐 Hora: {hora}

🆔 ID: {conversation_id}
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

---
Rentals AI Costa - Monte Hermoso"""

        # Email HTML
        email_html = f"""
        <h2>🔥 NUEVA DEMO AGENDADA - RENTALS AI COSTA</h2>
        
        <p><strong>👤 Nombre:</strong> {nombre}</p>
        <p><strong>📱 Teléfono:</strong> {telefono}</p>
        <p><strong>📧 Email:</strong> {email}</p>
        <p><strong>📅 Fecha:</strong> {dia}</p>
        <p><strong>🕐 Hora:</strong> {hora}</p>
        
        <hr>
        <p><strong>🆔 ID Conversación:</strong> {conversation_id}</p>
        <p><strong>⏰ Recibido:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <hr>
        <p><em>Rentals AI Costa - Monte Hermoso<br>
        Powered by IA MotorsHub - Bahía Blanca</em></p>
        """
        
        # Enviar Telegram
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        telegram_response = requests.post(telegram_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje_telegram})
        
        # Enviar Email (usando SendGrid o SMTP - necesitás configurar)
        # Por ahora solo logueo
        print(f"📧 EMAIL HTML: {email_html}")
        
        print(f"✅ Demo: {nombre} - {dia} {hora}")
        print(f"📱 Telegram enviado: {telegram_response.status_code}")
        
        return jsonify({"status": "success", "data": {"nombre": nombre, "telefono": telefono, "email": email}}), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

**Commit changes**

Render va a re-deployar automáticamente.

---

## 📝 PASO 2: MODIFICAR PROMPT DE MATÍAS

El problema es que ElevenLabs NO está guardando las variables. Necesitamos ser MÁS EXPLÍCITOS.

En el prompt de Matías, **AL PRINCIPIO**, agregá esto:
```
# INSTRUCCIONES DE VARIABLES (CRÍTICO)

Cuando captures información del cliente, GUARDÁ en estas variables:

- Cuando te diga su nombre completo → GUARDÁ en variable: nombre
- Cuando te diga su email → GUARDÁ en variable: email  
- Cuando te diga su teléfono → GUARDÁ en variable: telefono
- Cuando agende día de demo → GUARDÁ en variable: dia
- Cuando agende hora de demo → GUARDÁ en variable: hora

Ejemplo:
Cliente: "Me llamo Juan Pérez"
Acción interna: [guardar "Juan Pérez" en variable nombre]

Cliente: "Mi email es juan@example.com"
Acción interna: [guardar "juan@example.com" en variable email]
