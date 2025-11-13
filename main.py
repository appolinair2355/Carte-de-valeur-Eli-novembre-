"""
Point d'entrée principal (main.py)
Gère l'initialisation de l'application Flask et l'écoute du Webhook.
"""

import os
import logging
from flask import Flask, jsonify, request
from config import Config
from bot import TelegramBot
from handlers import process_update # La logique de traitement est appelée ici

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Initialisation ---
config = Config()

if not config.BOT_TOKEN:
    logger.critical("❌ FATAL - BOT_TOKEN n'est pas configuré. Le bot ne peut pas démarrer.")
    config.BOT_TOKEN = ""

# Créer l'instance du bot pour l'API Telegram
bot = TelegramBot(config.BOT_TOKEN)

# --- Application Flask ---
app = Flask(__name__)
application = app # Pour Gunicorn (Web Service)

# --- Routes Standardes ---

@app.route('/health', methods=['GET'])
def health():
    """Endpoint requis par Render pour vérifier que le service est actif."""
    return jsonify({"status": "healthy", "bot_mode": "webhook"}), 200

@app.route('/', methods=['GET'])
def home():
    """Page d'accueil."""
    webhook_info_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/getWebhookInfo"
    try:
        import requests
        response = requests.get(webhook_info_url, timeout=5)
        webhook_info = response.json() if response.status_code == 200 else {}
    except:
        webhook_info = {}
    
    return jsonify({
        "message": "Telegram Bot Predictor is running (Webhook mode)", 
        "status": "active",
        "webhook_configured": webhook_info.get('result', {}).get('url', 'Non configuré'),
        "bot_token_configured": bool(config.BOT_TOKEN)
    }), 200

@app.route('/test_bot', methods=['GET'])
def test_bot():
    """Teste si le bot peut envoyer un message à l'admin."""
    if not config.ADMIN_CHAT_ID:
        return jsonify({"status": "error", "message": "ADMIN_CHAT_ID non configuré"}), 500
    
    try:
        test_message = "🧪 Test du bot - Le bot fonctionne correctement !"
        message_id = bot.send_message(config.ADMIN_CHAT_ID, test_message)
        if message_id:
            return jsonify({"status": "success", "message": "Message de test envoyé à l'admin"}), 200
        else:
            return jsonify({"status": "error", "message": "Échec de l'envoi du message"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Route de Configuration Webhook (Utile pour le setup) ---
# NOTE: REPLIT_DEV_DOMAIN est une variable d'environnement sur Replit
REPLIT_DEV_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN')
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL')
EXTERNAL_URL = REPLIT_DEV_DOMAIN or RENDER_EXTERNAL_URL

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Configure le Webhook vers l'URL externe (Replit ou Render)."""
    if not EXTERNAL_URL:
        return jsonify({"status": "error", "message": "URL externe non définie. Vérifiez les variables d'environnement."}), 500
    
    webhook_url = f"https://{EXTERNAL_URL}/webhook"
    
    if bot.set_webhook(webhook_url):
        return jsonify({"status": "success", "message": f"✅ Webhook configuré avec succès vers : {webhook_url}"}), 200
    else:
        return jsonify({"status": "error", "message": "❌ Échec de la configuration du Webhook (voir les logs pour l'erreur API)."}), 500

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook_route():
    """Supprime le Webhook (pour revenir au Polling ou réinitialiser - résout l'erreur 409)."""
    if bot.delete_webhook():
        return jsonify({"status": "success", "message": "Webhook supprimé avec succès."}), 200
    else:
        return jsonify({"status": "error", "message": "Échec de la suppression du Webhook."}), 500

# --- Route Principale du Webhook ---

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Route écoutant les updates POST envoyées par Telegram."""
    try:
        logger.info("📨 Webhook appelé - Requête reçue")
        
        if not request.is_json:
            logger.warning("⚠️ Requête non-JSON reçue")
            return jsonify({"status": "ok"}), 200
        
        update = request.get_json()
        
        if not update:
            logger.warning("⚠️ Update vide reçu")
            return jsonify({"status": "ok"}), 200
        
        logger.info("📥 Update reçu de Telegram")
        
        try:
            process_update(bot, update)
            logger.info("✅ Update traité avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de l'update: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur critique dans telegram_webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"status": "ok"}), 200

# --- Lancement du Programme ---

if __name__ == '__main__':
    port = config.PORT
    logger.info(f"🚀 Démarrage du serveur Flask Webhook sur le port {port}.")
    
    # app.run() n'est utilisé que pour les tests locaux (non exécuté par Gunicorn)
    app.run(host="0.0.0.0", port=port, debug=False)
        
