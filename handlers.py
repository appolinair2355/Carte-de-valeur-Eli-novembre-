"""
Contient les gestionnaires de commandes et la logique de traitement des mises à jour.
"""

import os
import re
import logging
from typing import Dict, Optional
from card_predictor import card_predictor
from config import Config

logger = logging.getLogger(__name__)
config = Config()

# --- Gestionnaires de Commandes ---
# Chaque handler prend l'instance du bot et le chat_id

def handle_start_command(bot, chat_id):
    bot.send_message(chat_id, "Bot DAME PRÉDICTION démarré. Utilisez /status ou /help.", parse_mode=None)

def handle_help_command(bot, chat_id):
    help_text = (
        "**🤖 COMMANDES :**\n"
        "/status - Affiche l'état du Mode Intelligent et les échecs.\n"
        "/inter - Analyse les déclencheurs de Dame et permet l'activation interactive de la stratégie.\n"
        "/defaut - Désactive le Mode Intelligent et réinitialise les règles.\n"
    )
    bot.send_message(chat_id, help_text)

def handle_status_command(bot, chat_id):
    mode_status = "🟢 ACTIF (Règles appliquées)" if card_predictor.intelligent_mode_active else "🔴 INACTIF (Veille)"
    failure_count = card_predictor.consecutive_failures
    
    status_text = (
        "**📊 Statut du Predictor (Polling) :**\n"
        f"**Mode Intelligent :** {mode_status}\n"
        f"**Échecs consécutifs :** `{failure_count}/{card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE}`\n"
        f"Dernière prédiction Dame (Q): `{card_predictor.last_dame_prediction if card_predictor.last_dame_prediction else 'Aucune'}`\n"
    )
    bot.send_message(chat_id, status_text)

def handle_defaut_command(bot, chat_id):
    card_predictor.intelligent_mode_active = False
    card_predictor.consecutive_failures = 0
    bot.send_message(chat_id, "✅ **Mode Intelligent DÉSACTIVÉ.** Les prédictions automatiques sont maintenant basées sur la règle initiale (Veille).")

def handle_inter_command(bot, chat_id):
    """Analyse l'historique et demande l'activation du mode intelligent."""
    
    history = card_predictor.draw_history
    if not history or len(history) < 3:
        bot.send_message(chat_id, "Historique de tirage insuffisant (moins de 3 tirages complets). Attendez plus de résultats.")
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

    bot.send_message(
        chat_id, 
        f"{message_text}\n\n**Voulez-vous modifier les règles de prédiction pour utiliser le Mode Intelligent (Stratégie K/J/A/JJ) ?**", 
        reply_markup=reply_markup
    )


def handle_callback_query(bot, callback_query_id: str, chat_id: str, message_id: int, data: str):
    """Gère les réponses aux boutons 'Oui/Non'."""
    bot.answer_callback_query(callback_query_id)

    if data == 'activate_intelligent_mode':
        card_predictor.intelligent_mode_active = True
        card_predictor.consecutive_failures = 0
        new_text = "✅ **Mode Intelligent ACTIVÉ !** La stratégie (K/J/A/JJ) est maintenant appliquée pour les prédictions automatiques (N+2 ou N+3)."
    elif data == 'deactivate_intelligent_mode':
        card_predictor.intelligent_mode_active = False
        new_text = "❌ **Mode Intelligent DÉSACTIVÉ.** Les prédictions restent en mode Veille."
    else:
        new_text = "Action non reconnue."
        
    bot.edit_message_text(chat_id, message_id, new_text)

# --- Logique de Traitement Principal des Mises à Jour ---

def process_update(bot, update: Dict):
    """Processes a single Telegram Update (Message or Callback)."""
    
    target_channel_id = config.TARGET_CHANNEL_ID
    prediction_channel_id = config.PREDICTION_CHANNEL_ID
    admin_chat_id = config.ADMIN_CHAT_ID

    if 'message' in update or 'edited_message' in update:
        
        message_data = update.get('message') or update.get('edited_message')
        if not message_data: return
        
        text = message_data.get('text', '')
        chat_id = str(message_data['chat']['id'])
        message_id = message_data['message_id']
        
        # 1. Traitement des messages du canal source
        if chat_id == target_channel_id:
            
            verification_result = card_predictor.verify_prediction(text, message_id)
            
            if verification_result:
                
                if verification_result['type'] == 'fail_threshold_reached':
                    if admin_chat_id:
                        handle_inter_command(bot, admin_chat_id)
                    return
                    
                elif verification_result['type'] == 'edit_message':
                    edit_result = verification_result
                    bot.send_message(
                        prediction_channel_id,
                        f"✅ **VÉRIFICATION TERMINÉE** pour N{edit_result['predicted_game']} (via message source):\n{edit_result['new_message']}"
                    )
            
            # Prédiction Automatique 
            should_predict, game_number, predicted_value = card_predictor.should_predict(text)
            if should_predict:
                prediction_data = card_predictor.make_prediction(game_number, predicted_value)
                bot.send_message(prediction_channel_id, prediction_data['text'])
        
        # 2. Traitement des commandes utilisateur (hors canaux source/prédiction)
        elif text.startswith('/') and chat_id != prediction_channel_id:
            if text.startswith('/start'):
                handle_start_command(bot, chat_id)
            elif text.startswith('/help'):
                handle_help_command(bot, chat_id)
            elif text.startswith('/status'):
                handle_status_command(bot, chat_id)
            elif text.startswith('/inter'):
                handle_inter_command(bot, chat_id)
            elif text.startswith('/defaut'):
                handle_defaut_command(bot, chat_id)


    # Traitement des clics de boutons inline
    elif 'callback_query' in update:
        callback_query = update['callback_query']
        callback_query_id = callback_query['id']
        data = callback_query['data']
        chat_id = str(callback_query['message']['chat']['id'])
        message_id = callback_query['message']['message_id']
        
        handle_callback_query(bot, callback_query_id, chat_id, message_id, data)
  
