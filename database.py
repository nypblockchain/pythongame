"""
Database Operations Module

Provides Firestore operations for the Python Card Game:
- Saving game records
- Retrieving game history
- Leaderboard queries
- Batch statistics updates
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from firebase_admin.firestore import SERVER_TIMESTAMP

from firebase_config import (
    get_firestore_client,
    get_users_collection,
    get_games_collection,
    is_firebase_initialized
)


# =============================================================================
# GAME OPERATIONS
# =============================================================================


def save_game(game_data: Dict[str, Any]) -> Optional[str]:
    """
    Save a completed game record to Firestore.
    
    Args:
        game_data: Dictionary containing game information:
            - room_code (str): The game room code
            - players (list): List of player UIDs (or "AI" for bot)
            - player_names (dict): Map of player_id to display name
            - scores (dict): Map of player_id to final score
            - winner (str): UID of the winning player
            - played_cards (list): List of cards played in order
            - final_code (str): The final Python code built
            - duration (int): Game duration in seconds
            - game_type (str): "pvp" or "ai"
            - ai_difficulty (str, optional): "easy", "medium", or "hard"
            
    Returns:
        str: The game document ID if successful, None otherwise
    """
    games_collection = get_games_collection()
    if not games_collection:
        print("Warning: Cannot save game - Firestore not initialized")
        return None
    
    try:
        # Build the game document
        game_doc = {
            'roomCode': game_data.get('room_code', ''),
            'players': game_data.get('players', []),
            'playerNames': game_data.get('player_names', {}),
            'scores': game_data.get('scores', {}),
            'winner': game_data.get('winner'),
            'winnerName': game_data.get('player_names', {}).get(
                game_data.get('winner'), 'Unknown'
            ),
            'playedCards': game_data.get('played_cards', []),
            'finalCode': game_data.get('final_code', ''),
            'duration': game_data.get('duration', 0),
            'gameType': game_data.get('game_type', 'pvp'),
            'createdAt': SERVER_TIMESTAMP,
            'endedAt': SERVER_TIMESTAMP
        }
        
        # Add AI-specific fields if applicable
        if game_data.get('game_type') == 'ai':
            game_doc['aiDifficulty'] = game_data.get('ai_difficulty', 'medium')
        
        # Calculate additional statistics
        if game_data.get('scores'):
            scores = game_data['scores']
            score_values = list(scores.values())
            game_doc['totalScore'] = sum(score_values)
            game_doc['scoreDifference'] = abs(
                max(score_values) - min(score_values)
            ) if len(score_values) >= 2 else 0
        
        # Save the document
        doc_ref = games_collection.add(game_doc)
        game_id = doc_ref[1].id
        
        print(f"Game saved with ID: {game_id}")
        return game_id
        
    except Exception as e:
        print(f"Error saving game: {e}")
        return None


def get_game(game_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single game record by ID.
    
    Args:
        game_id: The Firestore document ID of the game
        
    Returns:
        dict: Game data with ID, or None if not found
    """
    games_collection = get_games_collection()
    if not games_collection:
        return None
    
    try:
        doc = games_collection.document(game_id).get()
        if doc.exists:
            game_data = doc.to_dict()
            game_data['id'] = doc.id
            # Convert timestamps to ISO strings
            if 'createdAt' in game_data and game_data['createdAt']:
                game_data['createdAt'] = game_data['createdAt'].isoformat()
            if 'endedAt' in game_data and game_data['endedAt']:
                game_data['endedAt'] = game_data['endedAt'].isoformat()
            return game_data
        return None
        
    except Exception as e:
        print(f"Error getting game: {e}")
        return None


def get_user_games(
    uid: str, 
    limit: int = 20,
    game_type: Optional[str] = None,
    include_ai: bool = True
) -> List[Dict[str, Any]]:
    """
    Get a user's game history from Firestore.
    
    Args:
        uid: User's Firebase UID
        limit: Maximum number of games to return (default 20, max 100)
        game_type: Filter by game type ("pvp" or "ai"), None for all
        include_ai: Whether to include AI games (only used if game_type is None)
        
    Returns:
        list: List of game records, ordered by creation date (newest first)
    """
    games_collection = get_games_collection()
    if not games_collection:
        return []
    
    try:
        # Limit to reasonable maximum
        limit = min(limit, 100)
        
        # Build query - filter by user participation
        query = games_collection.where('players', 'array_contains', uid)
        
        # Filter by game type if specified
        if game_type:
            query = query.where('gameType', '==', game_type)
        elif not include_ai:
            query = query.where('gameType', '==', 'pvp')
        
        # Order by creation date and limit
        query = query.order_by('createdAt', direction='DESCENDING').limit(limit)
        
        games = []
        for doc in query.stream():
            game_data = doc.to_dict()
            game_data['id'] = doc.id
            
            # Convert timestamps to ISO strings
            if 'createdAt' in game_data and game_data['createdAt']:
                game_data['createdAt'] = game_data['createdAt'].isoformat()
            if 'endedAt' in game_data and game_data['endedAt']:
                game_data['endedAt'] = game_data['endedAt'].isoformat()
            
            # Add user-specific derived fields
            game_data['userWon'] = game_data.get('winner') == uid
            game_data['userScore'] = game_data.get('scores', {}).get(uid, 0)
            
            games.append(game_data)
        
        return games
        
    except Exception as e:
        print(f"Error getting user games: {e}")
        return []


def get_user_game_stats(uid: str) -> Dict[str, Any]:
    """
    Calculate comprehensive game statistics for a user.
    
    Args:
        uid: User's Firebase UID
        
    Returns:
        dict: Statistics including wins, losses, averages, etc.
    """
    games_collection = get_games_collection()
    if not games_collection:
        return {}
    
    try:
        # Get all games for this user
        query = games_collection.where('players', 'array_contains', uid)
        
        total_games = 0
        wins = 0
        total_score = 0
        highest_score = 0
        total_duration = 0
        pvp_wins = 0
        pvp_games = 0
        ai_wins = 0
        ai_games = 0
        
        for doc in query.stream():
            game_data = doc.to_dict()
            total_games += 1
            
            # Check if user won
            user_won = game_data.get('winner') == uid
            if user_won:
                wins += 1
            
            # Get user's score
            user_score = game_data.get('scores', {}).get(uid, 0)
            total_score += user_score
            highest_score = max(highest_score, user_score)
            
            # Track duration
            total_duration += game_data.get('duration', 0)
            
            # Track by game type
            game_type = game_data.get('gameType', 'pvp')
            if game_type == 'pvp':
                pvp_games += 1
                if user_won:
                    pvp_wins += 1
            else:
                ai_games += 1
                if user_won:
                    ai_wins += 1
        
        # Calculate derived stats
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        avg_score = total_score / total_games if total_games > 0 else 0
        avg_duration = total_duration / total_games if total_games > 0 else 0
        pvp_win_rate = (pvp_wins / pvp_games * 100) if pvp_games > 0 else 0
        ai_win_rate = (ai_wins / ai_games * 100) if ai_games > 0 else 0
        
        return {
            'totalGames': total_games,
            'wins': wins,
            'losses': total_games - wins,
            'winRate': round(win_rate, 1),
            'totalScore': total_score,
            'highestScore': highest_score,
            'averageScore': round(avg_score, 1),
            'totalDuration': total_duration,
            'averageDuration': round(avg_duration, 1),
            'pvp': {
                'games': pvp_games,
                'wins': pvp_wins,
                'winRate': round(pvp_win_rate, 1)
            },
            'ai': {
                'games': ai_games,
                'wins': ai_wins,
                'winRate': round(ai_win_rate, 1)
            }
        }
        
    except Exception as e:
        print(f"Error getting user game stats: {e}")
        return {}


# =============================================================================
# LEADERBOARD OPERATIONS
# =============================================================================


def get_leaderboard(
    limit: int = 50,
    sort_by: str = 'gamesWon',
    game_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get the leaderboard of top players.
    
    Args:
        limit: Maximum number of players to return (default 50, max 100)
        sort_by: Field to sort by - 'gamesWon', 'winRate', 'totalScore', 'highestScore'
        game_type: Filter for specific game type stats (not currently implemented)
        
    Returns:
        list: List of player stats sorted by the specified criteria
    """
    users_collection = get_users_collection()
    if not users_collection:
        return []
    
    try:
        # Limit to reasonable maximum
        limit = min(limit, 100)
        
        # Map sort_by to Firestore field
        sort_field_map = {
            'gamesWon': 'stats.gamesWon',
            'totalScore': 'stats.totalScore',
            'highestScore': 'stats.highestScore',
            'gamesPlayed': 'stats.gamesPlayed'
        }
        
        sort_field = sort_field_map.get(sort_by, 'stats.gamesWon')
        
        # Query users ordered by the specified field
        query = users_collection.order_by(
            sort_field, 
            direction='DESCENDING'
        ).limit(limit)
        
        leaderboard = []
        rank = 1
        
        for doc in query.stream():
            user_data = doc.to_dict()
            stats = user_data.get('stats', {})
            
            # Calculate win rate
            games_played = stats.get('gamesPlayed', 0)
            games_won = stats.get('gamesWon', 0)
            win_rate = (games_won / games_played * 100) if games_played > 0 else 0
            
            leaderboard.append({
                'rank': rank,
                'uid': doc.id,
                'displayName': user_data.get('displayName', 'Unknown'),
                'gamesPlayed': games_played,
                'gamesWon': games_won,
                'winRate': round(win_rate, 1),
                'totalScore': stats.get('totalScore', 0),
                'highestScore': stats.get('highestScore', 0),
                'averageScore': round(
                    stats.get('totalScore', 0) / games_played, 1
                ) if games_played > 0 else 0
            })
            rank += 1
        
        # If sorting by win rate, we need to re-sort in Python
        # (Firestore doesn't support sorting by computed fields)
        if sort_by == 'winRate':
            # Only include players with at least 5 games for win rate ranking
            qualified = [p for p in leaderboard if p['gamesPlayed'] >= 5]
            unqualified = [p for p in leaderboard if p['gamesPlayed'] < 5]
            
            qualified.sort(key=lambda x: x['winRate'], reverse=True)
            
            # Re-rank qualified players
            for i, player in enumerate(qualified, 1):
                player['rank'] = i
            
            leaderboard = qualified[:limit]
        
        return leaderboard
        
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []


def get_recent_games(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get the most recent games across all players.
    
    Args:
        limit: Maximum number of games to return
        
    Returns:
        list: List of recent game records
    """
    games_collection = get_games_collection()
    if not games_collection:
        return []
    
    try:
        limit = min(limit, 50)
        
        query = games_collection.order_by(
            'createdAt', 
            direction='DESCENDING'
        ).limit(limit)
        
        games = []
        for doc in query.stream():
            game_data = doc.to_dict()
            game_data['id'] = doc.id
            
            # Convert timestamps
            if 'createdAt' in game_data and game_data['createdAt']:
                game_data['createdAt'] = game_data['createdAt'].isoformat()
            if 'endedAt' in game_data and game_data['endedAt']:
                game_data['endedAt'] = game_data['endedAt'].isoformat()
            
            games.append(game_data)
        
        return games
        
    except Exception as e:
        print(f"Error getting recent games: {e}")
        return []


# =============================================================================
# USER STATISTICS OPERATIONS
# =============================================================================


def update_user_stats_after_game(
    uid: str, 
    score: int, 
    won: bool
) -> bool:
    """
    Update a user's statistics after completing a game.
    
    Args:
        uid: User's Firebase UID
        score: Points scored in the game
        won: Whether the user won the game
        
    Returns:
        bool: True if successful, False otherwise
    """
    users_collection = get_users_collection()
    if not users_collection:
        return False
    
    try:
        # Get current stats
        doc = users_collection.document(uid).get()
        if not doc.exists:
            print(f"User {uid} not found in Firestore")
            return False
        
        current_stats = doc.to_dict().get('stats', {
            'gamesPlayed': 0,
            'gamesWon': 0,
            'totalScore': 0,
            'highestScore': 0
        })
        
        # Calculate new stats
        new_stats = {
            'gamesPlayed': current_stats.get('gamesPlayed', 0) + 1,
            'gamesWon': current_stats.get('gamesWon', 0) + (1 if won else 0),
            'totalScore': current_stats.get('totalScore', 0) + score,
            'highestScore': max(
                current_stats.get('highestScore', 0),
                score
            )
        }
        
        # Update the user document
        users_collection.document(uid).update({'stats': new_stats})
        return True
        
    except Exception as e:
        print(f"Error updating user stats: {e}")
        return False


def update_multiple_users_stats(game_results: List[Dict[str, Any]]) -> bool:
    """
    Update statistics for multiple users after a game (batch operation).
    
    Args:
        game_results: List of dicts with 'uid', 'score', and 'won' keys
        
    Returns:
        bool: True if all updates successful, False otherwise
    """
    if not is_firebase_initialized():
        return False
    
    try:
        db = get_firestore_client()
        if not db:
            return False
        
        # Use a batch write for efficiency
        batch = db.batch()
        users_ref = db.collection('users')
        
        for result in game_results:
            uid = result.get('uid')
            if not uid or uid.startswith('bot_'):  # Skip bot players
                continue
            
            score = result.get('score', 0)
            won = result.get('won', False)
            
            # Get current stats
            doc = users_ref.document(uid).get()
            if not doc.exists:
                continue
            
            current_stats = doc.to_dict().get('stats', {
                'gamesPlayed': 0,
                'gamesWon': 0,
                'totalScore': 0,
                'highestScore': 0
            })
            
            # Calculate new stats
            new_stats = {
                'gamesPlayed': current_stats.get('gamesPlayed', 0) + 1,
                'gamesWon': current_stats.get('gamesWon', 0) + (1 if won else 0),
                'totalScore': current_stats.get('totalScore', 0) + score,
                'highestScore': max(
                    current_stats.get('highestScore', 0),
                    score
                )
            }
            
            # Add to batch
            batch.update(users_ref.document(uid), {'stats': new_stats})
        
        # Commit all updates
        batch.commit()
        return True
        
    except Exception as e:
        print(f"Error updating multiple user stats: {e}")
        return False


# =============================================================================
# GAME COMPLETION HANDLER
# =============================================================================


def save_game_and_update_stats(
    room_code: str,
    players: List[str],
    player_names: Dict[str, str],
    scores: Dict[str, int],
    winner: str,
    played_cards: List[str],
    final_code: str,
    duration: int,
    game_type: str = 'pvp',
    ai_difficulty: Optional[str] = None
) -> Optional[str]:
    """
    Complete game handler: saves the game record and updates all player stats.
    
    This is the main function to call when a game ends. It handles:
    1. Saving the game record to the games collection
    2. Updating stats for all human players
    
    Args:
        room_code: The game room code
        players: List of player IDs
        player_names: Map of player ID to display name
        scores: Map of player ID to final score
        winner: ID of the winning player
        played_cards: List of cards played during the game
        final_code: The final Python code string
        duration: Game duration in seconds
        game_type: "pvp" or "ai"
        ai_difficulty: AI difficulty level (only for AI games)
        
    Returns:
        str: The saved game document ID, or None on failure
    """
    if not is_firebase_initialized():
        print("Firebase not initialized - game will not be saved")
        return None
    
    # Save the game record
    game_id = save_game({
        'room_code': room_code,
        'players': players,
        'player_names': player_names,
        'scores': scores,
        'winner': winner,
        'played_cards': played_cards,
        'final_code': final_code,
        'duration': duration,
        'game_type': game_type,
        'ai_difficulty': ai_difficulty
    })
    
    if not game_id:
        print("Failed to save game record")
        return None
    
    # Update stats for each human player
    game_results = []
    for player_id in players:
        # Skip bot players
        if player_id.startswith('bot_'):
            continue
        
        game_results.append({
            'uid': player_id,
            'score': scores.get(player_id, 0),
            'won': player_id == winner
        })
    
    if game_results:
        update_multiple_users_stats(game_results)
    
    return game_id


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_global_stats() -> Dict[str, Any]:
    """
    Get global game statistics across all players.
    
    Returns:
        dict: Global statistics including total games, total players, etc.
    """
    db = get_firestore_client()
    if not db:
        return {}
    
    try:
        # Count total games
        games_ref = db.collection('games')
        total_games = 0
        total_pvp = 0
        total_ai = 0
        
        for doc in games_ref.stream():
            total_games += 1
            game_type = doc.to_dict().get('gameType', 'pvp')
            if game_type == 'ai':
                total_ai += 1
            else:
                total_pvp += 1
        
        # Count total users
        users_ref = db.collection('users')
        total_users = sum(1 for _ in users_ref.stream())
        
        return {
            'totalGames': total_games,
            'totalPvPGames': total_pvp,
            'totalAIGames': total_ai,
            'totalUsers': total_users
        }
        
    except Exception as e:
        print(f"Error getting global stats: {e}")
        return {}


def delete_game(game_id: str) -> bool:
    """
    Delete a game record (admin function).
    
    Args:
        game_id: The Firestore document ID of the game
        
    Returns:
        bool: True if successful, False otherwise
    """
    games_collection = get_games_collection()
    if not games_collection:
        return False
    
    try:
        games_collection.document(game_id).delete()
        return True
    except Exception as e:
        print(f"Error deleting game: {e}")
        return False
