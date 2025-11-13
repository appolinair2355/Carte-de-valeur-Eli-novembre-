"""
Point d'entrée principal (main.py)
Gère l'initialisation de l'application Flask et le lancement du bot 
en mode Polling dans un thread séparé (Web Service requis par Render).
"""

import os
import logging
from threading import Thread
from flask import Flask, jsonify 
from config import Config
from bot import TelegramBot # Importe la classe bot.TelegramBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Fonction pour le Polling du Bot (Exécuté dans le Thread) ---
def run_bot(token: str):
    """Initialise et lance la boucle de Polling du bot dans un thread."""
    try:
        bot = TelegramBot(token) 
        logger.info("🤖 Lancement de la boucle de Polling du bot.")
        bot.start_polling() 
    except Exception as e:
        logger.critical(f"❌ Erreur critique dans le thread du bot: {e}")

# --- Application Flask Minimale pour le Health Check et le Port ---
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Endpoint requis par Render pour vérifier que le service est actif."""
    return jsonify({"status": "healthy", "bot_mode": "polling (threaded)"}), 200

@app.route('/', methods=['GET'])
def home():
    """Page d'accueil simple."""
    return jsonify({"message": "Telegram Bot Predictor is running (Polling mode)", "status": "active"}), 200

# Ceci est le point d'entrée pour Gunicorn (Web Service)
application = app 

# --- Lancement du Programme ---
if __name__ == '__main__':
    try:
        config = Config()
        
        if not config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN n'est pas configuré.")

        # 1. Démarrer le bot dans un thread séparé
        bot_thread = Thread(target=run_bot, args=(config.BOT_TOKEN,))
        bot_thread.daemon = True 
        bot_thread.start()
        logger.info("✅ Le thread du Bot a démarré.")

        # 2. Démarrer Flask sur le port requis par l'hébergeur (10000)
        port = config.PORT
        logger.info(f"🚀 Démarrage du serveur Flask minimal sur le port {port} (pour le Health Check).")
        
        # app.run() n'est utilisé que pour les tests locaux (non exécuté par Gunicorn)
        app.run(host="0.0.0.0", port=port, debug=False)

    except ValueError as ve:
        logger.critical(f"❌ Erreur de configuration : {ve}.")
    except Exception as e:
        logger.critical(f"❌ Échec critique au démarrage: {e}")
        
