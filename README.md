# 🤖 Bot de Prédiction DAME (Q) - Cycle Intelligent

Ce projet implémente un bot Telegram en Python (mode Polling) dédié à l'anticipation de la carte Dame (Q) dans les tirages. Le bot est construit sur une architecture modulaire et est optimisé pour un déploiement stable sur Render.com en tant que **Web Service**.

## 🌟 Architecture Modulaire

L'application est structurée en plusieurs fichiers pour une meilleure maintenabilité :

| Fichier | Rôle Principal | Description |
| :--- | :--- | :--- |
| `main.py` | **Point d'Entrée & Port** | Lance le serveur Flask minimal (`0.0.0.0:$PORT`) pour le Health Check et démarre le Polling du bot dans un **thread séparé**. |
| `bot.py` | **API & Boucle de Polling** | Contient la classe `TelegramBot` qui gère toutes les requêtes `requests` vers l'API Telegram et exécute la boucle infinie de `getUpdates`. |
| `handlers.py` | **Gestionnaires de Commandes** | Contient la logique pour toutes les commandes (`/status`, `/inter`, `/defaut`) et la fonction `process_update` qui dispatche les messages et callbacks. |
| `card_predictor.py` | **Logique de Prédiction** | Contient la classe `CardPredictor` gérant l'état du Mode Intelligent, la stratégie de la Dame (Q), l'historique des tirages et la vérification des résultats. |
| `config.py` | **Configuration** | Charge toutes les variables d'environnement (`BOT_TOKEN`, IDs de canaux, etc.). |
| `Procfile` | **Lanceur Render** | Commande pour lancer le processus principal via Gunicorn, forçant l'écoute du port. |

## 🚀 Déploiement sur Render.com

Pour un déploiement réussi, suivez ces étapes :

### 1. Variables d'Environnement

Ces variables doivent être ajoutées à votre service **Web Service** sur Render :

| Variable | Description | Exemple de format |
| :--- | :--- | :--- |
| **`BOT_TOKEN`** | Jeton d'API fourni par BotFather. | `8442253971:AAExxxx` |
| **`ADMIN_CHAT_ID`** | Votre ID de chat personnel pour les alertes `/inter`. | `5622847726` |
| **`TARGET_CHANNEL_ID`** | ID du canal source (le canal que le bot lit). **Doit être négatif.** | `-1003424179389` |
| **`PREDICTION_CHANNEL_ID`** | ID du canal de prédiction (où le bot écrit). **Doit être négatif.** | `-1003362820311` |

### 2. Fichier `Procfile`

Le service doit être de type **Web Service** et utiliser Gunicorn pour lancer l'application sur le port dynamique :


web: gunicorn --bind 0.0.0.0:$PORT main:application

## 💡 Stratégie du Mode Intelligent (Q)

Le bot opère en **Mode Intelligent** uniquement lorsque celui-ci est activé (manuellement via `/inter` ou après avoir atteint 2 échecs consécutifs). La stratégie est la suivante :

| Signal Détecté (N-1) | Règle de Prédiction | Jeu Cible | Interprétation |
| :--- | :--- | :--- | :--- |
| **Valet (J) seul** (sans A ni K) | `Q_IMMEDIATE` | **N+2** | Messager de la Dame |
| **Roi (K) + Valet (J)** | `Q_IMMEDIATE` | **N+2** | Forte corrélation |
| **Double Valet (J...J)** | `Q_IMMEDIATE_JJ` | **N+2** | Signal fort et direct |
| **Roi (K) seul** (sans J ni A) | `Q_NEXT_DRAW` | **N+3** | Domination masculine temporaire |
| **As (A) + Roi (K)** | `Q_WAIT_1` | **N+3** | Blocage puis bascule |

## 🕹️ Commandes Utilisateur

Le bot répond aux commandes suivantes envoyées par l'administrateur dans un chat privé :

| Commande | Description |
| :--- | :--- |
| **`/start`** | Message de bienvenue. |
| **`/help`** | Affiche la liste des commandes. |
| **`/status`** | Affiche l'état du Mode Intelligent et le décompte des échecs consécutifs (`{compteur}/2`). |
| **`/inter`** | Lance l'analyse de l'historique (N-2 → Q) et propose d'activer/désactiver le Mode Intelligent via des boutons interactifs. |
| **`/defaut`** | **Désactive** le Mode Intelligent et réinitialise le compteur d'échecs à zéro. |

