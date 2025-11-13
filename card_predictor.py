"""
Logique de prédiction et gestion de l'état (Mode Intelligent, Historique)
Utilise uniquement les messages source contenant les indicateurs de finalisation '✅' ou '🔰'.
"""

import re
import logging
from typing import Optional, Dict, Tuple
import time
import os

logger = logging.getLogger(__name__)

# IDs (Seront lus depuis les variables d'environnement)
TARGET_CHANNEL_ID = os.environ.get('TARGET_CHANNEL_ID')
PREDICTION_CHANNEL_ID = os.environ.get('PREDICTION_CHANNEL_ID')
COMPLETION_INDICATORS = ['✅', '🔰']

class CardPredictor:
    """Handles card prediction logic and state management."""

    def __init__(self):
        self.predictions = {} 
        self.processed_messages = set() 
        self.last_prediction_time = self._load_last_prediction_time()
        self.prediction_cooldown = 0   
        self.last_dame_prediction = None 
        
        self.consecutive_failures = 0
        self.intelligent_mode_active = False
        self.MAX_FAILURES_BEFORE_INTELLIGENT_MODE = 2
        
        self.draw_history = {} 
        self.history_limit = 10 
        
    def _load_last_prediction_time(self) -> float:
        return 0.0

    def _save_last_prediction_time(self):
        pass 

    # --- Utilitaires d'Extraction ---

    def extract_game_number(self, message: str) -> Optional[int]:
        """Extract game number from message like #n744 or #N744."""
        pattern = r'#[nN](\d+)\.?' 
        match = re.search(pattern, message)
        if match:
            return int(match.group(1))
        return None
    
    def extract_first_group_content(self, message: str) -> Optional[str]:
        """Extracts content inside the first parentheses group (full content)."""
        pattern = r'\(.*?\)'
        match = re.search(pattern, message)
        if match:
            return match.group(0).strip('()')
        return None

    def extract_first_two_cards_with_value(self, message: str) -> Optional[str]:
        """
        Extracts the first two cards with their suits/values from the first group.
        Ex: #N876. 18(8♠️10♦️) - 26(...) -> returns '8♠️10♦️'
        """
        pattern_group = r'\(.*?\)'
        match_group = re.search(pattern_group, message)
        if not match_group:
            return None
        
        content = match_group.group(0).strip('()')
        
        # Recherche des paires Valeur (1 ou 2 chars) + Symbole de carte
        card_pattern = r'[AKQJ\d]+[♥️♠️♦️♣️❤️]'
        cards = re.findall(card_pattern, content)
        
        if len(cards) >= 2:
            return cards[0] + cards[1]
            
        return None
        
    def extract_figure_signals(self, message: str) -> Dict[str, bool]:
        signals = {'J': False, 'K': False, 'A': False}
        if re.search(r'\b[JjVv]\b', message) or 'Valet' in message: 
             signals['J'] = True
        if re.search(r'\b[KkRr]\b', message) or 'Roi' in message:
             signals['K'] = True
        if re.search(r'\b[Aa]\b', message) or 'As' in message: 
             signals['A'] = True
        return signals

    def check_dame_in_first_group(self, message: str) -> bool:
        first_group_content = self.extract_first_group_content(message)
        if not first_group_content:
            return False
        return bool(re.search(r'\b[Qq]\b|Dame', first_group_content))

    def has_completion_indicators(self, text: str) -> bool:
        """Vérifie si le message contient les indicateurs de finalisation."""
        return any(indicator in text for indicator in COMPLETION_INDICATORS)

    # --- Logique de Prédiction ---
    
    def check_dame_rule(self, signals: Dict[str, bool], first_group_content: str) -> Optional[str]:
        """Applique la Stratégie de Mise Dame (Q) évolutive, y compris JJ."""
        
        if re.search(r'J.*J', first_group_content, re.IGNORECASE):
             return "Q_IMMEDIATE_JJ" 
             
        J, K, A = signals['J'], signals['K'], signals['A']
        
        if (J and not K and not A) or (K and J):
            return "Q_IMMEDIATE" 
        if K and not A:
            return "Q_NEXT_DRAW"
        if K and A:
            return "Q_WAIT_1"
            
        return None 
        
    def should_predict(self, message: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """Déclenchement de la prédiction uniquement si le Mode Intelligent est ACTIF."""
        game_number = self.extract_game_number(message)
        if not game_number: return False, None, None

        # La prédiction ne doit pas se baser sur un tirage déjà finalisé.
        if self.has_completion_indicators(message): return False, None, None 
        
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
                self._save_last_prediction_time()
                self.last_dame_prediction = predicted_value
                return True, game_number, predicted_value
        
        return False, None, None

    def make_prediction(self, game_number: int, predicted_value_or_costume: str) -> Dict:
        """Prépare le message et met à jour l'état interne pour l'envoi."""
        dame_rule = predicted_value_or_costume.split(':')[1]
        
        # Détermination du jeu cible N+2 ou N+3 et du message
        if dame_rule in ["Q_IMMEDIATE", "Q_IMMEDIATE_JJ"]:
             target_game = game_number + 2
             if dame_rule == "Q_IMMEDIATE_JJ":
                 prediction_text = f"🎯{target_game}🎯: Dame (Q) **IMMINENTE** (JJ) statut :⏳"
             else:
                 prediction_text = f"🎯{target_game}🎯: Dame (Q) **IMMINENTE** (J/K+J) statut :⏳"
                 
        elif dame_rule == "Q_NEXT_DRAW":
             target_game = game_number + 3 
             prediction_text = f"🎯{target_game}🎯: Dame (Q) **PROCHAIN** (K seul) statut :⏳"
             
        elif dame_rule == "Q_WAIT_1":
             target_game = game_number + 3 
             prediction_text = f"🎯{target_game}🎯: Dame (Q) **ATTENTE 1** (A+K) statut :⏳"
        else:
             target_game = game_number + 2
             prediction_text = f"🎯{target_game}🎯: Dame (Q) **EN COURS** statut :⏳"

        self.predictions[target_game] = {
            'predicted_costume_or_value': predicted_value_or_costume,
            'status': 'pending',
            'predicted_from': game_number,
            'verification_count': 0,
            'message_text': prediction_text,
            'is_dame_prediction': predicted_value_or_costume.startswith('Q:') 
        }
        
        return {'text': prediction_text, 'target_game': target_game}


    def verify_prediction(self, text: str, message_id: Optional[int] = None) -> Optional[Dict]:
        """Vérification N, N+1, N+2, N+3 et gestion de l'historique."""
        game_number = self.extract_game_number(text)
        if not game_number: return None

        # Traiter uniquement si le message est finalisé
        if not self.has_completion_indicators(text):
            return None

        # --- GESTION DE L'HISTORIQUE (pour les messages finalisés uniquement) ---
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
        # ---------------------------------------------------------------------
        
        if not self.predictions: return None

        for predicted_game in sorted(self.predictions.keys()):
            prediction = self.predictions[predicted_game]
            if prediction.get('status') != 'pending': continue

            verification_offset = game_number - predicted_game
            is_dame_prediction = prediction.get('is_dame_prediction', False) 

            status_symbol = None
            should_fail = False
            
            if is_dame_prediction:
                max_offset_dame = 3 
                if verification_offset < 0: continue
                
                if verification_offset in [0, 1, 2, 3]:
                    status_symbol = f"✅{verification_offset}️⃣"
                
                elif verification_offset > max_offset_dame:
                    status_symbol = "❌"
                    should_fail = True
                else: continue
            else: continue 

            costume_or_value_found = False
            if not should_fail and is_dame_prediction:
                costume_or_value_found = self.check_dame_in_first_group(text) 

            original_message = prediction.get('message_text')

            if costume_or_value_found:
                # SUCCÈS
                updated_message = original_message.replace("statut :⏳", f"statut :{status_symbol}")
                prediction['status'] = 'correct'
                
                if is_dame_prediction:
                    self.consecutive_failures = 0
                
                return {
                    'type': 'edit_message', 'predicted_game': predicted_game, 
                    'new_message': updated_message, 'original_message': original_message
                }
            
            elif should_fail:
                # ÉCHEC FINAL
                updated_message = original_message.replace("statut :⏳", "statut :❌")
                prediction['status'] = 'failed'
                
                if is_dame_prediction:
                    self.consecutive_failures += 1

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
