"""
Logique de prédiction et gestion de l'état (Mode Intelligent, Historique)
Ce module contient l'objet CardPredictor, le cœur de la stratégie.
"""

import re
import logging
from typing import Optional, Dict, Tuple
import time
import os

logger = logging.getLogger(__name__)

# --- Configuration de l'État ---

class CardPredictor:
    """Handles card prediction logic and state management."""

    def __init__(self):
        self.predictions = {} 
        self.processed_messages = set() 
        self.last_prediction_time = 0.0
        self.last_dame_prediction = None 
        
        # État du mode intelligent
        self.consecutive_failures = 0
        self.intelligent_mode_active = False
        self.MAX_FAILURES_BEFORE_INTELLIGENT_MODE = 2
        
        # Gestion de l'historique
        self.draw_history = {} 
        self.history_limit = 10 
        
    # --- Utilitaires d'Extraction ---

    def extract_game_number(self, message: str) -> Optional[int]:
        """Extrait le numéro de jeu du message comme #n744 ou #N744."""
        pattern = r'#[nN](\d+)\.?' 
        match = re.search(pattern, message)
        if match:
            return int(match.group(1))
        return None
    
    def extract_first_group_content(self, message: str) -> Optional[str]:
        """Extrait le contenu à l'intérieur du premier groupe de parenthèses."""
        pattern = r'\(.*?\)'
        match = re.search(pattern, message)
        if match:
            return match.group(0).strip('()')
        return None

    def extract_first_two_cards_with_value(self, message: str) -> Optional[str]:
        """Extrait les deux premières cartes avec leur couleur/valeur du premier groupe."""
        pattern_group = r'\(.*?\)'
        match_group = re.search(pattern_group, message)
        if not match_group:
            return None
        
        content = match_group.group(0).strip('()')
        card_pattern = r'[AKQJ\d]+[♥️♠️♦️♣️❤️]'
        cards = re.findall(card_pattern, content)
        
        if len(cards) >= 2:
            return cards[0] + cards[1]
            
        return None
        
    def extract_figure_signals(self, message: str) -> Dict[str, bool]:
        """Détecte la présence de figures (J, K, A)."""
        signals = {'J': False, 'K': False, 'A': False}
        if re.search(r'\b[JjVv]\b', message) or 'Valet' in message: 
             signals['J'] = True
        if re.search(r'\b[KkRr]\b', message) or 'Roi' in message:
             signals['K'] = True
        if re.search(r'\b[Aa]\b', message) or 'As' in message: 
             signals['A'] = True
        return signals

    def check_dame_in_first_group(self, message: str) -> bool:
        """Vérifie la présence de la Dame (Q) dans le premier groupe."""
        first_group_content = self.extract_first_group_content(message)
        if not first_group_content:
            return False
        return bool(re.search(r'\b[Qq]\b|Dame', first_group_content))

    def has_completion_indicators(self, text: str) -> bool:
        """Vérifie si le message source est finalisé (contient des indicateurs de fin)."""
        COMPLETION_INDICATORS = ['✅', '🔰', '❌', '🔴']
        return any(indicator in text for indicator in COMPLETION_INDICATORS)

    # --- Logique de Prédiction ---
    
    def check_dame_rule(self, signals: Dict[str, bool], first_group_content: str) -> Optional[str]:
        """Applique la Stratégie de Mise Dame (Q) : détermine la règle à appliquer."""
        
        # Règle spéciale Double Valet (JJ)
        if re.search(r'J.*J', first_group_content, re.IGNORECASE):
             return "Q_IMMEDIATE_JJ" 
             
        J, K, A = signals['J'], signals['K'], signals['A']
        
        # Règle 1: Valet seul OU Roi + Valet
        if (J and not K and not A) or (K and J):
            return "Q_IMMEDIATE" 
        # Règle 2: Roi seul
        if K and not A:
            return "Q_NEXT_DRAW" # N+3
        # Règle 3: As + Roi
        if K and A:
            return "Q_WAIT_1" # N+3
            
        return None 
        
    def should_predict(self, message: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Vérifie si une prédiction de Dame doit être faite."""
        game_number = self.extract_game_number(message)
        if not game_number: return False, None, None

        if self.has_completion_indicators(message): return False, None, None 
        
        # Prédiction uniquement si le Mode Intelligent est ACTIF
        if not self.intelligent_mode_active:
             return False, None, None
        
        signals = self.extract_figure_signals(message)
        first_group = self.extract_first_group_content(message)
        
        if not first_group: return False, None, None
        
        dame_prediction = self.check_dame_rule(signals, first_group)
        
        if dame_prediction:
            predicted_value = f"Q:{dame_prediction}"
            message_hash = hash(message)
            if message_hash not in self.processed_messages:
                self.processed_messages.add(message_hash)
                self.last_prediction_time = time.time()
                self.last_dame_prediction = predicted_value
                return True, game_number, predicted_value
        
        return False, None, None

    def make_prediction(self, game_number: int, predicted_value_or_costume: str) -> Dict:
        """Crée l'objet de prédiction et génère le message."""
        dame_rule = predicted_value_or_costume.split(':')[1]
        
        if dame_rule in ["Q_IMMEDIATE", "Q_IMMEDIATE_JJ"]:
             target_game = game_number + 2
             if dame_rule == "Q_IMMEDIATE_JJ":
                 prediction_text = f"🎯{target_game}🎯: Dame (Q) **IMMINENTE** (JJ) statut :⏳"
             else:
                 prediction_text = f"🎯{target_game}🎯: Dame (Q) **IMMINENTE** (J/K+J) statut :⏳"
                 
        elif dame_rule in ["Q_NEXT_DRAW", "Q_WAIT_1"]:
             target_game = game_number + 3 
             if dame_rule == "Q_NEXT_DRAW":
                 prediction_text = f"🎯{target_game}🎯: Dame (Q) **PROCHAIN** (K seul) statut :⏳"
             else: # Q_WAIT_1
                 prediction_text = f"🎯{target_game}🎯: Dame (Q) **ATTENTE 1** (A+K) statut :⏳"
        else:
             target_game = game_number + 2
             prediction_text = f"🎯{target_game}🎯: Dame (Q) **EN COURS** statut :⏳"

        self.predictions[target_game] = {
            'predicted_costume_or_value': predicted_value_or_costume,
            'status': 'pending',
            'predicted_from': game_number,
            'message_text': prediction_text,
            'is_dame_prediction': predicted_value_or_costume.startswith('Q:') 
        }
        
        return {'text': prediction_text, 'target_game': target_game}


    def verify_prediction(self, text: str, message_id: Optional[int] = None) -> Optional[Dict]:
        """Vérifie si une prédiction en attente correspond au tirage actuel."""
        game_number = self.extract_game_number(text)
        if not game_number: return None

        if not self.has_completion_indicators(text):
            return None

        # --- GESTION DE L'HISTORIQUE (pour la fonction /inter) ---
        first_group_content = self.extract_first_group_content(text) 
        first_two_cards = self.extract_first_two_cards_with_value(text) 
        
        if first_group_content:
            self.draw_history[game_number] = {
                'text': text, 
                'first_group': first_group_content, 
                'message_id': message_id,
                'first_two_cards': first_two_cards 
            }
        
            if len(self.draw_history) > self.history_limit:
                oldest_key = min(self.draw_history.keys())
                del self.draw_history[oldest_key]
        # -----------------------------------------------------
        
        if not self.predictions: return None

        for predicted_game in sorted(self.predictions.keys()):
            prediction = self.predictions[predicted_game]
            if prediction.get('status') != 'pending': continue

            verification_offset = game_number - predicted_game
            is_dame_prediction = prediction.get('is_dame_prediction', False) 

            # Traitement uniquement si c'est une prédiction de Dame
            if not is_dame_prediction: continue
            
            # Décalage maximal pour la vérification (N+3)
            max_offset_dame = 3 
            if verification_offset < 0: continue # Le tirage n'est pas encore arrivé
            
            status_symbol = None
            should_fail = False
            
            if verification_offset == 0:
                # Vérification au jeu cible (N+2 ou N+3)
                status_symbol = "✅"
            elif 0 < verification_offset <= max_offset_dame:
                # Vérification dans les jeux suivants si le jeu cible est raté
                status_symbol = "✅"
            elif verification_offset > max_offset_dame:
                # Échec final après le décalage maximal
                status_symbol = "❌"
                should_fail = True
            else:
                continue

            costume_or_value_found = False
            original_message = prediction.get('message_text')

            if not should_fail:
                costume_or_value_found = self.check_dame_in_first_group(text) 

            if costume_or_value_found:
                # SUCCÈS
                updated_message = original_message.replace("statut :⏳", f"statut :{status_symbol}")
                prediction['status'] = 'correct'
                self.consecutive_failures = 0
                
                return {
                    'type': 'edit_message', 'predicted_game': predicted_game, 
                    'new_message': updated_message, 'original_message': original_message
                }
            
            elif should_fail:
                # ÉCHEC FINAL
                updated_message = original_message.replace("statut :⏳", "statut :❌")
                prediction['status'] = 'failed'
                
                self.consecutive_failures += 1

                # Déclenchement du prompt /inter pour l'administrateur
                if self.consecutive_failures == self.MAX_FAILURES_BEFORE_INTELLIGENT_MODE:
                     return {'type': 'fail_threshold_reached'} 

                return {
                    'type': 'edit_message', 'predicted_game': predicted_game, 
                    'new_message': updated_message, 'original_message': original_message
                }
            else:
                continue
                
        return None

card_predictor = CardPredictor()
