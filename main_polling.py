"""
Point d'entrée principal en mode POLLING
Le bot interroge continuellement Telegram pour obtenir les nouvelles mises à jour.
Un serveur HTTP minimal tourne sur le port configuré pour satisfaire Render.com.
"""

import logging
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import Config
from bot import TelegramBot
from handlers import process_update

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Gestionnaire HTTP minimal pour le health check de Render.com"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot Telegram en mode POLLING - OK')
    
    def log_message(self, format, *args):
        # Désactiver les logs HTTP pour ne pas polluer la console
        pass

def start_health_server(port):
    """Démarre un serveur HTTP minimal sur le port spécifié"""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"🌐 Serveur HTTP de health check démarré sur le port {port}")
    server.serve_forever()

# --- Initialisation ---
config = Config()

if not config.BOT_TOKEN:
    logger.critical("❌ FATAL - BOT_TOKEN n'est pas configuré. Le bot ne peut pas démarrer.")
    exit(1)

# Créer l'instance du bot
bot = TelegramBot(config.BOT_TOKEN)

def run_polling():
    """Lance le bot en mode polling (long polling)."""
    logger.info("=" * 60)
    logger.info("🚀 DÉMARRAGE DU BOT EN MODE POLLING")
    logger.info("=" * 60)
    logger.info(f"🌐 Port HTTP: {config.PORT}")
    logger.info(f"📡 Canal Source (TARGET_CHANNEL_ID): {config.TARGET_CHANNEL_ID}")
    logger.info(f"📤 Canal Prédiction (PREDICTION_CHANNEL_ID): {config.PREDICTION_CHANNEL_ID}")
    logger.info(f"👤 Admin (ADMIN_CHAT_ID): {config.ADMIN_CHAT_ID}")
    logger.info("=" * 60)
    
    # Supprimer le webhook pour activer le polling
    logger.info("🔄 Suppression du webhook (si configuré)...")
    bot.delete_webhook()
    time.sleep(2)
    
    logger.info("✅ Mode Polling activé - Le bot écoute maintenant les messages...")
    logger.info("💡 Surveillance active du canal source en cours...")
    logger.info("=" * 60)
    
    offset = None
    error_count = 0
    max_errors = 5
    
    while True:
        try:
            # Récupérer les mises à jour (long polling avec timeout de 30s)
            updates = bot.get_updates(offset=offset, timeout=30)
            
            if updates:
                logger.info(f"📥 {len(updates)} nouvelle(s) mise(s) à jour reçue(s)")
                
                for update in updates:
                    update_id = update.get('update_id')
                    
                    if update_id is None:
                        continue
                    
                    # Traiter la mise à jour
                    try:
                        process_update(bot, update)
                        logger.info(f"✅ Mise à jour {update_id} traitée avec succès")
                    except Exception as e:
                        logger.error(f"❌ Erreur lors du traitement de la mise à jour {update_id}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    # Mettre à jour l'offset pour ignorer les messages déjà traités
                    offset = update_id + 1
                
                # Réinitialiser le compteur d'erreurs après succès
                error_count = 0
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Arrêt du bot demandé par l'utilisateur")
            break
            
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Erreur dans la boucle de polling (tentative {error_count}/{max_errors}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            if error_count >= max_errors:
                logger.critical(f"❌ Trop d'erreurs consécutives ({max_errors}). Arrêt du bot.")
                break
            
            # Attendre avant de réessayer
            time.sleep(5)

if __name__ == '__main__':
    # Démarrer le serveur HTTP dans un thread séparé (pour Render.com)
    http_thread = threading.Thread(target=start_health_server, args=(config.PORT,), daemon=True)
    http_thread.start()
    logger.info(f"✅ Thread HTTP démarré sur le port {config.PORT}")
    
    # Démarrer le polling dans le thread principal
    run_polling()
