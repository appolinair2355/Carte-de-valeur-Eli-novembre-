"""
Implémentation de l'interaction avec l'API Telegram et de la boucle de Polling.
"""
import os
import time
import requests
import logging
from typing import Dict, Optional, List
from config import Config
from handlers import process_update # Importe le gestionnaire d'updates

logger = logging.getLogger(__name__)

# La configuration sera chargée dans l'instance
config = Config()

class TelegramBot:
    """Gère les requêtes API Telegram et la boucle de Polling."""

    def __init__(self, token: str):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.last_update_id = 0

    def _request(self, method: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Méthode générique pour envoyer une requête à l'API Telegram."""
        url = self.api_url + method
        try:
            if not config.BOT_TOKEN:
                 return None 
            response = requests.post(url, json=data, timeout=5) 
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur API Telegram ({method}): {e}")
            return None

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

    def get_updates(self, timeout: int = 20) -> Optional[List[Dict]]:
        data = {
            'timeout': timeout,
            'offset': self.last_update_id + 1
        }
        result = self._request('getUpdates', data)
        if result and result.get('ok') and 'result' in result:
            updates = result['result']
            if updates:
                self.last_update_id = updates[-1]['update_id']
            return updates
        return None

    def start_polling(self):
        """Boucle principale de Polling (méthode bloquante)."""
        if not config.BOT_TOKEN or not config.TARGET_CHANNEL_ID or not config.PREDICTION_CHANNEL_ID:
            logger.critical("Configuration manquante. Le Polling ne peut pas démarrer.")
            return

        logger.info("Bot Polling démarré.")
        
        # S'assurer que le Webhook est désactivé avant de commencer le Polling
        self._request('deleteWebhook', data={'drop_pending_updates': True})
        
        while True:
            updates = self.get_updates()
            if updates:
                for update in updates:
                    # Passe l'instance du bot au gestionnaire pour les réponses
                    process_update(self, update) 
            time.sleep(1) 
