"""
Python Syntax Card Game - Game Logic
Contains card definitions, deck management, validation rules, and game state.
"""

import random
from typing import Optional, Dict, List, Any

# =============================================================================
# CARD CATEGORIES
# =============================================================================

CATEGORIES = {
    'LOOP': 'Loop keywords like for, while',
    'VARIABLE': 'Variable names like x, i, n, item',
    'KEYWORD': 'Python keywords like in, if, else, def, return',
    'FUNCTION': 'Built-in functions like range, print, len, input',
    'VALUE': 'Values like 1, 10, True, False, strings',
    'OPERATOR': 'Operators like +, -, ==, and, or, <, >',
    'SYNTAX_OPEN': 'Opening parenthesis (',
    'SYNTAX_CLOSE': 'Closing parenthesis )',
    'SYNTAX_COLON': 'Colon :',
    'SPECIAL': 'Special action cards',
    'START': 'Virtual category for game start'
}

# =============================================================================
# CARD DEFINITIONS
# Each card has: category, points, can_follow (list of categories it can follow)
# Optional: effect (for special cards), count (copies in deck)
# =============================================================================

CARDS = {
    # -------------------------------------------------------------------------
    # LOOP CARDS (Uncommon - 2 points)
    # -------------------------------------------------------------------------
    "for": {
        "category": "LOOP",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 3,
        "description": "For loop - iterates over a sequence"
    },
    "while": {
        "category": "LOOP",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "While loop - repeats while condition is true"
    },

    # -------------------------------------------------------------------------
    # VARIABLE CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "x": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 4,
        "description": "Common variable name"
    },
    "i": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 4,
        "description": "Iterator variable"
    },
    "n": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 3,
        "description": "Number variable"
    },
    "item": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 3,
        "description": "Item in a collection"
    },
    "result": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Result variable"
    },

    # -------------------------------------------------------------------------
    # KEYWORD CARDS (Uncommon - 2 points)
    # -------------------------------------------------------------------------
    "in": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["VARIABLE"],
        "count": 4,
        "description": "Membership test / iteration"
    },
    "if": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 3,
        "description": "Conditional statement"
    },
    "else": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["SYNTAX_COLON"],
        "count": 2,
        "description": "Alternative branch"
    },
    "elif": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["SYNTAX_COLON"],
        "count": 2,
        "description": "Else-if branch"
    },
    "not": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Logical negation"
    },

    # -------------------------------------------------------------------------
    # RARE KEYWORD CARDS (Rare - 3 points)
    # -------------------------------------------------------------------------
    "def": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "Function definition"
    },
    "return": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["SYNTAX_COLON", "START"],
        "count": 2,
        "description": "Return statement"
    },
    "lambda": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["OPERATOR", "SYNTAX_OPEN", "KEYWORD"],
        "count": 1,
        "description": "Anonymous function"
    },
    "class": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 1,
        "description": "Class definition"
    },
    "try": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 1,
        "description": "Exception handling"
    },
    "except": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["SYNTAX_COLON"],
        "count": 1,
        "description": "Exception handler"
    },

    # -------------------------------------------------------------------------
    # FUNCTION CARDS (Uncommon - 2 points)
    # -------------------------------------------------------------------------
    "range": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 4,
        "description": "Generate number sequence"
    },
    "print": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 3,
        "description": "Output to console"
    },
    "len": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 3,
        "description": "Get length of sequence"
    },
    "input": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Get user input"
    },
    "int": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Convert to integer"
    },
    "str": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Convert to string"
    },
    "list": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Create a list"
    },
    "sum": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Sum of sequence"
    },

    # -------------------------------------------------------------------------
    # VALUE CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "0": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "OPERATOR", "KEYWORD"],
        "count": 3,
        "description": "Number zero"
    },
    "1": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "OPERATOR", "KEYWORD"],
        "count": 4,
        "description": "Number one"
    },
    "10": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "OPERATOR", "KEYWORD"],
        "count": 3,
        "description": "Number ten"
    },
    "100": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "OPERATOR", "KEYWORD"],
        "count": 2,
        "description": "Number hundred"
    },
    "True": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 3,
        "description": "Boolean true"
    },
    "False": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 3,
        "description": "Boolean false"
    },
    "None": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "None value"
    },
    '"hello"': {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "OPERATOR", "KEYWORD"],
        "count": 2,
        "description": "String literal"
    },
    "[]": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 2,
        "description": "Empty list"
    },

    # -------------------------------------------------------------------------
    # OPERATOR CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "+": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 3,
        "description": "Addition"
    },
    "-": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 3,
        "description": "Subtraction"
    },
    "*": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 2,
        "description": "Multiplication"
    },
    "/": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 2,
        "description": "Division"
    },
    "==": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 3,
        "description": "Equality check"
    },
    "!=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 2,
        "description": "Not equal check"
    },
    "<": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 3,
        "description": "Less than"
    },
    ">": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 3,
        "description": "Greater than"
    },
    "<=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 2,
        "description": "Less than or equal"
    },
    ">=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 2,
        "description": "Greater than or equal"
    },
    "and": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 2,
        "description": "Logical and"
    },
    "or": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 2,
        "description": "Logical or"
    },
    "=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VARIABLE"],
        "count": 4,
        "description": "Assignment"
    },
    "+=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VARIABLE"],
        "count": 2,
        "description": "Add and assign"
    },

    # -------------------------------------------------------------------------
    # SYNTAX CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "(": {
        "category": "SYNTAX_OPEN",
        "points": 1,
        "can_follow": ["FUNCTION", "KEYWORD"],
        "count": 6,
        "description": "Open parenthesis"
    },
    ")": {
        "category": "SYNTAX_CLOSE",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 6,
        "description": "Close parenthesis"
    },
    ":": {
        "category": "SYNTAX_COLON",
        "points": 1,
        "can_follow": ["SYNTAX_CLOSE", "VALUE", "VARIABLE", "KEYWORD"],
        "count": 5,
        "description": "Colon - ends statement"
    },

    # -------------------------------------------------------------------------
    # SPECIAL CARDS (0 points - action effects)
    # -------------------------------------------------------------------------
    "Draw 2": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 3,
        "effect": "draw_2",
        "description": "Force opponent to draw 2 cards"
    },
    "Discard 2": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 2,
        "effect": "discard_2",
        "description": "Force opponent to discard 2 random cards"
    },
    "Skip": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 3,
        "effect": "skip",
        "description": "Skip opponent's turn"
    },
    "Wild": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 2,
        "effect": "wild",
        "description": "Can be played as any category"
    },
}

# =============================================================================
# DECK MANAGEMENT
# =============================================================================

def create_deck() -> List[str]:
    """
    Create a full deck of cards based on card definitions.
    Returns a list of card names (with duplicates based on count).
    """
    deck = []
    for card_name, card_data in CARDS.items():
        count = card_data.get("count", 1)
        deck.extend([card_name] * count)
    return deck


def shuffle_deck(deck: List[str]) -> List[str]:
    """Shuffle a deck of cards in place and return it."""
    random.shuffle(deck)
    return deck


def draw_cards(deck: List[str], num_cards: int) -> List[str]:
    """
    Draw cards from the top of the deck.
    Returns a list of drawn cards.
    """
    drawn = []
    for _ in range(min(num_cards, len(deck))):
        if deck:
            drawn.append(deck.pop())
    return drawn


# =============================================================================
# CARD VALIDATION
# =============================================================================

def get_last_card_category(played_cards: List[str]) -> str:
    """
    Get the category of the last played card.
    Returns 'START' if no cards have been played.
    """
    if not played_cards:
        return "START"
    
    last_card = played_cards[-1]
    if last_card in CARDS:
        return CARDS[last_card]["category"]
    return "START"


def can_play_card(card_name: str, played_cards: List[str]) -> bool:
    """
    Check if a card can be played given the current played cards.
    Returns True if the card can be played, False otherwise.
    """
    if card_name not in CARDS:
        return False
    
    card = CARDS[card_name]
    last_category = get_last_card_category(played_cards)
    
    # Special cards (except Wild) can be played anytime
    if card["category"] == "SPECIAL":
        return True
    
    # Check if the card can follow the last played category
    can_follow = card.get("can_follow", [])
    return last_category in can_follow


def get_playable_cards(hand: List[str], played_cards: List[str]) -> List[str]:
    """
    Get all cards from hand that can be legally played.
    Returns a list of playable card names.
    """
    return [card for card in hand if can_play_card(card, played_cards)]


def is_special_card(card_name: str) -> bool:
    """Check if a card is a special action card."""
    if card_name not in CARDS:
        return False
    return CARDS[card_name]["category"] == "SPECIAL"


def get_card_effect(card_name: str) -> Optional[str]:
    """Get the effect of a special card, or None if not a special card."""
    if card_name not in CARDS:
        return None
    return CARDS[card_name].get("effect")


def get_card_points(card_name: str) -> int:
    """Get the point value of a card."""
    if card_name not in CARDS:
        return 0
    return CARDS[card_name].get("points", 0)


def get_card_info(card_name: str) -> Optional[Dict[str, Any]]:
    """Get full information about a card."""
    return CARDS.get(card_name)


# =============================================================================
# GAME STATE CLASS
# =============================================================================

class GameState:
    """Manages the state of a game session."""
    
    # Game constants
    STARTING_HAND_SIZE = 7
    WIN_SCORE = 50
    MAX_CONSECUTIVE_PASSES = 3
    
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.players: List[str] = []
        self.player_names: Dict[str, str] = {}  # player_id: display_name
        self.hands: Dict[str, List[str]] = {}  # player_id: [cards]
        self.played_cards: List[str] = []
        self.scores: Dict[str, int] = {}  # player_id: score
        self.current_turn: int = 0  # Index in players list
        self.deck: List[str] = []
        self.game_started: bool = False
        self.game_over: bool = False
        self.winner: Optional[str] = None
        self.consecutive_passes: Dict[str, int] = {}  # player_id: pass_count
        self.last_action: Optional[Dict[str, Any]] = None
        self.turn_number: int = 0
    
    def add_player(self, player_id: str, player_name: str = None) -> bool:
        """Add a player to the game. Returns True if successful."""
        if len(self.players) >= 2:
            return False
        if player_id in self.players:
            return False
        
        self.players.append(player_id)
        self.player_names[player_id] = player_name or f"Player {len(self.players)}"
        self.hands[player_id] = []
        self.scores[player_id] = 0
        self.consecutive_passes[player_id] = 0
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the game. Returns True if successful."""
        if player_id not in self.players:
            return False
        
        self.players.remove(player_id)
        self.hands.pop(player_id, None)
        self.scores.pop(player_id, None)
        self.player_names.pop(player_id, None)
        self.consecutive_passes.pop(player_id, None)
        return True
    
    def is_ready(self) -> bool:
        """Check if the game has 2 players and is ready to start."""
        return len(self.players) == 2
    
    def start_game(self) -> bool:
        """
        Initialize and start the game.
        Returns True if game started successfully.
        """
        if not self.is_ready():
            return False
        if self.game_started:
            return False
        
        # Create and shuffle the deck
        self.deck = shuffle_deck(create_deck())
        
        # Deal starting hands
        for player_id in self.players:
            self.hands[player_id] = draw_cards(self.deck, self.STARTING_HAND_SIZE)
        
        # Randomly determine who goes first
        self.current_turn = random.randint(0, 1)
        self.game_started = True
        self.turn_number = 1
        
        return True
    
    def get_current_player(self) -> Optional[str]:
        """Get the player ID of the current turn."""
        if not self.players:
            return None
        return self.players[self.current_turn]
    
    def get_opponent(self, player_id: str) -> Optional[str]:
        """Get the opponent's player ID."""
        if player_id not in self.players:
            return None
        for p in self.players:
            if p != player_id:
                return p
        return None
    
    def is_player_turn(self, player_id: str) -> bool:
        """Check if it's the specified player's turn."""
        return self.get_current_player() == player_id
    
    def next_turn(self) -> None:
        """Advance to the next player's turn."""
        self.current_turn = (self.current_turn + 1) % 2
        self.turn_number += 1
    
    def play_card(self, player_id: str, card_name: str) -> Dict[str, Any]:
        """
        Attempt to play a card.
        Returns a result dict with success status and any messages/effects.
        """
        result = {
            "success": False,
            "message": "",
            "effect": None,
            "points_earned": 0
        }
        
        # Validate game state
        if not self.game_started:
            result["message"] = "Game has not started yet"
            return result
        
        if self.game_over:
            result["message"] = "Game is already over"
            return result
        
        if not self.is_player_turn(player_id):
            result["message"] = "It's not your turn"
            return result
        
        # Validate card is in player's hand
        if card_name not in self.hands.get(player_id, []):
            result["message"] = "You don't have that card"
            return result
        
        # Validate card can be played
        if not can_play_card(card_name, self.played_cards):
            result["message"] = f"Cannot play '{card_name}' after the current card"
            return result
        
        # Play the card
        self.hands[player_id].remove(card_name)
        self.consecutive_passes[player_id] = 0  # Reset pass counter
        
        # Handle special cards
        effect = get_card_effect(card_name)
        if effect:
            result["effect"] = effect
            effect_result = self._apply_special_effect(player_id, effect)
            result["message"] = effect_result["message"]
        else:
            # Regular card - add to played cards and score points
            self.played_cards.append(card_name)
            points = get_card_points(card_name)
            self.scores[player_id] += points
            result["points_earned"] = points
            result["message"] = f"Played '{card_name}' for {points} points"
        
        # Record the action
        self.last_action = {
            "type": "play",
            "player": player_id,
            "card": card_name,
            "effect": effect
        }
        
        # Check win conditions
        winner = self._check_win_conditions()
        if winner:
            self.game_over = True
            self.winner = winner
            result["message"] += f" | {self.player_names.get(winner, winner)} wins!"
        
        # Advance turn (unless skip effect was applied)
        if effect != "skip":
            self.next_turn()
        
        result["success"] = True
        return result
    
    def _apply_special_effect(self, player_id: str, effect: str) -> Dict[str, str]:
        """Apply a special card effect. Returns result message."""
        opponent_id = self.get_opponent(player_id)
        
        if effect == "draw_2":
            if opponent_id and self.deck:
                drawn = draw_cards(self.deck, 2)
                self.hands[opponent_id].extend(drawn)
                return {"message": f"Opponent draws {len(drawn)} cards!"}
            return {"message": "Draw 2 played (deck empty)"}
        
        elif effect == "discard_2":
            if opponent_id and self.hands.get(opponent_id):
                opponent_hand = self.hands[opponent_id]
                num_discard = min(2, len(opponent_hand))
                discarded = random.sample(opponent_hand, num_discard)
                for card in discarded:
                    opponent_hand.remove(card)
                return {"message": f"Opponent discards {num_discard} cards!"}
            return {"message": "Discard 2 played (opponent has no cards)"}
        
        elif effect == "skip":
            return {"message": "Opponent's turn skipped!"}
        
        elif effect == "wild":
            # Wild card acts as a bridge - doesn't add to played cards
            # but resets the sequence so any card can follow
            return {"message": "Wild card played! Any card can follow."}
        
        return {"message": "Special effect applied"}
    
    def pass_turn(self, player_id: str) -> Dict[str, Any]:
        """
        Pass the turn (when no valid moves available).
        Returns result dict.
        """
        result = {
            "success": False,
            "message": "",
            "drew_card": None
        }
        
        if not self.game_started:
            result["message"] = "Game has not started yet"
            return result
        
        if self.game_over:
            result["message"] = "Game is already over"
            return result
        
        if not self.is_player_turn(player_id):
            result["message"] = "It's not your turn"
            return result
        
        # Check if player actually has no valid moves
        playable = get_playable_cards(self.hands.get(player_id, []), self.played_cards)
        if playable:
            result["message"] = "You have valid cards to play"
            return result
        
        # Draw a card if deck is not empty
        if self.deck:
            drawn = draw_cards(self.deck, 1)
            if drawn:
                self.hands[player_id].extend(drawn)
                result["drew_card"] = drawn[0]
                result["message"] = f"Drew a card: {drawn[0]}"
        
        # Increment pass counter
        self.consecutive_passes[player_id] += 1
        
        # Record action
        self.last_action = {
            "type": "pass",
            "player": player_id,
            "drew_card": result.get("drew_card")
        }
        
        # Check if player has passed too many times
        if self.consecutive_passes[player_id] >= self.MAX_CONSECUTIVE_PASSES:
            opponent_id = self.get_opponent(player_id)
            if opponent_id:
                self.game_over = True
                self.winner = opponent_id
                result["message"] += f" | {self.player_names.get(opponent_id, 'Opponent')} wins (opponent couldn't play)!"
        
        # Check other win conditions
        winner = self._check_win_conditions()
        if winner and not self.game_over:
            self.game_over = True
            self.winner = winner
        
        self.next_turn()
        result["success"] = True
        return result
    
    def _check_win_conditions(self) -> Optional[str]:
        """
        Check all win conditions.
        Returns the winner's player_id or None.
        """
        for player_id in self.players:
            # Win condition 1: Reach 50 points
            if self.scores.get(player_id, 0) >= self.WIN_SCORE:
                return player_id
            
            # Win condition 3: Deck empty and player has no cards
            if not self.deck and not self.hands.get(player_id):
                return player_id
        
        return None
    
    def get_game_state_for_player(self, player_id: str) -> Dict[str, Any]:
        """
        Get the game state formatted for a specific player.
        Hides opponent's actual cards.
        """
        opponent_id = self.get_opponent(player_id)
        
        return {
            "room_code": self.room_code,
            "game_started": self.game_started,
            "game_over": self.game_over,
            "winner": self.winner,
            "winner_name": self.player_names.get(self.winner) if self.winner else None,
            "turn_number": self.turn_number,
            "current_player": self.get_current_player(),
            "is_your_turn": self.is_player_turn(player_id),
            "your_hand": self.hands.get(player_id, []),
            "your_score": self.scores.get(player_id, 0),
            "opponent_card_count": len(self.hands.get(opponent_id, [])) if opponent_id else 0,
            "opponent_score": self.scores.get(opponent_id, 0) if opponent_id else 0,
            "opponent_name": self.player_names.get(opponent_id, "Opponent") if opponent_id else None,
            "your_name": self.player_names.get(player_id, "You"),
            "played_cards": self.played_cards.copy(),
            "last_played_card": self.played_cards[-1] if self.played_cards else None,
            "deck_remaining": len(self.deck),
            "playable_cards": get_playable_cards(self.hands.get(player_id, []), self.played_cards),
            "last_action": self.last_action,
            "players_ready": len(self.players)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary (for debugging/admin)."""
        return {
            "room_code": self.room_code,
            "players": self.players,
            "player_names": self.player_names,
            "hands": self.hands,
            "played_cards": self.played_cards,
            "scores": self.scores,
            "current_turn": self.current_turn,
            "deck_size": len(self.deck),
            "game_started": self.game_started,
            "game_over": self.game_over,
            "winner": self.winner,
            "turn_number": self.turn_number
        }


# =============================================================================
# GAME ROOM MANAGEMENT
# =============================================================================

# Game rooms storage (in-memory)
game_rooms: Dict[str, GameState] = {}


def generate_room_code() -> str:
    """Generate a unique 6-character room code."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Removed confusing chars (I,O,0,1)
    while True:
        code = ''.join(random.choices(chars, k=6))
        if code not in game_rooms:
            return code


def create_room(room_code: str = None) -> GameState:
    """Create a new game room. Auto-generates code if not provided."""
    if room_code is None:
        room_code = generate_room_code()
    game_rooms[room_code] = GameState(room_code)
    return game_rooms[room_code]


def get_room(room_code: str) -> Optional[GameState]:
    """Get an existing game room."""
    return game_rooms.get(room_code)


def delete_room(room_code: str) -> bool:
    """Delete a game room. Returns True if successful."""
    if room_code in game_rooms:
        del game_rooms[room_code]
        return True
    return False


def get_all_rooms() -> Dict[str, GameState]:
    """Get all active game rooms."""
    return game_rooms


def cleanup_empty_rooms() -> int:
    """Remove rooms with no players. Returns count of removed rooms."""
    empty_rooms = [code for code, room in game_rooms.items() if not room.players]
    for code in empty_rooms:
        del game_rooms[code]
    return len(empty_rooms)
