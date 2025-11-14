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
    logger.info(f"▶️ Commande /start reçue de chat_id: {chat_id}")
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
    logger.info(f"📊 Commande /status reçue de chat_id: {chat_id}")

    mode_status = "🟢 ACTIF (Règles appliquées)" if card_predictor.intelligent_mode_active else "🔴 INACTIF (Veille)"
    failure_count = card_predictor.consecutive_failures

    status_text = (
        "📊 Statut du Predictor (Webhook) :\n"
        f"Mode Intelligent : {mode_status}\n"
        f"Échecs consécutifs : {failure_count}/{card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE}\n"
        f"Dernière prédiction Dame (Q): {card_predictor.last_dame_prediction if card_predictor.last_dame_prediction else 'Aucune'}\n"
    )

    logger.info(f"   Mode intelligent: {'ACTIF' if card_predictor.intelligent_mode_active else 'INACTIF'}")
    logger.info(f"   Échecs: {failure_count}/{card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE}")

    bot.send_message(chat_id, status_text)

def handle_defaut_command(bot, chat_id):
    logger.info(f"⏹️ Commande /defaut reçue de chat_id: {chat_id}")

    card_predictor.intelligent_mode_active = False
    card_predictor.consecutive_failures = 0

    logger.info(f"   Mode Intelligent DÉSACTIVÉ, échecs réinitialisés à 0")

    bot.send_message(chat_id, "✅ Mode Intelligent DÉSACTIVÉ. Les prédictions automatiques sont maintenant basées sur la règle initiale (Veille).")

def handle_deploy_command(bot, chat_id):
    """Génère le package de déploiement et l'envoie."""
    import subprocess
    import glob
    import requests

    logger.info(f"📦 Commande /deploy reçue de chat_id: {chat_id}")

    bot.send_message(chat_id, "📦 Génération du package de déploiement en cours...")

    try:
        # Tentative de génération du package spécifique 'fin9.zip'
        # En supposant que 'scripts/deploy.py' peut être configuré pour créer 'fin9.zip'
        # Si 'scripts/deploy.py' ne supporte pas cela, cette partie pourrait nécessiter une adaptation
        # ou une nouvelle logique pour créer spécifiquement 'fin9.zip'.
        # Pour l'instant, on suppose que le script est capable de générer le bon fichier.
        result = subprocess.run(
            ['python3', 'scripts/deploy.py', 'fin9'], # Passer 'fin9' comme argument si le script le supporte
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )

        if result.returncode == 0:
            # Chercher spécifiquement fin9.zip
            zip_files = glob.glob('fin9.zip')
            if not zip_files:
                # Fallback sur d'autres versions fin*.zip si fin9.zip n'est pas trouvé
                zip_files = glob.glob('fin*.zip')
            if not zip_files:
                zip_files = glob.glob('bot_telegram_render_*.zip')

            if zip_files:
                latest_zip = max(zip_files, key=os.path.getctime)
                zip_filename = os.path.basename(latest_zip) # Utiliser le nom du fichier trouvé

                if not os.path.exists(latest_zip):
                    bot.send_message(chat_id, f"❌ Fichier {latest_zip} introuvable.")
                    return

                file_size = os.path.getsize(latest_zip) / 1024

                bot.send_message(
                    chat_id,
                    "✅ Package fin9.zip créé avec succès !\n\n"
                    f"📦 Fichier : {zip_filename}\n"
                    f"📊 Taille : {file_size:.2f} KB\n\n"
                    "✨ NOUVEAUTÉS VERSION fin9:\n"
                    "🧠 Mode Intelligent avec 3 Déclencheurs Fréquents:\n"
                    "   1️⃣ Double Valet (JJ) → N+2\n"
                    "   2️⃣ Valet seul (J) → N+2\n"
                    "   3️⃣ Roi + Valet (KJ) → N+2\n\n"
                    "🚀 Instructions de déploiement sur REPLIT:\n"
                    "1. Uploadez fin9.zip dans votre Repl\n"
                    "2. Extrayez les fichiers\n"
                    "3. Configurez 2 Secrets (variables d'environnement):\n"
                    "   - BOT_TOKEN\n"
                    "   - ADMIN_CHAT_ID\n"
                    "4. Cliquez sur Run\n"
                    "5. Port 10000 configuré automatiquement\n"
                    "6. IDs de canaux pré-configurés ✅"
                )

                success = bot.send_document(chat_id, latest_zip)
                if success:
                    bot.send_message(chat_id, f"✅ Fichier {latest_zip} envoyé avec succès !")
                else:
                    bot.send_message(chat_id, f"⚠️ Erreur lors de l'envoi. Téléchargez {latest_zip} manuellement.")
            else:
                bot.send_message(chat_id, "❌ Aucun fichier ZIP trouvé après génération.")
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            bot.send_message(chat_id, f"❌ Erreur lors de la génération :\n{error_msg[:500]}")
    except subprocess.TimeoutExpired:
        bot.send_message(chat_id, "❌ La génération a pris trop de temps (timeout).")
    except Exception as e:
        logger.error(f"❌ Erreur lors de /deploy : {e}")
        bot.send_message(chat_id, f"❌ Erreur inattendue : {str(e)}")

def handle_inter_command(bot, chat_id):
    """Analyse l'historique et détecte les cycles de Dame (Q) selon N-2 → N."""
    logger.info(f"🔍 Commande /inter reçue de chat_id: {chat_id}")

    history = card_predictor.draw_history
    logger.info(f"   Historique disponible: {len(history)} tirages")
    if not history or len(history) < 3:
        bot.send_message(chat_id, "⚠️ Historique insuffisant (minimum 3 tirages). Attendez plus de résultats.")
        return

    sorted_game_numbers = sorted(history.keys())

    # Analyser les cycles Dame : N-2 → N avec format simplifié
    cycle_list = []

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

                    # Format simplifié : numéro :879 \n Déclencheur 8♠️8❤️ \n Carte: Q❤️
                    cycle_list.append(
                        f"numéro :{game_number}\nDéclencheur {trigger_cards}\nCarte: {dame_card}"
                    )

    if cycle_list:
        cycles_output = "\n\n".join(cycle_list[-10:])
        alert_title = "🚨 MODE INTELLIGENT REQUIS" if card_predictor.consecutive_failures >= card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE else "🔍 ANALYSE DES CYCLES DAME"

        message_text = (
            f"{alert_title}\n\n"
            "📊 HISTORIQUE COMPLET:\n"
            f"{len(cycle_list)} cycle(s) détecté(s) (N-2 → N):\n\n"
            f"{cycles_output}\n\n"
            "---"
        )
    else:
        message_text = (
            "⚠️ AUCUN CYCLE VALIDE DÉTECTÉ\n\n"
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
        f"{message_text}\n\nVoulez-vous activer le Mode Intelligent (Stratégie K/J/A/JJ) ?",
        reply_markup=reply_markup
    )


def handle_callback_query(bot, callback_query_id: str, chat_id: int, message_id: int, data: str):
    """Gère les réponses aux boutons 'Oui/Non'."""
    bot.answer_callback_query(callback_query_id)

    if data == 'activate_intelligent_mode':
        # Mise à jour du mode intelligent avec 3 déclencheurs fréquents
        card_predictor.intelligent_mode_active = True
        card_predictor.consecutive_failures = 0
        # Les déclencheurs spécifiques (JJ, J, KJ) sont gérés dans la logique de prédiction elle-même
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
        chat_id = message_data['chat']['id']
        message_id = message_data['message_id']

        # 🔍 LOG DE DIAGNOSTIC - Afficher TOUS les messages reçus
        logger.info(f"🔍 DIAGNOSTIC - Message reçu:")
        logger.info(f"   Chat ID reçu: {chat_id} (type: {type(chat_id)})")
        logger.info(f"   TARGET_CHANNEL_ID configuré: {target_channel_id} (type: {type(target_channel_id)})")

        # Convertir TARGET_CHANNEL_ID en int pour comparaison fiable
        try:
            target_id_int = int(target_channel_id) if target_channel_id else None
        except (ValueError, TypeError):
            target_id_int = None
            logger.error(f"❌ TARGET_CHANNEL_ID invalide: {target_channel_id}")

        logger.info(f"   Comparaison chat_id == target_id_int: {chat_id == target_id_int}")
        logger.info(f"   Texte du message (100 premiers caractères): {text[:100]}")

        # --- Messages provenant du CANAL SOURCE ---
        # Normaliser les deux IDs en entiers pour une comparaison fiable
        if target_id_int and chat_id == target_id_int:
            logger.info(f"📡 Message reçu du CANAL SOURCE (ID: {target_channel_id})")
            logger.info(f"📝 Contenu: {text[:100]}...")

            # Extraire le numéro de jeu
            game_number = card_predictor.extract_game_number(text)

            # Vérifier si le message est en attente (⏰)
            if card_predictor.is_pending_message(text):
                if game_number:
                    # Mémoriser le message en attente
                    card_predictor.pending_messages[game_number] = {
                        'text': text,
                        'message_id': message_id
                    }
                    logger.info(f"⏰ Message en attente mémorisé pour N{game_number} - En attente de finalisation (✅ ou 🔰)")
                return

            # Vérifier si ce message était en attente et vient d'être finalisé
            if game_number and game_number in card_predictor.pending_messages:
                logger.info(f"✅ Message N{game_number} finalisé (était en attente ⏰)")
                # Supprimer de la liste d'attente
                del card_predictor.pending_messages[game_number]

            # Construire l'historique pour les messages finalisés
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
                    logger.info(f"📝 Historique mis à jour : N{game_number} ajouté ({len(card_predictor.draw_history)} tirages)")

                    # Limiter l'historique
                    if len(card_predictor.draw_history) > card_predictor.history_limit:
                        oldest_key = min(card_predictor.draw_history.keys())
                        del card_predictor.draw_history[oldest_key]

            verification_result = card_predictor.verify_prediction(text, message_id)

            if verification_result:
                logger.info(f"🔍 VÉRIFICATION de prédiction en cours...")

                if verification_result['type'] == 'fail_threshold_reached':
                    logger.warning(f"⚠️ SEUIL D'ÉCHECS ATTEINT ({card_predictor.consecutive_failures} échecs)")
                    logger.info(f"📨 Envoi de /inter automatique à l'admin (ID: {admin_chat_id})")
                    if admin_chat_id:
                        handle_inter_command(bot, admin_chat_id)
                    return

                elif verification_result['type'] == 'edit_message':
                    edit_result = verification_result
                    predicted_game_number = edit_result['predicted_game']
                    logger.info(f"✅ Prédiction vérifiée pour N{predicted_game_number}")
                    logger.info(f"   Statut: {edit_result['new_message']}")

                    # Récupérer l'ID du message de prédiction depuis le dictionnaire des prédictions
                    prediction_obj = card_predictor.predictions.get(predicted_game_number)
                    if prediction_obj:
                        original_msg_id = prediction_obj.get('prediction_message_id')
                        if original_msg_id:
                            logger.info(f"🔄 Mise à jour du message de prédiction (message_id: {original_msg_id})")
                            bot.edit_message_text(
                                prediction_channel_id,
                                original_msg_id,
                                edit_result['new_message']
                            )
                            logger.info(f"✅ Message de prédiction mis à jour avec succès")
                        else:
                            logger.warning(f"⚠️ prediction_message_id non trouvé pour N{predicted_game_number}")
                            # Fallback : envoyer un nouveau message
                            bot.send_message(
                                prediction_channel_id,
                                f"✅ **VÉRIFICATION** N{predicted_game_number}:\n{edit_result['new_message']}"
                            )
                    else:
                        logger.warning(f"⚠️ Prédiction N{predicted_game_number} non trouvée dans le dictionnaire")

            # Prédiction Automatique (même sur les messages en attente ⏰)
            should_predict, game_number, predicted_value = card_predictor.should_predict(text)
            if should_predict and game_number is not None and predicted_value is not None:
                mode = "INTELLIGENT" if card_predictor.intelligent_mode_active else "PAR DÉFAUT"
                logger.info(f"🎯 PRÉDICTION AUTOMATIQUE activée (Mode: {mode})")
                logger.info(f"   Jeu source: N{game_number}")
                logger.info(f"   Règle: {predicted_value}")

                prediction_data = card_predictor.make_prediction(game_number, predicted_value)
                logger.info(f"📤 Envoi de la prédiction au CANAL DE PRÉDICTION (ID: {prediction_channel_id})")
                logger.info(f"   Message: {prediction_data['text']}")

                result = bot.send_message(prediction_channel_id, prediction_data['text'])
                if result:
                    logger.info(f"✅ Prédiction envoyée avec succès (message_id: {result})")
                    # Stocker l'ID du message pour mise à jour ultérieure
                    target_game = prediction_data['target_game']
                    if target_game in card_predictor.predictions:
                        card_predictor.predictions[target_game]['prediction_message_id'] = result
                else:
                    logger.error(f"❌ Échec de l'envoi de la prédiction")

        # 2. Traitement des commandes utilisateur (hors canaux source/ prédiction)
        elif text.startswith('/') and str(chat_id) != prediction_channel_id:
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
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']

        handle_callback_query(bot, callback_query_id, chat_id, message_id, data)