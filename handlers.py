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
    bot.send_message(chat_id, "Bot DAME PRÉDICTION démarré. Utilisez /status ou /help.")

def handle_help_command(bot, chat_id):
    help_text = (
        "🤖 COMMANDES :\n"
        "/status - Affiche l'état du Mode Intelligent et les échecs.\n"
        "/inter - Analyse les déclencheurs de Dame et permet l'activation interactive de la stratégie.\n"
        "/defaut - Désactive le Mode Intelligent et réinitialise les règles.\n"
        "/deploy - Génère un package ZIP pour déploiement sur Render.com.\n"
    )
    bot.send_message(chat_id, help_text)

def handle_status_command(bot, chat_id):
    mode_status = "🟢 ACTIF (Règles appliquées)" if card_predictor.intelligent_mode_active else "🔴 INACTIF (Veille)"
    failure_count = card_predictor.consecutive_failures

    status_text = (
        "📊 Statut du Predictor (Webhook) :\n"
        f"Mode Intelligent : {mode_status}\n"
        f"Échecs consécutifs : {failure_count}/{card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE}\n"
        f"Dernière prédiction Dame (Q): {card_predictor.last_dame_prediction if card_predictor.last_dame_prediction else 'Aucune'}\n"
    )
    bot.send_message(chat_id, status_text)

def handle_defaut_command(bot, chat_id):
    card_predictor.intelligent_mode_active = False
    card_predictor.consecutive_failures = 0
    bot.send_message(chat_id, "✅ Mode Intelligent DÉSACTIVÉ. Les prédictions automatiques sont maintenant basées sur la règle initiale (Veille).")

def handle_deploy_command(bot, chat_id):
    """Génère le package de déploiement et l'envoie."""
    import subprocess
    import glob
    import requests

    bot.send_message(chat_id, "📦 Génération du package de déploiement en cours...")

    try:
        result = subprocess.run(
            ['python3', 'scripts/deploy.py'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )

        if result.returncode == 0:
            zip_files = glob.glob('dam200.zip')
            if not zip_files:
                zip_files = glob.glob('bot_telegram_render_*.zip')
            
            if zip_files:
                latest_zip = max(zip_files, key=os.path.getctime)
                
                if not os.path.exists(latest_zip):
                    bot.send_message(chat_id, f"❌ Fichier {latest_zip} introuvable.")
                    return
                
                file_size = os.path.getsize(latest_zip) / 1024

                message = (
                    f"✅ Package créé avec succès !\n\n"
                    f"📦 Fichier : {latest_zip}\n"
                    f"📊 Taille : {file_size:.2f} KB\n\n"
                    f"🚀 Instructions :\n"
                    f"1. Déployez sur Render.com\n"
                    f"2. Configurez les variables d'environnement\n"
                    f"3. Port 10000 configuré automatiquement\n"
                    f"4. Appelez /set_webhook après déploiement"
                )
                
                bot.send_message(chat_id, message)
                
                success = bot.send_document(chat_id, latest_zip)
                if success:
                    bot.send_message(chat_id, f"✅ Fichier {latest_zip} envoyé avec succès !")
                else:
                    bot.send_message(chat_id, f"⚠️ Erreur lors de l'envoi. Téléchargez {latest_zip} manuellement.")
            else:
                bot.send_message(chat_id, "❌ Aucun fichier ZIP trouvé après génération.")
        else:
            error_msg = result.stderr if result.stderr else "Erreur inconnue"
            bot.send_message(chat_id, f"❌ Erreur lors de la génération :\n{error_msg}")

    except subprocess.TimeoutExpired:
        bot.send_message(chat_id, "⏱️ Timeout : La génération a pris trop de temps.")
    except Exception as e:
        logger.error(f"❌ Erreur dans handle_deploy_command: {e}")
        import traceback
        logger.error(traceback.format_exc())
        bot.send_message(chat_id, f"❌ Erreur : {str(e)}")

def handle_inter_command(bot, chat_id):
    """Analyse l'historique et détecte les cycles de Dame (Q) selon N-2 → N."""

    history = card_predictor.draw_history
    if not history or len(history) < 3:
        bot.send_message(chat_id, "⚠️ Historique insuffisant (minimum 3 tirages). Attendez plus de résultats.")
        return

    sorted_game_numbers = sorted(history.keys())

    # Afficher l'historique complet
    history_summary = f"📊 **HISTORIQUE COMPLET** : {len(history)} tirages enregistrés\n\n"
    for game_num in sorted_game_numbers[-10:]:
        draw = history[game_num]
        first_two = draw.get('first_two_cards', 'N/A')
        first_group = draw.get('first_group', 'N/A')
        has_q = '👸' if re.search(r'Q[♥️♠️♦️♣️❤️]', first_group) else ''
        history_summary += f"**N{game_num}** : {first_two} | ({first_group}) {has_q}\n"

    bot.send_message(chat_id, history_summary)

    # Analyser les cycles Dame : N-2 → N
    cycle_list = []
    cycle_num = 1

    for game_number in sorted_game_numbers:
        current_draw = history[game_number]
        first_group_text = current_draw.get('first_group', '')

        # Chercher Q (Dame) dans le premier groupe
        dame_match = re.search(r'Q[♥️♠️♦️♣️❤️]', first_group_text)
        if dame_match:
            dame_card = dame_match.group(0)

            # Chercher le déclencheur N-2
            trigger_number = game_number - 2
            trigger_draw = history.get(trigger_number)

            if trigger_draw:
                # Vérifier que N-2 ne contient PAS de Dame
                trigger_first_group = trigger_draw.get('first_group', '')
                if not re.search(r'Q[♥️♠️♦️♣️❤️]', trigger_first_group):
                    trigger_cards = trigger_draw.get('first_two_cards', 'N/A')

                    cycle_list.append(
                        f"**Cycle N°{cycle_num}**\n"
                        f"**Déclencheur** : `{trigger_cards}` (vu au jeu #N{trigger_number})\n"
                        f"**Carte** : `{dame_card}` (La Dame spécifique trouvée au 1er groupe)\n"
                        f"**Au numéro** : `#N{game_number}`"
                    )
                    cycle_num += 1

    if cycle_list:
        cycles_output = "\n\n".join(cycle_list[-5:])
        alert_title = "**🚨 MODE INTELLIGENT REQUIS**" if card_predictor.consecutive_failures >= card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE else "**🔍 ANALYSE DES CYCLES DAME**"

        message_text = (
            f"{alert_title}\n\n"
            "**🔍 CYCLE DE LA DAME : (N-2) → (N)**\n"
            f"{len(cycle_list)} cycle(s) détecté(s) :\n\n"
            f"{cycles_output}\n\n"
            "---"
        )
    else:
        message_text = (
            "⚠️ **AUCUN CYCLE VALIDE DÉTECTÉ**\n\n"
            f"Historique : {len(history)} tirages enregistrés\n"
            "Aucun cycle (N-2) → (N) avec Dame n'a été trouvé.\n\n"
            "Continuez à observer les tirages."
        )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ OUI (Activer Mode Intelligent)", "callback_data": "activate_intelligent_mode"},
                {"text": "❌ NON (Rester en Règle par Défaut)", "callback_data": "deactivate_intelligent_mode"}
            ]
        ]
    }

    bot.send_message(
        chat_id, 
        f"{message_text}\n\n**Voulez-vous activer le Mode Intelligent (Stratégie K/J/A/JJ) ?**", 
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

    if 'message' in update or 'edited_message' in update or 'channel_post' in update or 'edited_channel_post' in update:

        message_data = update.get('message') or update.get('edited_message') or update.get('channel_post') or update.get('edited_channel_post')
        if not message_data: return

        text = message_data.get('text', '')
        chat_id = str(message_data['chat']['id'])
        message_id = message_data['message_id']

        # 1. Traitement des messages du canal source
        if chat_id == target_channel_id:

            # Construire l'historique pour tous les messages (pas seulement les complétés)
            game_number = card_predictor.extract_game_number(text)
            if game_number:
                first_group = card_predictor.extract_first_group_content(text)
                first_two_cards = card_predictor.extract_first_two_cards_with_value(text)

                if first_group:
                    card_predictor.draw_history[game_number] = {
                        'text': text,
                        'first_group': first_group,
                        'message_id': message_id,
                        'first_two_cards': first_two_cards
                    }

                    # Limiter l'historique
                    if len(card_predictor.draw_history) > card_predictor.history_limit:
                        oldest_key = min(card_predictor.draw_history.keys())
                        del card_predictor.draw_history[oldest_key]

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
            if should_predict and game_number is not None and predicted_value is not None:
                prediction_data = card_predictor.make_prediction(game_number, predicted_value)
                bot.send_message(prediction_channel_id, prediction_data['text'])

        # 2. Traitement des commandes utilisateur (hors canaux source/ prédiction)
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
            elif text.startswith('/deploy'):
                handle_deploy_command(bot, chat_id)


    # Traitement des clics de boutons inline
    elif 'callback_query' in update:
        callback_query = update['callback_query']
        callback_query_id = callback_query['id']
        data = callback_query['data']
        chat_id = str(callback_query['message']['chat']['id'])
        message_id = callback_query['message']['message_id']

        handle_callback_query(bot, callback_query_id, chat_id, message_id, data)