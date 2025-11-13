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
    return jsonify({"message": "Telegram Bot Predictor is running (Webhook mode)", "status": "active"}), 200

# --- Route de Configuration Webhook (Utile pour le setup) ---
# NOTE: RENDER_EXTERNAL_URL est une variable d'environnement injectée par Render
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL') 

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Configure le Webhook vers l'URL externe de Render (à appeler une fois)."""
    if not RENDER_EXTERNAL_URL:
        return jsonify({"status": "error", "message": "RENDER_EXTERNAL_URL non défini. Redémarrez le service ou ajoutez la variable manuellement."}), 500
    
    webhook_url = f"https://{RENDER_EXTERNAL_URL}/webhook"
    
    if bot.set_webhook(webhook_url):
        return jsonify({"status": "success", "message": f"Webhook configuré vers {webhook_url}"}), 200
    else:
        return jsonify({"status": "error", "message": "Échec de la configuration du Webhook (voir les logs pour l'erreur API)."}), 500

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
    if not request.is_json:
        return jsonify({"status": "error", "message": "Format de requête invalide"}), 400
    
    update = request.get_json()
    
    if update:
        # Passer l'instance du bot au gestionnaire pour qu'il puisse répondre
        try:
            process_update(bot, update)
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de l'update: {e}")
            # Toujours répondre 200 OK pour éviter les renvois de Telegram
    
    # Telegram attend toujours une réponse 200 OK pour accuser réception de l'update.
    return jsonify({"status": "ok"}), 200

# --- Lancement du Programme ---

if __name__ == '__main__':
    port = config.PORT
    logger.info(f"🚀 Démarrage du serveur Flask Webhook sur le port {port}.")
    
    # app.run() n'est utilisé que pour les tests locaux (non exécuté par Gunicorn)
    app.run(host="0.0.0.0", port=port, debug=False)
        
