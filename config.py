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
        self.PORT = int(os.environ.get('PORT', 5000))
        
        # Validation et logs détaillés
        logger.info("=" * 50)
        logger.info("🔧 Configuration du Bot")
        logger.info("=" * 50)
        
        if not self.BOT_TOKEN:
            logger.critical("❌ BOT_TOKEN n'est pas configuré - Le bot ne peut pas démarrer")
        else:
            logger.info(f"✅ BOT_TOKEN configuré (longueur: {len(self.BOT_TOKEN)})")
        
        if not self.TARGET_CHANNEL_ID:
            logger.warning("⚠️ TARGET_CHANNEL_ID non configuré")
        else:
            logger.info(f"✅ TARGET_CHANNEL_ID: {self.TARGET_CHANNEL_ID}")
        
        if not self.PREDICTION_CHANNEL_ID:
            logger.warning("⚠️ PREDICTION_CHANNEL_ID non configuré")
        else:
            logger.info(f"✅ PREDICTION_CHANNEL_ID: {self.PREDICTION_CHANNEL_ID}")
        
        if not self.ADMIN_CHAT_ID:
            logger.warning("⚠️ ADMIN_CHAT_ID non configuré")
        else:
            logger.info(f"✅ ADMIN_CHAT_ID: {self.ADMIN_CHAT_ID}")
        
        logger.info(f"✅ PORT: {self.PORT}")
        logger.info("=" * 50)
          
