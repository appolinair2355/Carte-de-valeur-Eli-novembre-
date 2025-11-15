"""
Contient les gestionnaires de commandes et la logique de traitement des mises à jour.
"""

import os
import re
import logging
from typing import Dict, Optional
from card_predictor import card_predictor # Import du prédicteur pour la logique
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
        "🤖 COMMANDES :\\n"
        "/status - Affiche l'état du Mode Intelligent et les échecs.\\n"
        "/inter - Analyse les déclencheurs de Dame et permet l'activation interactive de la stratégie.\\n"
        "/defaut - Désactive le Mode Intelligent et réinitialise les règles.\\n"
        "/deploy - Génère un package ZIP pour déploiement sur Render.com.\\n"
    )
    bot.send_message(chat_id, help_text)

def handle_status_command(bot, chat_id):
    logger.info(f"📊 Commande /status reçue de chat_id: {chat_id}")

    mode_status = "🟢 ACTIF (Règles appliquées)" if card_predictor.intelligent_mode_active else "🔴 INACTIF (Veille)"
    failure_count = card_predictor.consecutive_failures

    status_message = (
        f"**🤖 Statut du Bot DAME**\\n\\n"
        f"**Mode Intelligent :** {mode_status}\\n"
        f"**Échecs Consécutifs :** {failure_count} / {card_predictor.MAX_FAILURES_BEFORE_INTELLIGENT_MODE}\\n"
        f"**Historique Tirages :** {len(card_predictor.draw_history)} derniers jeux enregistrés\\n"
        f"**Prédictions en Attente :** {len(card_predictor.pending_messages)} messages (⏰)\\n\\n"
        f"Utilisez /inter pour interagir avec la stratégie."
    )
    bot.send_message(chat_id, status_message, parse_mode="Markdown")

def handle_inter_command(bot, chat_id):
    logger.info(f"🧠 Commande /inter reçue de chat_id: {chat_id}")
    
    if len(card_predictor.draw_history) < 3:
        bot.send_message(chat_id, "⚠️ Historique insuffisant (minimum 3 tirages). Attendez plus de résultats.")
        return

    # Logique pour le mode interactif
    message = (
        "**INTERACTION STRATÉGIE**\\n\\n"
        f"Le bot a trouvé {len(card_predictor.draw_history)} tirages avec des Dames.\\n"
        f"Mode Intelligent est actuellement {'ACTIF' if card_predictor.intelligent_mode_active else 'INACTIF'}.\\n\\n"
        "Voulez-vous activer ou désactiver manuellement le Mode Intelligent ?"
    )
    
    keyboard = [
        [
            {'text': '🟢 Activer Mode Intelligent', 'callback_data': 'SET_MODE_ON'},
        ],
        [
            {'text': '🔴 Désactiver Mode Intelligent', 'callback_data': 'SET_MODE_OFF'},
        ]
    ]
    
    bot.send_message(chat_id, message, reply_markup={'inline_keyboard': keyboard}, parse_mode="Markdown")

def handle_defaut_command(bot, chat_id):
    logger.info(f"❌ Commande /defaut reçue de chat_id: {chat_id}. Désactivation du mode intelligent.")
    card_predictor.intelligent_mode_active = False
    card_predictor.consecutive_failures = 0
    bot.send_message(chat_id, "🔴 Mode Intelligent désactivé et compteur d'échecs réinitialisé.")

def handle_deploy_command(bot, chat_id):
    logger.info(f"📦 Commande /deploy reçue de chat_id: {chat_id}. Préparation du fichier ZIP.")
    # Logique de création de ZIP (non incluse ici, mais elle génère le fichier)
    zip_path = "deploy_package.zip" 
    
    # Simuler la création du ZIP pour l'exemple
    with open(zip_path, 'w') as f:
        f.write("Fichier de déploiement simulé.")
    
    success = bot.send_document(chat_id, zip_path)
    if success:
        logger.info("✅ Fichier de déploiement ZIP envoyé avec succès.")
    
    # Nettoyage
    os.remove(zip_path)

# --- Gestionnaire de Callbacks (Boutons) ---

def handle_callback_query(bot, callback_query_id, chat_id, message_id, data):
    logger.info(f"⚙️ Callback reçu de chat_id: {chat_id}, Data: {data}")
    
    admin_chat_id = str(config.ADMIN_CHAT_ID)
    if str(chat_id) != admin_chat_id:
        bot.answer_callback_query(callback_query_id, "Seul l'administrateur peut effectuer cette action.")
        return

    if data == 'SET_MODE_ON':
        card_predictor.intelligent_mode_active = True
        card_predictor.consecutive_failures = 0
        message = "🟢 Mode Intelligent **ACTIVÉ** manuellement. Compteur d'échecs réinitialisé."
        logger.info("🟢 Mode intelligent activé par l'administrateur.")
    elif data == 'SET_MODE_OFF':
        card_predictor.intelligent_mode_active = False
        card_predictor.consecutive_failures = 0
        message = "🔴 Mode Intelligent **DÉSACTIVÉ** manuellement. Compteur d'échecs réinitialisé."
        logger.info("🔴 Mode intelligent désactivé par l'administrateur.")
    else:
        message = "Action inconnue."
        
    bot.edit_message_text(chat_id, message_id, message, parse_mode="Markdown")
    bot.answer_callback_query(callback_query_id, "Action effectuée.")

# --- Fonction principale de gestion des mises à jour ---

def handle_update(bot, update: Dict):
    admin_chat_id = str(config.ADMIN_CHAT_ID)
    
    # =====================================================================
    # NOUVEAU LOG D'ANALYSE : TRAITEMENT DES MESSAGES DE CANAL (channel_post)
    # =====================================================================
    
    if 'channel_post' in update:
        channel_post = update['channel_post']
        chat_id = str(channel_post['chat']['id'])
        text = channel_post.get('text', '[Message sans texte]')
        
        # Log de vérification critique : Si vous voyez cette ligne, le bot reçoit les messages du canal !
        logger.info(f"✅ RECU MESSAGE DE CANAL SOURCE. ID: {chat_id}, Texte: {text[:80]}...")
        
        # Vérifiez que le message provient du TARGET_CHANNEL_ID configuré
        if chat_id == config.TARGET_CHANNEL_ID:
            logger.info("🎯 Message confirmé comme provenant du canal source cible.")
            
            # 1. Traiter le message du canal source
            analysis_result = card_predictor.process_new_draw(text)
            
            if analysis_result:
                # Si un résultat est retourné (ex: prédiction, message en attente)
                result_type = analysis_result.get('type')
                predicted_game = analysis_result.get('predicted_game')
                
                if result_type == 'new_prediction':
                    message_id = bot.send_message(config.PREDICTION_CHANNEL_ID, analysis_result['message'], parse_mode="Markdown")
                    if message_id:
                        logger.info(f"📤 Nouvelle prédiction envoyée au jeu {predicted_game}. Message ID: {message_id}")
                        # Stocker le message ID pour la vérification future
                        card_predictor.predictions[predicted_game]['prediction_message_id'] = message_id
                
                elif result_type == 'update_pending_message':
                    # Mise à jour des messages en attente (logique de Dame)
                    bot.edit_message_text(
                        chat_id=config.PREDICTION_CHANNEL_ID, 
                        message_id=analysis_result['message_id'], 
                        text=analysis_result['new_message'],
                        parse_mode="Markdown"
                    )
                    logger.info(f"🔄 Message en attente édité pour le jeu {predicted_game}.")
            
            else:
                logger.info("⏩ Message du canal source ignoré (ne contient pas de tirage valide ou ne nécessite pas d'action).")
        
        # 2. Vérification des prédictions précédentes (si le message est un résultat de jeu)
        verification_result = card_predictor.verify_predictions(text)
        
        if verification_result:
            result_type = verification_result.get('type')
            predicted_game = verification_result.get('predicted_game')
            
            if result_type == 'edit_message':
                bot.edit_message_text(
                    chat_id=config.PREDICTION_CHANNEL_ID, 
                    message_id=verification_result['prediction_message_id'], 
                    text=verification_result['new_message'],
                    parse_mode="Markdown"
                )
                logger.info(f"✅/❌ Prédiction vérifiée et message édité pour le jeu {predicted_game}.")
            
            elif result_type == 'fail_threshold_reached':
                # Alerter l'admin que le mode intelligent devrait être activé
                logger.warning("🚨 Seuil d'échecs atteint. Envoi d'une alerte /inter à l'admin.")
                handle_inter_command(bot, admin_chat_id)
                
        return # Terminer le traitement après le post de canal

    # =====================================================================
    # FIN DE LA LOGIQUE CHANNEL_POST
    # =====================================================================

    
    # Traitement des messages de chat standard (Commandes)
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        chat_type = message['chat']['type']
        text = message.get('text', '')

        if text.startswith('/'):
            logger.info(f"💬 Commande détectée : {text[:50]} depuis chat_type: {chat_type}, chat_id: {chat_id}")

            # Traiter les commandes seulement si c'est un message privé ou d'un admin
            if chat_type == 'private' or str(chat_id) == admin_chat_id:
                logger.info(f"✅ Traitement de la commande autorisé (private ou admin)")
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
            else:
                logger.info(f"⏩ Commande ignorée (pas un message privé ni admin)")


    # Traitement des clics de boutons inline
    elif 'callback_query' in update:
        callback_query = update['callback_query']
        callback_query_id = callback_query['id']
        data = callback_query['data']
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']

        handle_callback_query(bot, callback_query_id, chat_id, message_id, data)
    
    # Log de tout autre type de mise à jour reçue mais non traitée
    else:
        update_type = list(update.keys())[0] if update else "INCONNU"
        logger.info(f"ℹ️ Mise à jour reçue mais ignorée : {update_type}")

