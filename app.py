from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8334312092:AAGiK-6DEkboJHfEBFrv893SqfYBf09mps0"
TELEGRAM_CHAT_ID = "5392151099"

@app.route('/')
def home():
    return jsonify({"status": "online"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/webhook/elevenlabs', methods=['POST'])
def elevenlabs_webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        nombre = data.get('nombre', 'No especificado')
        telefono = data.get('telefono', 'No especificado')
        email = data.get('email', 'No especificado')
        dia = data.get('dia', 'No especificado')
        hora = data.get('hora', 'No especificado')
        mensaje = f"DEMO: {nombre} - {telefono} - {email} - {dia} {hora}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje})
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test')
def test():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": "TEST OK"})
    return jsonify({"status": "test_sent"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
