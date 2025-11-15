import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration du Bot, avec IDs de canaux pré-configurés pour la stratégie DAME.
    """
    def __init__(self):
        # --- IDs de Canaux par défaut (Pré-Configurations) ---
        # Ces valeurs seront utilisées si les variables d'environnement (os.getenv) ne sont pas définies.
        
        # TARGET_CHANNEL_ID : Le canal où les tirages bruts sont postés (Canal Source)
        DEFAULT_TARGET_CHANNEL_ID = "-1003424179389"
        
        # PREDICTION_CHANNEL_ID : Le canal où le bot envoie ses analyses et prédictions
        DEFAULT_PREDICTION_CHANNEL_ID = "-1003362820311"

        # --- Variables Critiques du Bot ---
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID") # Votre ID personnel pour les commandes admin

        # --- Chargement des IDs de Canaux ---
        # Utilise la variable d'environnement si elle existe, sinon utilise la valeur par défaut
        self.TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID", DEFAULT_TARGET_CHANNEL_ID)
        self.PREDICTION_CHANNEL_ID = os.getenv("PREDICTION_CHANNEL_ID", DEFAULT_PREDICTION_CHANNEL_ID)

        # --- Variables Webhook/Serveur (Compatibilité) ---
        # Les variables WEBHOOK_URL et PORT sont conservées avec des valeurs par défaut
        # et utilisées si le bot est démarré en mode Webhook (ex: sur Render.com).
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
        self.PORT = int(os.getenv("PORT", "10000"))

        # --- Validation ---
        if not self.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN manquant. Le bot ne peut pas démarrer.")

    @property
    def webhook_path(self) -> str:
        """Construit le chemin complet du webhook."""
        return f"{self.WEBHOOK_URL}/webhook" if self.WEBHOOK_URL else ""

