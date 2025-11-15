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
from handlers import process_update

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
        "bot_token_configured": bool(config.BOT_TOKEN),
        "admin_chat_id": config.ADMIN_CHAT_ID
    }), 200

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Route principale pour recevoir les webhooks de Telegram"""
    global notification_sent
    
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
        
        # Envoyer la notification de déploiement au premier webhook (une seule fois)
        if not notification_sent and config.ADMIN_CHAT_ID:
            try:
                notification_message = (
                    "✅ **BOT DÉPLOYÉ AVEC SUCCÈS SUR RENDER.COM**\n\n"
                    "🌐 Mode : WEBHOOK\n"
                    f"📡 Canal Source : {config.TARGET_CHANNEL_ID}\n"
                    f"📤 Canal Prédiction : {config.PREDICTION_CHANNEL_ID}\n"
                    f"👤 Admin : {config.ADMIN_CHAT_ID}\n\n"
                    "✅ Le bot est opérationnel et attend les messages !"
                )
                bot.send_message(config.ADMIN_CHAT_ID, notification_message)
                logger.info("✅ Notification de déploiement envoyée à l'admin")
                notification_sent = True
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'envoi de la notification : {e}")
        
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

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Configure le webhook automatiquement"""
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    
    if not render_url:
        return jsonify({"status": "error", "message": "RENDER_EXTERNAL_URL non définie"}), 500
    
    webhook_url = f"https://{render_url}/webhook"
    
    if bot.set_webhook(webhook_url):
        return jsonify({
            "status": "success", 
            "message": f"✅ Webhook configuré : {webhook_url}"
        }), 200
    else:
        return jsonify({
            "status": "error", 
            "message": "❌ Échec de la configuration du webhook"
        }), 500

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook_route():
    """Supprime le webhook"""
    if bot.delete_webhook():
        return jsonify({"status": "success", "message": "Webhook supprimé"}), 200
    else:
        return jsonify({"status": "error", "message": "Échec de la suppression"}), 500

def configure_webhook_on_startup():
    """Configure le webhook automatiquement au démarrage"""
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    
    if not render_url:
        logger.error("❌ RENDER_EXTERNAL_URL non définie - Webhook non configuré")
        return False
    
    webhook_url = f"https://{render_url}/webhook"
    
    logger.info(f"🔧 Configuration automatique du webhook...")
    logger.info(f"📍 URL: {webhook_url}")
    
    # Attendre que le serveur soit prêt
    time.sleep(2)
    
    # Supprimer l'ancien webhook
    bot.delete_webhook()
    time.sleep(1)
    
    # Configurer le nouveau webhook
    if bot.set_webhook(webhook_url):
        logger.info(f"✅ Webhook configuré avec succès")
        
        # Envoyer un message de test à l'admin
        if config.ADMIN_CHAT_ID:
            test_message = (
                "🚀 **BOT DÉMARRÉ SUR RENDER.COM**\n\n"
                f"🌐 Webhook URL : {webhook_url}\n"
                f"📡 Canal Source : {config.TARGET_CHANNEL_ID}\n"
                f"📤 Canal Prédiction : {config.PREDICTION_CHANNEL_ID}\n\n"
                "✅ Configuration terminée - Le bot est prêt !"
            )
            bot.send_message(config.ADMIN_CHAT_ID, test_message)
            logger.info("✅ Message de test envoyé à l'admin")
        
        return True
    else:
        logger.error("❌ Échec de la configuration du webhook")
        return False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    logger.info("=" * 60)
    logger.info("🤖 BOT TELEGRAM DAME PRÉDICTION - MODE WEBHOOK")
    logger.info("=" * 60)
    logger.info(f"✅ Bot Token configuré")
    logger.info(f"✅ Admin Chat ID: {config.ADMIN_CHAT_ID}")
    logger.info(f"✅ Canal Source: {config.TARGET_CHANNEL_ID}")
    logger.info(f"✅ Canal Prédiction: {config.PREDICTION_CHANNEL_ID}")
    logger.info(f"✅ Port: {port}")
    logger.info("=" * 60)
    
    # Configuration automatique du webhook
    configure_webhook_on_startup()
    
    # Démarrer le serveur Flask
    logger.info(f"🚀 Démarrage du serveur Flask sur le port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
