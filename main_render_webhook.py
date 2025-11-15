"""
Point d'entrée pour Render.com - MODE WEBHOOK
Le bot utilise Flask pour recevoir les webhooks de Telegram
Notification automatique après déploiement
"""

import os
import logging
import time
import requests
from flask import Flask, request, jsonify
from config import Config
from bot import TelegramBot
# --- CORRECTION DE L'IMPORTATION (handle_update est la bonne fonction) ---
import handlers 
from handlers import handle_update # Importez la bonne fonction 'handle_update'

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Initialisation ---
config = Config()

if not config.BOT_TOKEN:
    logger.critical("❌ FATAL - BOT_TOKEN n'est pas configuré")
    exit(1)

bot = TelegramBot(config.BOT_TOKEN)

# --- Application Flask ---
app = Flask(__name__)
application = app  # Pour Gunicorn

# Variable globale pour tracker si la notification a été envoyée
notification_sent = False

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé requis par Render"""
    return jsonify({"status": "healthy", "bot_mode": "webhook"}), 200

@app.route('/', methods=['GET'])
def home():
    """Page d'accueil avec informations sur le webhook"""
    webhook_url = os.environ.get('RENDER_EXTERNAL_URL')
    webhook_info = f"https://{webhook_url}/webhook" if webhook_url else "Non configuré"
    
    return jsonify({
        "message": "🤖 Bot Telegram DAME - Mode Webhook",
        "status": "active",
        "webhook_url": webhook_info,
        "admin_chat_id": config.ADMIN_CHAT_ID
    }), 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Configure le webhook sur Telegram"""
    webhook_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not webhook_url:
        return jsonify({"status": "error", "message": "RENDER_EXTERNAL_URL non trouvé."}), 500
    
    # Construction de l'URL du webhook
    full_webhook_url = f"https://{webhook_url}/webhook"
    
    # Configuration du webhook
    if bot.set_webhook(full_webhook_url):
        return jsonify({"status": "success", "message": f"Webhook défini sur {full_webhook_url}"}), 200
    else:
        return jsonify({"status": "error", "message": "Échec de la configuration du webhook Telegram."}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint principal pour la réception des mises à jour Telegram"""
    # --- CORRECTION DE LA RÉCUPÉRATION DU JSON (Force la lecture du JSON) ---
    update = request.get_json(silent=True, force=True) 
    
    if update:
        # LOG BRUT AJOUTÉ POUR CONFIRMER LA RÉCEPTION (avant le traitement)
        update_type = list(update.keys())[0] if update else "VIDE"
        logger.info(f"🚨 UPDATE REÇU (Type): {update_type}") 
        
        try:
            # Appel de la fonction de gestion des mises à jour corrigée
            handle_update(bot, update) # <-- APPEL DE LA BONNE FONCTION
        except Exception as e:
            logger.error(f"❌ Erreur critique lors du traitement de l'update: {e}")
            import traceback
            logger.error(traceback.format_exc()) 
            
    # Telegram s'attend toujours à une réponse HTTP 200 pour confirmer la réception
    return jsonify({'status': 'ok'}), 200

def run_setup(webhook_url):
    """Effectue les actions de configuration après le démarrage."""
    
    if bot.set_webhook(webhook_url):
        logger.info(f"✅ Webhook configuré avec succès")
        
        # Envoyer un message de test à l'admin
        if config.ADMIN_CHAT_ID:
            test_message = (
                "🚀 **BOT DÉMARRÉ SUR RENDER.COM**\\n\\n"
                f"🌐 Webhook URL : {webhook_url}\\n"
                f"📡 Canal Source : {config.TARGET_CHANNEL_ID}\\n"
                f"📤 Canal Prédiction : {config.PREDICTION_CHANNEL_ID}\\n\\n"
                "✅ Configuration terminée - Le bot est prêt !"
            )
            bot.send_message(config.ADMIN_CHAT_ID, test_message, parse_mode='Markdown')
            logger.info("✅ Message de test envoyé à l'admin")
        
        return True
    else:
        logger.error("❌ Échec de la configuration du webhook")
        return False

if __name__ == '__main__':
    port = config.PORT
    
    logger.info("=" * 60)
    logger.info("🤖 BOT TELEGRAM DAME PRÉDICTION - MODE WEBHOOK")
    logger.info("=" * 60)
    logger.info(f"✅ Bot Token configuré")
    logger.info(f"✅ Admin Chat ID: {config.ADMIN_CHAT_ID}")
    logger.info(f"✅ Canal Source: {config.TARGET_CHANNEL_ID}")
    logger.info(f"✅ Canal Prédiction: {config.PREDICTION_CHANNEL_ID}")
    logger.info(f"✅ Port : {port}")
    
    # Lance le setup après un court délai pour que Render attribue l'URL externe
    time.sleep(3) 
    webhook_url = os.environ.get('RENDER_EXTERNAL_URL')
    
    if webhook_url:
        run_setup(f"https://{webhook_url}/webhook")
        
    app.run(host='0.0.0.0', port=port)



