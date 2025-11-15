# 🤖 Bot Telegram DAME - Déploiement Render.com (Webhook)

## 📋 Variables d'Environnement REQUISES

Configurez ces 4 variables sur Render.com :

1. **BOT_TOKEN** : Votre token Telegram (depuis @BotFather)
2. **ADMIN_CHAT_ID** : Votre ID Telegram personnel
3. **TARGET_CHANNEL_ID** : ID du canal source (format: -1003424179389)
4. **PREDICTION_CHANNEL_ID** : ID du canal de prédiction (format: -1003362820311)

## 🚀 Instructions de Déploiement

### 1. Uploadez les fichiers sur GitHub
- Créez un nouveau dépôt GitHub
- Uploadez TOUS les fichiers du ZIP
- **IMPORTANT** : Renommez les fichiers suivants :
  - `Procfile_render` → `Procfile`
  - `render_re300.yaml` → `render.yaml`
  - `requirements_render.txt` → `requirements.txt`
- Commitez et poussez

### 2. Créez un Web Service sur Render.com
- Allez sur https://render.com
- Cliquez sur "New +" → "Web Service"
- Connectez votre dépôt GitHub
- Render détectera automatiquement render.yaml

### 3. Configurez les 4 variables d'environnement
- Dans la section "Environment"
- Ajoutez les 4 variables listées ci-dessus
- Cliquez sur "Create Web Service"

### 4. Vérification Automatique
- Le déploiement prendra 2-3 minutes
- **Le webhook sera configuré automatiquement**
- **Vous recevrez un message de test sur Telegram** avec :
  ```
  🚀 BOT DÉMARRÉ SUR RENDER.COM
  🌐 Webhook URL : https://votre-app.onrender.com/webhook
  📡 Canal Source : -1003424179389
  📤 Canal Prédiction : -1003362820311
  ✅ Configuration terminée - Le bot est prêt !
  ```

### 5. Premier Message du Canal
- Dès que le premier message arrive du canal source
- Vous recevrez une notification :
  ```
  ✅ BOT DÉPLOYÉ AVEC SUCCÈS SUR RENDER.COM
  🌐 Mode : WEBHOOK
  ✅ Le bot est opérationnel et attend les messages !
  ```

## ✅ Fonctionnalités

- ✅ Mode Webhook (pas de polling)
- ✅ Configuration automatique du webhook au démarrage
- ✅ **Notification automatique après déploiement**
- ✅ **Message de test envoyé à l'admin**
- ✅ 2 règles de prédiction automatique
- ✅ 2 déclencheurs intelligents
- ✅ Vérification automatique des prédictions
- ✅ Logs détaillés

## 🔧 Routes Disponibles

- `GET /` - Page d'accueil avec informations
- `POST /webhook` - Endpoint pour recevoir les webhooks Telegram
- `GET /health` - Health check pour Render
- `GET /set_webhook` - Reconfigurer le webhook manuellement
- `GET /delete_webhook` - Supprimer le webhook

## ⚠️ Problèmes Courants

**Le bot ne répond pas :**
- Vérifiez que les 4 variables d'environnement sont configurées
- Vérifiez les logs dans Render.com
- Assurez-vous que le BOT_TOKEN est valide

**Pas de message de test reçu :**
- Vérifiez que ADMIN_CHAT_ID est bien configuré
- Vérifiez les logs pour voir si le webhook a été configuré
- Appelez manuellement https://votre-app.onrender.com/set_webhook

**Le bot ne reçoit pas les messages des canaux :**
- Vérifiez que le bot est ajouté aux canaux avec les permissions d'administrateur
- Vérifiez que les IDs de canaux sont au bon format (négatifs)
