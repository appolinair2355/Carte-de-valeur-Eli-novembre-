"""
Fichier de configuration : Charge les variables d'environnement
"""
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.BOT_TOKEN = os.environ.get('BOT_TOKEN')
        self.TARGET_CHANNEL_ID = os.environ.get('TARGET_CHANNEL_ID')
        self.PREDICTION_CHANNEL_ID = os.environ.get('PREDICTION_CHANNEL_ID')
        self.ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')
        self.PORT = int(os.environ.get('PORT', 10000))
        
        if not self.BOT_TOKEN:
            logger.critical("BOT_TOKEN n'est pas configuré.")
        if not self.TARGET_CHANNEL_ID or not self.PREDICTION_CHANNEL_ID:
            logger.warning("IDs de canaux non configurés. Le bot ne pourra pas interagir avec les canaux.")
          
