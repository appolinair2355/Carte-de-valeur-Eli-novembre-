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

# --- Gestionnaires de Commandes (Aucun changement ici) ---
# ... (le code des handlers de commandes est inchangé)

# --- Gestionnaire de Callbacks (Boutons) (Aucun changement ici) ---
# ... (le code de handle_callback_query est inchangé)

# --- Fonction principale de gestion des mises à jour ---

def handle_update(bot, update: Dict):
    admin_chat_id = str(config.ADMIN_CHAT_ID)
    
    # =====================================================================
    # LOGIQUE DE TRAITEMENT DES MESSAGES DE CANAL
    # =====================================================================
    
    # ⚠️ DÉTECTION DU MESSAGE DE CANAL (POST ou EDITÉ)
    if 'channel_post' in update:
        channel_post = update['channel_post']
        logger.info("🎯 Mise à jour détectée : Nouveau message de canal (channel_post).")
        
    elif 'edited_channel_post' in update: # <-- AJOUT CRITIQUE
        channel_post = update['edited_channel_post']
        logger.info("🎯 Mise à jour détectée : Message de canal ÉDITÉ (edited_channel_post).")
        
    else:
        # Poursuivre le traitement avec les commandes ou autres mises à jour
        channel_post = None 
        
    if channel_post:
        # Logique de traitement du canal, commune aux POST et EDITÉS
        chat_id = str(channel_post['chat']['id'])
        text = channel_post.get('text', '[Message sans texte]')
        
        # Log de vérification critique : Si vous voyez cette ligne, le bot reçoit les messages du canal !
        logger.info(f"✅ RECU MESSAGE DE CANAL SOURCE. ID: {chat_id}, Texte: {text[:80]}...")
        
        # Le reste de la logique de traitement du canal (inchangée)
        if chat_id == config.TARGET_CHANNEL_ID:
            logger.info("🎯 Message confirmé comme provenant du canal source cible.")
            
            # 1. Traiter le message du canal source
            analysis_result = card_predictor.process_new_draw(text)
            
            if analysis_result:
                result_type = analysis_result.get('type')
                predicted_game = analysis_result.get('predicted_game')
                
                if result_type == 'new_prediction':
                    message_id = bot.send_message(config.PREDICTION_CHANNEL_ID, analysis_result['message'], parse_mode="Markdown")
                    if message_id:
                        logger.info(f"📤 Nouvelle prédiction envoyée au jeu {predicted_game}. Message ID: {message_id}")
                        card_predictor.predictions[predicted_game]['prediction_message_id'] = message_id
                
                elif result_type == 'update_pending_message':
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
                logger.warning("🚨 Seuil d'échecs atteint. Envoi d'une alerte /inter à l'admin.")
                handle_inter_command(bot, admin_chat_id)
                
        return # Terminer le traitement après le post/edit de canal

    # =====================================================================
    # FIN DE LA LOGIQUE CHANNEL_POST
    # =====================================================================

    
    # Traitement des messages de chat standard (Commandes)
    if 'message' in update:
        # ... (le reste de la logique de commande est inchangé)
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
            
