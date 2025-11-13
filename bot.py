"""
Implémentation de l'interaction avec l'API Telegram (Webhook et requêtes).
"""
import os
import time
import requests
import logging
from typing import Dict, Optional, List
from config import Config
from handlers import process_update # Non utilisé directement ici, mais le module est appelé

logger = logging.getLogger(__name__)

# La configuration sera chargée globalement ou passée à l'instance
config = Config()

class TelegramBot:
    """Gère les requêtes API Telegram."""

    def __init__(self, token: str):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.token = token
        
    def _request(self, method: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Méthode générique pour envoyer une requête à l'API Telegram."""
        url = self.api_url + method
        try:
            if not self.token:
                 return None 
            response = requests.post(url, json=data, timeout=5) 
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur API Telegram ({method}): {e}")
            return None

    def set_webhook(self, webhook_url: str) -> bool:
        """Configure l'URL du Webhook."""
        # drop_pending_updates=True résout l'erreur 409 Conflict en supprimant l'ancien Webhook
        data = {
            'url': webhook_url,
            'drop_pending_updates': True 
        }
        result = self._request('setWebhook', data)
        if result and result.get('ok'):
            logger.info(f"✅ Webhook configuré : {webhook_url}")
            return True
        else:
            logger.error(f"❌ Échec de la configuration du Webhook. Réponse : {result}")
            return False

    def delete_webhook(self) -> bool:
        """Supprime l'URL du Webhook (utile pour la réinitialisation ou le debug)."""
        data = {'drop_pending_updates': True}
        result = self._request('deleteWebhook', data)
        if result and result.get('ok'):
            logger.info("✅ Webhook supprimé avec succès.")
            return True
        else:
            logger.error(f"❌ Échec de la suppression du Webhook. Réponse : {result}")
            return False

    # --- Méthodes API ---
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = 'Markdown', reply_markup: Optional[Dict] = None) -> Optional[int]:
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'reply_markup': reply_markup
        }
        result = self._request('sendMessage', data)
        if result and result.get('ok') and 'result' in result:
            return result['result'].get('message_id')
        return None

    def edit_message_text(self, chat_id: str, message_id: int, text: str, parse_mode: str = 'Markdown', reply_markup: Optional[Dict] = None):
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode,
            'reply_markup': reply_markup
        }
        self._request('editMessageText', data)

    def answer_callback_query(self, callback_query_id: str, text: str = ""):
        data = {
            'callback_query_id': callback_query_id,
            'text': text
        }
        self._request('answerCallbackQuery', data)
        
