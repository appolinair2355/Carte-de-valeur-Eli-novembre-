#!/usr/bin/env python3
"""
Script pour configurer automatiquement le webhook Telegram
"""
import os
import requests

REPLIT_DEV_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not REPLIT_DEV_DOMAIN:
    print("❌ Erreur: REPLIT_DEV_DOMAIN n'est pas défini")
    exit(1)

if not BOT_TOKEN:
    print("❌ Erreur: BOT_TOKEN n'est pas configuré")
    exit(1)

webhook_url = f"https://{REPLIT_DEV_DOMAIN}/webhook"
api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"

print(f"🔧 Configuration du webhook Telegram...")
print(f"📍 URL du webhook: {webhook_url}")

try:
    response = requests.post(api_url, json={'url': webhook_url, 'drop_pending_updates': True})
    result = response.json()
    
    if result.get('ok'):
        print(f"✅ Webhook configuré avec succès !")
        print(f"📨 Vous pouvez maintenant envoyer des commandes à votre bot sur Telegram")
        print(f"\n🔗 URL complète du webhook: {webhook_url}")
    else:
        print(f"❌ Erreur lors de la configuration du webhook:")
        print(f"   {result.get('description', 'Erreur inconnue')}")
except Exception as e:
    print(f"❌ Exception: {e}")
