"""
Fichier de configuration : Charge les variables d'environnement
Avec IDs pré-configurés pour le déploiement
"""
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        # IDs pré-configurés (peuvent être surchargés par les variables d'environnement)
        DEFAULT_TARGET_CHANNEL_ID = "-1003424179389"
        DEFAULT_PREDICTION_CHANNEL_ID = "-1003362820311"
        
        self.BOT_TOKEN = os.environ.get('BOT_TOKEN')
        self.TARGET_CHANNEL_ID = os.environ.get('TARGET_CHANNEL_ID', DEFAULT_TARGET_CHANNEL_ID)
        self.PREDICTION_CHANNEL_ID = os.environ.get('PREDICTION_CHANNEL_ID', DEFAULT_PREDICTION_CHANNEL_ID)
        self.ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')
        self.PORT = int(os.environ.get('PORT', 10000))
        
        # Validation et logs détaillés
        logger.info("=" * 50)
        logger.info("🔧 Configuration du Bot")
        logger.info("=" * 50)
        
        if not self.BOT_TOKEN:
            logger.critical("❌ BOT_TOKEN n'est pas configuré - Le bot ne peut pas démarrer")
        else:
            logger.info(f"✅ BOT_TOKEN configuré (longueur: {len(self.BOT_TOKEN)})")
        
        logger.info(f"✅ TARGET_CHANNEL_ID: {self.TARGET_CHANNEL_ID} (pré-configuré)")
        logger.info(f"✅ PREDICTION_CHANNEL_ID: {self.PREDICTION_CHANNEL_ID} (pré-configuré)")
        
        if not self.ADMIN_CHAT_ID:
            logger.warning("⚠️ ADMIN_CHAT_ID non configuré")
        else:
            logger.info(f"✅ ADMIN_CHAT_ID: {self.ADMIN_CHAT_ID}")
        
        logger.info(f"✅ PORT: {self.PORT}")
        logger.info("=" * 50)
