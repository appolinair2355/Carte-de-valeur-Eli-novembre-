import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration du Bot, optimisée pour le mode Polling.
    """
    def __init__(self):
        # Jeton d'API (Nécessaire)
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        
        # IDs des chats/canaux (Nécessaires au fonctionnement de la logique)
        # Note: Les valeurs par défaut ne sont utilisées qu'en l'absence de variables d'environnement.
        self.ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
        self.TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID", "-1003424179389")
        self.PREDICTION_CHANNEL_ID = os.getenv("PREDICTION_CHANNEL_ID", "-1003362820311")

        # Variables Webhook/Serveur (Gardées pour la compatibilité, mais généralement non utilisées en Polling)
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
        self.PORT = int(os.getenv("PORT", "10000"))

        # Validation critique
        if not self.BOT_TOKEN:
            # Leve une erreur pour empêcher le bot de démarrer sans token
            raise ValueError("❌ BOT_TOKEN manquant. Le bot ne peut pas démarrer sans jeton d'API.")
        
        # Logs pour le débogage
        logger.info("=" * 50)
        logger.info("🔧 Configuration du Bot (Format Simplifié)")
        logger.info(f"✅ BOT_TOKEN configuré (longueur: {len(self.BOT_TOKEN)})")
        logger.info(f"✅ ADMIN_CHAT_ID: {self.ADMIN_CHAT_ID or '⚠️ Manquant/Non utilisé en Polling par défaut'}")
        logger.info(f"✅ TARGET_CHANNEL_ID: {self.TARGET_CHANNEL_ID}")
        logger.info(f"✅ PREDICTION_CHANNEL_ID: {self.PREDICTION_CHANNEL_ID}")
        logger.info("=" * 50)


    @property
    def webhook_path(self) -> str:
        """Construit le chemin complet du webhook (pour le mode Webhook si réactivé)."""
        return f"{self.WEBHOOK_URL}/webhook" if self.WEBHOOK_URL else ""
        
