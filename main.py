"""
Main application file with Telegram API handler (using requests) and Polling loop.
Déploiement sur Render.com en mode Web Service + Threaded Polling.
Le port 10000 est exposé via Gunicorn pour satisfaire Render.
"""

import os
import time
import logging
import requests
from flask import Flask 
from typing import Dict, Optional, List
from card_predictor import card_predictor, TARGET_CHANNEL_ID, PREDICTION_CHANNEL_ID
import threading

# --- Configuration et Initialisation ---

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Récupération du jeton et configuration de l'API
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.critical("BOT_TOKEN n'est pas configuré. Arrêt du bot.")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Chat ID pour l'alerte automatique
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID') 

# Flask setup (Écoute sur le port 10000)
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 10000)) 

# --- Classe d'Interaction avec l'API Telegram (tg_api) ---

class TelegramBotAPI:
    """Utility class to send messages and edits using requests."""

    def __init__(self, api_url):
        self.api_url = api_url
        self.last_update_id = 0

    def _request(self, method: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Generic method to send a request to the Telegram API."""
        url = self.api_url + method
        try:
            response = requests.post(url, json=data, timeout=5) 
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API Telegram ({method}): {e}")
            return None

    def send_message(self, chat_id: str, text: str, parse_mode: str = 'Markdown', reply_markup: Optional[Dict] = None) -> Optional[int]:
        """Sends a message and returns its message_id."""
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
        """Edits an existing message."""
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode,
            'reply_markup': reply_markup
        }
        self._request('editMessageText', data)

    def answer_callback_query(self, callback_query_id: str, text: str = ""):
        """Answers a callback query to remove the loading status."""
        data = {
            'callback_query_id': callback_query_id,
            'text': text
        }
        self._request('answerCallbackQuery', data)

    def get_updates(self, timeout: int = 20) -> Optional[List[Dict]]:
        """Retrieves new updates using polling."""
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

tg_api = TelegramBotAPI(API_URL)

# --- Gestionnaires de Commandes (Non modifiés) ---

def handle_start_command(chat_id):
    tg_api.send_message(chat_id, "Bot DAME PRÉDICTION démarré. Utilisez /status ou /help.", parse_mode=None)

def handle_help_command(chat_id):
    help_text = (
        "**🤖 COMMANDES :**\n"
        "/status - Affiche l'état du Mode Intelligent et les échecs.\n"
        "/inter - Analyse les déclencheurs de Dame et permet l'activation interactive de la stratégie.\n"
        "/defaut - Désactive le Mode Intelligent et réinitialise les règles.\n"
    )
    tg_api.send_message(chat_id, help_text)

def handle_status_command(chat_id):
    mode_status = "🟢 ACTIF (Règles appliquées)" if card_predictor.intelligent_mode_active else "🔴 INACTIF (Veille)"
    failure_count = card_predictor.consecutive_failures
    
    status_text = (
        "**📊 Statut du Predictor (Polling) :**\n"
        f"**Mode Intelligent :** {mode_status}\n"
        f"**Échecs consécutifs :** `{failure_count}/{card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE}`\n"
        f"Dernière prédiction Dame (Q): `{card_predictor.last_dame_prediction if card_predictor.last_dame_prediction else 'Aucune'}`\n"
    )
    tg_api.send_message(chat_id, status_text)

def handle_defaut_command(chat_id):
    card_predictor.intelligent_mode_active = False
    card_predictor.consecutive_failures = 0
    tg_api.send_message(chat_id, "✅ **Mode Intelligent DÉSACTIVÉ.** Les prédictions automatiques sont maintenant basées sur la règle initiale (Veille).")

def handle_inter_command(chat_id):
    """Analyse l'historique et demande l'activation du mode intelligent."""
    
    history = card_predictor.draw_history
    if not history or len(history) < 3:
        tg_api.send_message(chat_id, "Historique de tirage insuffisant (moins de 3 tirages complets). Attendez plus de résultats.")
        return

    analysis_list = []
    sorted_game_numbers = sorted(history.keys())
    
    for game_number in sorted_game_numbers:
        current_draw = history[game_number]
        
        if card_predictor.check_dame_in_first_group(current_draw.get('text', '')):
            trigger_number = game_number - 2
            trigger_draw = history.get(trigger_number)
            
            if trigger_draw:
                trigger_content = trigger_draw.get('first_two_cards', 'N/A')
                dame_content = current_draw.get('first_group', 'N/A')
                
                dame_match = re.search(r'\bQ[♥️♠️♦️♣️❤️]|Dame', dame_content)
                dame_card = dame_match.group(0) if dame_match else 'Q'
                
                analysis_list.append(
                    f"**Demandeur N{trigger_number}** : *{trigger_content}*\n"
                    f"Numéro reçu Dame N{game_number} 👉🏻 {dame_card}"
                )

    if analysis_list:
        analysis_output = "\n\n".join(analysis_list[-5:]) 
        alert_title = "**🚨 MODE INTELLIGENT REQUIS**" if card_predictor.consecutive_failures >= card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE else "**🔍 ANALYSE EN COURS**"
        
        message_text = (
            f"{alert_title}\n"
            "**🔍 ANALYSE DU CYCLE DE LA DAME : (N-2) → (N)**\n"
            "Voici les 5 derniers cycles observés (Demandeur = 2 premières cartes N-2) :\n\n"
            f"{analysis_output}\n\n"
            "---"
        )
    else:
        message_text = "🚨 **ALERTE.** Échecs potentiels atteints, mais historique N-2 → Q incomplet."

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ OUI (Activer Mode Intelligent)", "callback_data": "activate_intelligent_mode"},
                {"text": "❌ NON (Rester en veille)", "callback_data": "deactivate_intelligent_mode"}
            ]
        ]
    }

    tg_api.send_message(
        chat_id, 
        f"{message_text}\n\n**Voulez-vous modifier les règles de prédiction pour utiliser le Mode Intelligent (Stratégie K/J/A/JJ) ?**", 
        reply_markup=reply_markup
    )


def handle_callback_query(callback_query_id: str, chat_id: str, message_id: int, data: str):
    """Gère les réponses aux boutons 'Oui/Non'."""
    tg_api.answer_callback_query(callback_query_id)

    if data == 'activate_intelligent_mode':
        card_predictor.intelligent_mode_active = True
        card_predictor.consecutive_failures = 0
        new_text = "✅ **Mode Intelligent ACTIVÉ !** La stratégie (K/J/A/JJ) est maintenant appliquée pour les prédictions automatiques (N+2 ou N+3)."
    elif data == 'deactivate_intelligent_mode':
        card_predictor.intelligent_mode_active = False
        new_text = "❌ **Mode Intelligent DÉSACTIVÉ.** Les prédictions restent en mode Veille."
    else:
        new_text = "Action non reconnue."
        
    tg_api.edit_message_text(chat_id, message_id, new_text)

# --- Logique de Traitement Principal des Mises à Jour (Non modifiée) ---

def process_update(update: Dict):
    """Processes a single Telegram Update (Message or Callback)."""
    
    if 'message' in update or 'edited_message' in update:
        
        message_data = update.get('message') or update.get('edited_message')
        if not message_data: return
        
        text = message_data.get('text', '')
        chat_id = str(message_data['chat']['id'])
        message_id = message_data['message_id']
        
        # 1. Traitement des messages du canal source
        if chat_id == TARGET_CHANNEL_ID:
            
            verification_result = card_predictor.verify_prediction(text, message_id)
            
            if verification_result:
                
                # Cas 1. 2 échecs consécutifs atteints -> Déclenchement automatique
                if verification_result['type'] == 'fail_threshold_reached':
                    if ADMIN_CHAT_ID:
                        logger.info(f"Déclenchement automatique de /inter vers l'administrateur ({ADMIN_CHAT_ID}).")
                        handle_inter_command(ADMIN_CHAT_ID)
                    else:
                        logger.warning("ADMIN_CHAT_ID non configuré, le prompt automatique n'a pas été envoyé.")
                    return
                    
                # Cas 2. Succès ou échec final de la vérification
                elif verification_result['type'] == 'edit_message':
                    edit_result = verification_result
                    tg_api.send_message(
                        PREDICTION_CHANNEL_ID,
                        f"✅ **VÉRIFICATION TERMINÉE** pour N{edit_result['predicted_game']} (via message source):\n{edit_result['new_message']}"
                    )
            
            # Prédiction Automatique (uniquement si le Mode Intelligent est actif et le message n'est pas finalisé)
            should_predict, game_number, predicted_value = card_predictor.should_predict(text)
            if should_predict:
                prediction_data = card_predictor.make_prediction(game_number, predicted_value)
                tg_api.send_message(PREDICTION_CHANNEL_ID, prediction_data['text'])
        
        # 2. Traitement des commandes utilisateur (hors canaux source/prédiction)
        elif text.startswith('/') and chat_id != PREDICTION_CHANNEL_ID:
            if text.startswith('/start'):
                handle_start_command(chat_id)
            elif text.startswith('/help'):
                handle_help_command(chat_id)
            elif text.startswith('/status'):
                handle_status_command(chat_id)
            elif text.startswith('/inter'):
                handle_inter_command(chat_id)
            elif text.startswith('/defaut'):
                handle_defaut_command(chat_id)


    # Traitement des clics de boutons inline
    elif 'callback_query' in update:
        callback_query = update['callback_query']
        callback_query_id = callback_query['id']
        data = callback_query['data']
        chat_id = str(callback_query['message']['chat']['id'])
        message_id = callback_query['message']['message_id']
        
        handle_callback_query(callback_query_id, chat_id, message_id, data)


def polling_loop():
    """Main polling loop for the bot (runs in a separate thread)."""
    if not all([BOT_TOKEN, TARGET_CHANNEL_ID, PREDICTION_CHANNEL_ID]):
        logger.critical("Configuration manquante. Le Polling ne peut pas démarrer.")
        return
        
    logger.info("Bot Polling démarré en thread séparé.")
    
    # S'assurer que le Webhook est désactivé avant de commencer le Polling
    tg_api._request('deleteWebhook', data={'drop_pending_updates': True})
    
    while True:
        updates = tg_api.get_updates()
        if updates:
            for update in updates:
                process_update(update)
        time.sleep(1) 

# --- Démarrage du Bot ---

# Démarrer le Polling dans un thread séparé immédiatement
polling_thread = threading.Thread(target=polling_loop)
polling_thread.start()
logger.info("Thread de Polling lancé en arrière-plan.")

# Point d'entrée pour Gunicorn. Ceci permet à Render de voir l'application écouter le port 10000.
@app.route('/')
def home():
    """Endpoint pour le Health Check de Render."""
    return "Bot Predictor is running (Polling active in thread).", 200

application = app 

