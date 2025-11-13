
#!/usr/bin/env python3
"""
Script pour vérifier si le bot est administrateur des canaux configurés
"""
import os
import requests

BOT_TOKEN = os.environ.get('BOT_TOKEN')
TARGET_CHANNEL_ID = os.environ.get('TARGET_CHANNEL_ID')
PREDICTION_CHANNEL_ID = os.environ.get('PREDICTION_CHANNEL_ID')

def check_admin_status(channel_id, channel_name):
    """Vérifie si le bot est administrateur d'un canal"""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    
    try:
        # Obtenir les informations du bot dans le canal
        response = requests.get(api_url, params={
            'chat_id': channel_id,
            'user_id': BOT_TOKEN.split(':')[0]  # L'ID du bot est avant les ':'
        })
        result = response.json()
        
        if result.get('ok'):
            member = result['result']
            status = member.get('status')
            
            print(f"\n{'='*60}")
            print(f"📊 Canal: {channel_name}")
            print(f"🆔 ID: {channel_id}")
            print(f"👤 Statut du bot: {status}")
            
            if status in ['administrator', 'creator']:
                permissions = member.get('can_post_messages', False)
                read_messages = member.get('can_read_all_group_messages', True)
                
                print(f"✅ Le bot EST administrateur")
                print(f"   - Peut poster des messages: {permissions}")
                print(f"   - Peut lire les messages: {read_messages}")
                return True
            else:
                print(f"❌ Le bot N'EST PAS administrateur (statut: {status})")
                return False
        else:
            error = result.get('description', 'Erreur inconnue')
            print(f"\n{'='*60}")
            print(f"📊 Canal: {channel_name}")
            print(f"🆔 ID: {channel_id}")
            print(f"❌ Erreur API: {error}")
            
            if "not found" in error.lower() or "chat not found" in error.lower():
                print(f"⚠️ Le bot n'a peut-être jamais été ajouté à ce canal")
            elif "user not found" in error.lower():
                print(f"⚠️ Le bot ne fait pas partie de ce canal")
            
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == '__main__':
    print("🔍 VÉRIFICATION DES PERMISSIONS ADMINISTRATEUR")
    print("="*60)
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN non configuré")
        exit(1)
    
    if not TARGET_CHANNEL_ID:
        print("❌ TARGET_CHANNEL_ID non configuré")
        exit(1)
    
    if not PREDICTION_CHANNEL_ID:
        print("❌ PREDICTION_CHANNEL_ID non configuré")
        exit(1)
    
    # Vérifier le canal source
    source_is_admin = check_admin_status(TARGET_CHANNEL_ID, "Canal SOURCE (Statistiques 21)")
    
    # Vérifier le canal de prédiction
    pred_is_admin = check_admin_status(PREDICTION_CHANNEL_ID, "Canal PRÉDICTION (Carte de valeur)")
    
    # Vérifier le canal qui envoie actuellement des messages
    mystery_channel = "-1002646551216"
    mystery_is_admin = check_admin_status(mystery_channel, "Canal ACTUEL (qui envoie des messages)")
    
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ")
    print("="*60)
    print(f"Canal SOURCE (configuré): {'✅ Admin' if source_is_admin else '❌ PAS Admin'}")
    print(f"Canal PRÉDICTION: {'✅ Admin' if pred_is_admin else '❌ PAS Admin'}")
    print(f"Canal ACTUEL ({mystery_channel}): {'✅ Admin' if mystery_is_admin else '❌ PAS Admin'}")
    
    if not source_is_admin:
        print(f"\n⚠️ ACTION REQUISE:")
        print(f"   1. Ajoutez le bot comme ADMINISTRATEUR au canal 'Statistiques 21'")
        print(f"   2. ID du canal: {TARGET_CHANNEL_ID}")
        print(f"   3. Donnez les permissions de lecture des messages")
