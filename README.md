🤖 Bot de Prédiction DAME (Q) - Cycle Intelligent
Ce projet implémente un bot Telegram en Python (mode Polling) dédié à la prédiction de l'apparition de la carte Dame (Q) dans un jeu, en utilisant une stratégie basée sur les figures (Rois, Valets, As) observées dans les tirages précédents.
🌟 Fonctionnalités Clés
Mode Intelligent (Stratégie K/J/A/JJ) : Le bot utilise des règles conditionnelles avancées pour anticiper la Dame (Q) aux tirages N+2 ou N+3.
Vérification Automatique : Il suit ses propres prédictions et les marque comme ✅ (succès) ou ❌ (échec) en comparant le tirage final dans le canal source.
Historique et Analyse : Maintient un historique des derniers tirages pour l'analyse des cycles et la vérification des conditions N-2 → Q.
Déclenchement Interactif : En cas d'échecs consécutifs (> 2), il alerte l'administrateur via la commande /inter pour une réactivation manuelle ou une validation de la stratégie.
🚀 Déploiement (Render.com)
Ce bot est conçu pour être déployé en tant que Web Service sur Render.com afin de garantir la détection du port et la stabilité du processus continu (Polling).
1. Fichiers Requis

2. Fichier Description Rôle Principal
main.py Point d'entrée de l'application. Gère l'API Telegram, le Polling, les commandes, et utilise le threading pour écouter le port 10000. Cœur du bot et Threading
card_predictor.py Contient toute la logique métier : règles de Dame (Q), gestion de l'état, de l'historique et des échecs. Logique de Prédiction
Procfile Définit le processus de lancement pour Render (utilise Gunicorn). Lancement Gunicorn
requirements.txt Liste des dépendances Python. Dépendances
