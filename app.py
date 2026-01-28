"""
Python Syntax Card Game - Main Flask Application
A browser-based 1v1 card game where players compete by playing Python syntax cards.
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

import threading
import time

from game_logic import (
    create_room, get_room, delete_room, get_all_rooms, generate_room_code,
    get_card_info, CARDS, build_python_code, validate_python_syntax,
    get_syntax_validation_info, can_play_card_with_reason,
    can_insert_card_at_position, get_playable_cards_at_position,
    get_playable_cards, BotPlayer
)
from firebase_config import initialize_firebase, is_firebase_initialized
from auth import (
    require_auth, optional_auth, create_user, get_user_profile,
    update_user_profile, get_user_game_history, get_leaderboard
)
from database import (
    save_game_and_update_stats, get_user_games, get_user_game_stats,
    get_leaderboard as get_db_leaderboard, get_recent_games, get_global_stats
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'python-card-game-secret-key')

# Initialize Firebase
firebase_initialized = initialize_firebase()
if firebase_initialized:
    print("Firebase authentication enabled")
else:
    print("Warning: Firebase not initialized - auth features disabled")

# Initialize Socket.IO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Track which player is in which room (socket_id: room_code)
player_rooms = {}

# Track AI games (room_code: BotPlayer instance)
ai_games = {}

# Map socket ID to Firebase UID (socket_id: firebase_uid)
socket_to_uid = {}

# =============================================================================
# IN-MEMORY STATS STORAGE (since Firestore is disabled)
# =============================================================================

# Store user stats in memory (uid -> stats dict)
memory_user_stats = {}

# Store game history in memory (list of game records)
memory_game_history = []

def get_or_create_user_stats(uid, display_name=None):
    """Get user stats from memory, creating if needed."""
    if uid not in memory_user_stats:
        memory_user_stats[uid] = {
            'uid': uid,
            'displayName': display_name or 'Player',
            'gamesPlayed': 0,
            'gamesWon': 0,
            'totalScore': 0,
            'highestScore': 0
        }
    elif display_name and memory_user_stats[uid]['displayName'] == 'Player':
        memory_user_stats[uid]['displayName'] = display_name
    return memory_user_stats[uid]

def update_memory_stats(uid, display_name, score, won):
    """Update user stats in memory after a game."""
    stats = get_or_create_user_stats(uid, display_name)
    stats['gamesPlayed'] += 1
    if won:
        stats['gamesWon'] += 1
    stats['totalScore'] += score
    stats['highestScore'] = max(stats['highestScore'], score)
    return stats

def add_game_to_history(game_record):
    """Add a game to the in-memory history."""
    memory_game_history.insert(0, game_record)  # Add to front
    # Keep only last 100 games
    if len(memory_game_history) > 100:
        memory_game_history.pop()

def get_memory_leaderboard(limit=50):
    """Get leaderboard from memory stats."""
    if not memory_user_stats:
        return []
    
    # Sort by games won, then by win rate
    sorted_users = sorted(
        memory_user_stats.values(),
        key=lambda x: (x['gamesWon'], x['gamesPlayed']),
        reverse=True
    )[:limit]
    
    leaderboard = []
    for rank, user in enumerate(sorted_users, 1):
        games_played = user['gamesPlayed']
        games_won = user['gamesWon']
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        
        leaderboard.append({
            'rank': rank,
            'uid': user['uid'],
            'displayName': user['displayName'],
            'gamesPlayed': games_played,
            'gamesWon': games_won,
            'winRate': round(win_rate, 1),
            'totalScore': user['totalScore'],
            'highestScore': user['highestScore']
        })
    
    return leaderboard

def get_user_game_history_memory(uid, limit=20):
    """Get game history for a user from memory."""
    user_games = [g for g in memory_game_history if uid in g.get('players', [])]
    return user_games[:limit]

# =============================================================================
# HTTP ROUTES
# =============================================================================


@app.route('/health')
def health():
    """Health check endpoint for keep-alive pings."""
    return 'OK', 200


@app.route('/')
def index():
    """Home page - game lobby."""
    return render_template('index.html')


@app.route('/game/<room_code>')
def game(room_code):
    """Game board page."""
    return render_template('game.html', room_code=room_code)


@app.route('/profile')
def profile():
    """User profile page."""
    return render_template('profile.html')


@app.route('/leaderboard')
def leaderboard_page():
    """Leaderboard page with rankings."""
    return render_template('leaderboard.html')


@app.route('/api/cards')
def get_cards():
    """API endpoint to get all card definitions."""
    return CARDS


@app.route('/api/rooms')
def get_rooms_list():
    """API endpoint to get list of open rooms (rooms waiting for players)."""
    return {'rooms': get_open_rooms_list()}


@app.route('/api/ai-difficulties')
def get_ai_difficulties():
    """API endpoint to get available AI difficulty levels."""
    return {
        'difficulties': [
            {
                'id': 'easy',
                'name': 'Easy',
                'description': 'Random valid card selection. Great for learning!',
                'think_time': '1-2 seconds'
            },
            {
                'id': 'medium',
                'name': 'Medium',
                'description': 'Prioritizes high-point cards. A fair challenge.',
                'think_time': '1.5-2.5 seconds'
            },
            {
                'id': 'hard',
                'name': 'Hard',
                'description': 'Strategic play with combos and blocking. Beware!',
                'think_time': '2-3 seconds'
            }
        ]
    }


@app.route('/api/validate-syntax', methods=['POST'])
def validate_syntax():
    """
    API endpoint to validate Python syntax from card sequence.
    
    Request body:
    {
        "cards": ["for", "i", "in", "range", "(", "10", ")"]
    }
    
    Response:
    {
        "code": "for i in range(10)",
        "is_valid": true,
        "is_complete": false,
        "error": "",
        "suggestions": ["SYNTAX_COLON"]
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Request body required'
        }), 400
    
    cards = data.get('cards', [])
    
    if not isinstance(cards, list):
        return jsonify({
            'success': False,
            'error': 'Cards must be a list'
        }), 400
    
    # Get syntax validation info
    validation_info = get_syntax_validation_info(cards)
    
    return jsonify({
        'success': True,
        **validation_info
    })


@app.route('/api/check-card', methods=['POST'])
def check_card():
    """
    API endpoint to check if a card can be played.
    
    Request body:
    {
        "card": "range",
        "played_cards": ["for", "i", "in"],
        "last_was_wild": false,
        "open_paren_count": 0
    }
    
    Response:
    {
        "can_play": true,
        "reason": "Valid after 'in'"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Request body required'
        }), 400
    
    card = data.get('card', '')
    played_cards = data.get('played_cards', [])
    last_was_wild = data.get('last_was_wild', False)
    open_paren_count = data.get('open_paren_count', 0)
    
    if not card:
        return jsonify({
            'success': False,
            'error': 'Card name required'
        }), 400
    
    # Check if card can be played with reason
    can_play, reason = can_play_card_with_reason(
        card, played_cards, last_was_wild, open_paren_count
    )
    
    return jsonify({
        'success': True,
        'can_play': can_play,
        'reason': reason
    })


@app.route('/api/check-insertion', methods=['POST'])
def check_insertion():
    """
    API endpoint to check if a card can be inserted at a specific position.
    
    Request body:
    {
        "card": "print",
        "played_cards": ["for", "i", "in", "range", "(", "10", ")", ":"],
        "position": 8,
        "last_was_wild": false
    }
    
    Response:
    {
        "can_insert": true,
        "reason": "Valid insertion at position 8"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Request body required'
        }), 400
    
    card = data.get('card', '')
    played_cards = data.get('played_cards', [])
    position = data.get('position', len(played_cards))
    last_was_wild = data.get('last_was_wild', False)
    
    if not card:
        return jsonify({
            'success': False,
            'error': 'Card name required'
        }), 400
    
    can_insert, reason = can_insert_card_at_position(
        card, played_cards, position, last_was_wild
    )
    
    return jsonify({
        'success': True,
        'can_insert': can_insert,
        'reason': reason
    })


@app.route('/api/playable-at-position', methods=['POST'])
def playable_at_position():
    """
    API endpoint to get all playable cards at a specific position.
    
    Request body:
    {
        "hand": ["print", "x", "=", "10"],
        "played_cards": ["for", "i", "in", "range", "(", "10", ")", ":"],
        "position": 8,
        "last_was_wild": false
    }
    
    Response:
    {
        "playable_cards": ["print", "x"]
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Request body required'
        }), 400
    
    hand = data.get('hand', [])
    played_cards = data.get('played_cards', [])
    position = data.get('position', len(played_cards))
    last_was_wild = data.get('last_was_wild', False)
    
    playable = get_playable_cards_at_position(hand, played_cards, position, last_was_wild)
    
    return jsonify({
        'success': True,
        'playable_cards': playable
    })


# =============================================================================
# AUTHENTICATION API ENDPOINTS
# =============================================================================


@app.route('/api/auth/status')
def auth_status():
    """Check if authentication is available."""
    return jsonify({
        'available': is_firebase_initialized(),
        'message': 'Authentication available' if is_firebase_initialized() else 'Authentication not configured'
    })


@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "displayName": "PlayerName"  (optional)
    }
    """
    if not is_firebase_initialized():
        return jsonify({
            'success': False,
            'error': 'Authentication service not available'
        }), 503
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Request body required'
        }), 400
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    display_name = data.get('displayName', '').strip()
    
    # Validate email
    if not email or '@' not in email:
        return jsonify({
            'success': False,
            'error': 'Valid email required'
        }), 400
    
    # Validate password
    if len(password) < 6:
        return jsonify({
            'success': False,
            'error': 'Password must be at least 6 characters'
        }), 400
    
    # Validate display name if provided
    if display_name and len(display_name) > 30:
        return jsonify({
            'success': False,
            'error': 'Display name must be 30 characters or less'
        }), 400
    
    # Create the user
    result = create_user(email, password, display_name or None)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@app.route('/api/auth/verify', methods=['POST'])
@require_auth
def verify_token():
    """
    Verify a Firebase ID token and return user info.
    
    Requires Authorization header with Bearer token.
    Returns immediately with user info from token - NO Firestore calls.
    """
    user = request.current_user
    uid = user.get('uid')
    
    # Return IMMEDIATELY with info from the token itself
    # No Firestore calls - profile can be fetched separately if needed
    display_name = user.get('name', user.get('email', '').split('@')[0] if user.get('email') else 'Player')
    
    return jsonify({
        'success': True,
        'user': {
            'uid': uid,
            'email': user.get('email'),
            'displayName': display_name,
            'stats': None  # Stats fetched separately via /api/user/profile
        }
    })


@app.route('/api/user/profile')
@require_auth
def get_profile():
    """
    Get the current user's profile.
    
    Requires Authorization header with Bearer token.
    """
    uid = request.current_user.get('uid')
    email = request.current_user.get('email', '')
    name = request.current_user.get('name', email.split('@')[0] if email else 'Player')
    
    # Get stats from in-memory storage
    stats = get_or_create_user_stats(uid, name)
    print(f"[API] GET /api/user/profile - {name}: {stats['gamesPlayed']} games, {stats['gamesWon']} wins")
    
    return jsonify({
        'success': True,
        'profile': {
            'uid': uid,
            'displayName': name,
            'email': email,
            'stats': {
                'gamesPlayed': stats['gamesPlayed'],
                'gamesWon': stats['gamesWon'],
                'totalScore': stats['totalScore'],
                'highestScore': stats['highestScore']
            }
        }
    })


@app.route('/api/user/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update the current user's profile.
    
    Request body:
    {
        "displayName": "NewName"
    }
    """
    uid = request.current_user.get('uid')
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Request body required'
        }), 400
    
    # Only allow updating certain fields
    allowed_fields = ['displayName']
    updates = {}
    
    for field in allowed_fields:
        if field in data:
            value = data[field]
            if field == 'displayName':
                if not value or len(value) > 30:
                    return jsonify({
                        'success': False,
                        'error': 'Display name must be 1-30 characters'
                    }), 400
            updates[field] = value
    
    if not updates:
        return jsonify({
            'success': False,
            'error': 'No valid fields to update'
        }), 400
    
    if update_user_profile(uid, updates):
        return jsonify({
            'success': True,
            'message': 'Profile updated'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to update profile'
        }), 500


@app.route('/api/user/history')
@require_auth
def get_history():
    """
    Get the current user's game history.
    
    Query parameters:
    - limit: Maximum number of games to return (default: 20, max: 50)
    """
    uid = request.current_user.get('uid')
    limit = min(int(request.args.get('limit', 20)), 50)
    
    history = get_user_game_history(uid, limit)
    
    return jsonify({
        'success': True,
        'history': history,
        'count': len(history)
    })


@app.route('/api/leaderboard')
@optional_auth
def leaderboard():
    """
    Get the leaderboard of top players.
    
    Query parameters:
    - limit: Maximum number of players to return (default: 50, max: 100)
    """
    limit = min(int(request.args.get('limit', 50)), 100)
    
    # Get leaderboard from in-memory storage
    leaders = get_memory_leaderboard(limit)
    
    current_uid = None
    if hasattr(request, 'current_user') and request.current_user:
        current_uid = request.current_user.get('uid')
    
    print(f"[API] GET /api/leaderboard - returning {len(leaders)} players")
    
    return jsonify({
        'success': True,
        'leaderboard': leaders,
        'count': len(leaders),
        'currentUserUid': current_uid
    })


@app.route('/api/user/stats')
@require_auth
def get_user_stats():
    """
    Get detailed game statistics for the current user.
    
    Returns comprehensive stats including:
    - Total games, wins, losses
    - Win rate, average score, highest score
    - PvP vs AI game breakdowns
    """
    uid = request.current_user.get('uid')
    email = request.current_user.get('email', '')
    name = request.current_user.get('name', email.split('@')[0] if email else 'Player')
    
    # Get stats from in-memory storage
    stats = get_or_create_user_stats(uid, name)
    games_played = stats['gamesPlayed']
    games_won = stats['gamesWon']
    games_lost = games_played - games_won
    win_rate = (games_won / games_played * 100) if games_played > 0 else 0
    avg_score = (stats['totalScore'] / games_played) if games_played > 0 else 0
    
    print(f"[API] GET /api/user/stats - {name}: {games_played} games, {games_won} wins")
    
    # Return with both naming conventions for compatibility
    return jsonify({
        'success': True,
        'stats': {
            # Standard names (used by profile page)
            'gamesPlayed': games_played,
            'gamesWon': games_won,
            'totalScore': stats['totalScore'],
            'highestScore': stats['highestScore'],
            # Alternative names for backwards compatibility
            'totalGames': games_played,
            'wins': games_won,
            'losses': games_lost,
            'winRate': round(win_rate, 1),
            'averageScore': round(avg_score, 1)
        }
    })


@app.route('/api/user/games')
@require_auth
def get_user_games_list():
    """
    Get the current user's game history with filtering options.
    
    Query parameters:
    - limit: Maximum number of games (default 20, max 100)
    - type: Filter by game type ('pvp', 'ai', or omit for all)
    """
    uid = request.current_user.get('uid')
    limit = min(int(request.args.get('limit', 20)), 100)
    game_type = request.args.get('type')
    
    # Get games from in-memory storage
    games = get_user_game_history_memory(uid, limit)
    
    # Filter by game type if specified
    if game_type and game_type in ['pvp', 'ai']:
        games = [g for g in games if g.get('gameType') == game_type]
    
    print(f"[API] GET /api/user/games - returning {len(games)} games for {uid}")
    
    return jsonify({
        'success': True,
        'games': games,
        'count': len(games)
    })


@app.route('/api/games/recent')
@optional_auth
def recent_games():
    """
    Get the most recent games across all players.
    
    Query parameters:
    - limit: Maximum number of games (default 20, max 50)
    """
    limit = min(int(request.args.get('limit', 20)), 50)
    
    # Get from in-memory storage
    games = memory_game_history[:limit]
    
    print(f"[API] GET /api/games/recent - returning {len(games)} games")
    
    return jsonify({
        'success': True,
        'games': games,
        'count': len(games)
    })


@app.route('/api/stats/global')
@optional_auth
def global_stats():
    """
    Get global game statistics.
    
    Returns:
    - Total games played
    - Total PvP games
    - Total AI games
    - Total registered users
    """
    # Calculate from in-memory storage
    total_games = len(memory_game_history)
    total_pvp = sum(1 for g in memory_game_history if g.get('gameType') == 'pvp')
    total_ai = sum(1 for g in memory_game_history if g.get('gameType') == 'ai')
    total_users = len(memory_user_stats)
    
    print(f"[API] GET /api/stats/global - {total_games} games, {total_users} users")
    
    return jsonify({
        'success': True,
        'stats': {
            'totalGames': total_games,
            'totalPvPGames': total_pvp,
            'totalAIGames': total_ai,
            'totalUsers': total_users
        }
    })


@app.route('/api/leaderboard/advanced')
@optional_auth
def advanced_leaderboard():
    """
    Get the leaderboard with advanced sorting options.
    
    Query parameters:
    - limit: Maximum number of players (default 50, max 100)
    - sort_by: Field to sort by - 'gamesWon', 'winRate', 'totalScore', 'highestScore'
    """
    limit = min(int(request.args.get('limit', 50)), 100)
    sort_by = request.args.get('sort_by', 'gamesWon')
    
    # Validate sort_by
    valid_sorts = ['gamesWon', 'winRate', 'totalScore', 'highestScore', 'gamesPlayed']
    if sort_by not in valid_sorts:
        sort_by = 'gamesWon'
    
    # Get leaderboard from in-memory storage
    if not memory_user_stats:
        leaders = []
    else:
        # Sort based on requested field
        sort_key = {
            'gamesWon': lambda x: x['gamesWon'],
            'winRate': lambda x: (x['gamesWon'] / x['gamesPlayed'] * 100) if x['gamesPlayed'] > 0 else 0,
            'totalScore': lambda x: x['totalScore'],
            'highestScore': lambda x: x['highestScore'],
            'gamesPlayed': lambda x: x['gamesPlayed']
        }.get(sort_by, lambda x: x['gamesWon'])
        
        sorted_users = sorted(memory_user_stats.values(), key=sort_key, reverse=True)[:limit]
        
        leaders = []
        for rank, user in enumerate(sorted_users, 1):
            games_played = user['gamesPlayed']
            games_won = user['gamesWon']
            win_rate = (games_won / games_played * 100) if games_played > 0 else 0
            
            leaders.append({
                'rank': rank,
                'uid': user['uid'],
                'displayName': user['displayName'],
                'gamesPlayed': games_played,
                'gamesWon': games_won,
                'winRate': round(win_rate, 1),
                'totalScore': user['totalScore'],
                'highestScore': user['highestScore']
            })
    
    current_uid = None
    if hasattr(request, 'current_user') and request.current_user:
        current_uid = request.current_user.get('uid')
    
    print(f"[API] GET /api/leaderboard/advanced - returning {len(leaders)} players, sorted by {sort_by}")
    
    return jsonify({
        'success': True,
        'leaderboard': leaders,
        'count': len(leaders),
        'sortedBy': sort_by,
        'currentUserUid': current_uid
    })


# =============================================================================
# GAME SAVE HELPER FUNCTIONS
# =============================================================================


# Track game start times for duration calculation
game_start_times = {}


def record_game_start(room_code: str):
    """Record when a game starts for duration tracking."""
    import time
    game_start_times[room_code] = time.time()


def save_completed_game(room, game_type: str = 'pvp', ai_difficulty: str = None):
    """
    Save a completed game to in-memory storage and update player stats.
    
    Args:
        room: The GameState/room object
        game_type: 'pvp' or 'ai'
        ai_difficulty: AI difficulty level (only for AI games)
    """
    import time as time_module
    
    # Calculate game duration
    start_time = game_start_times.pop(room.room_code, None)
    duration = int(time_module.time() - start_time) if start_time else 0
    
    # Map socket IDs to Firebase UIDs for stats storage
    player_uids = {}
    uid_to_name = {}
    uid_scores = {}
    winner_uid = None
    
    # Update stats for each player
    for socket_id in room.players:
        player_name = room.player_names.get(socket_id, 'Player')
        player_score = room.scores.get(socket_id, 0)
        player_won = (room.winner == socket_id)
        
        # Skip bot players for stats
        if socket_id.startswith('bot_'):
            player_uids[socket_id] = socket_id  # Bots keep their ID
            uid_to_name[socket_id] = player_name
            uid_scores[socket_id] = player_score
            continue
        
        # Get Firebase UID if available, otherwise use socket ID
        firebase_uid = socket_to_uid.get(socket_id, socket_id)
        player_uids[socket_id] = firebase_uid
        uid_to_name[firebase_uid] = player_name
        uid_scores[firebase_uid] = player_score
        
        if player_won:
            winner_uid = firebase_uid
        
        update_memory_stats(firebase_uid, player_name, player_score, player_won)
        print(f"[MEMORY] Updated stats for {player_name} (uid={firebase_uid}): score={player_score}, won={player_won}")
    
    # Create game record with Firebase UIDs
    game_record = {
        'id': f"game_{room.room_code}_{int(time_module.time())}",
        'roomCode': room.room_code,
        'players': list(player_uids.values()),  # Use Firebase UIDs
        'playerNames': uid_to_name,  # Map UID to name
        'scores': uid_scores,  # Map UID to score
        'winner': winner_uid or room.winner,  # Use Firebase UID for winner
        'gameType': game_type,
        'aiDifficulty': ai_difficulty,
        'duration': duration,
        'createdAt': time_module.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    add_game_to_history(game_record)
    print(f"[MEMORY] Game {room.room_code} saved to memory")


# =============================================================================
# LOBBY HELPER FUNCTIONS
# =============================================================================


def get_open_rooms_list():
    """Get a list of rooms that are waiting for players (not full, not started)."""
    open_rooms = []
    for room_code, room in get_all_rooms().items():
        # Only include rooms that have 1 player waiting (not full, game not started)
        if len(room.players) == 1 and not room.game_started:
            # Get the host (first player)
            host_id = room.players[0]
            host_name = room.player_names.get(host_id, 'Unknown')
            open_rooms.append({
                'room_code': room_code,
                'host_name': host_name,
                'players_count': len(room.players),
                'max_players': 2
            })
    return open_rooms


def broadcast_room_list_update():
    """Broadcast updated room list to all connected clients in the lobby."""
    room_list = get_open_rooms_list()
    socketio.emit('room_list_update', {'rooms': room_list})


# =============================================================================
# SOCKET.IO EVENT HANDLERS
# =============================================================================


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f'Client connected: {request.sid}')


@socketio.on('get_open_rooms')
def handle_get_open_rooms():
    """Return list of open rooms waiting for players."""
    emit('room_list_update', {'rooms': get_open_rooms_list()})


@socketio.on('quick_match')
def handle_quick_match(data):
    """Quick match - auto-join first available room or create new one."""
    player_id = request.sid
    player_name = data.get('name', 'Player')
    firebase_uid = data.get('uid')  # Firebase UID from client
    
    # Store Firebase UID mapping if provided
    if firebase_uid:
        socket_to_uid[player_id] = firebase_uid
        print(f'[MATCH] Stored UID mapping: {player_id} -> {firebase_uid}')
    
    # Check if player is already in a room
    if player_id in player_rooms:
        emit('error', {'message': 'Already in a room'})
        return
    
    # Find an open room (1 player waiting, game not started)
    open_room = None
    for room_code, room in get_all_rooms().items():
        if len(room.players) == 1 and not room.game_started:
            open_room = room
            break
    
    if open_room:
        # Join the existing open room
        room_code = open_room.room_code
        print(f'Quick match: Player {player_id} joining existing room {room_code}')
    else:
        # Create a new room
        room_code = generate_room_code()
        open_room = create_room(room_code)
        print(f'Quick match: Player {player_id} creating new room {room_code}')
        # Broadcast that a new room is available
        broadcast_room_list_update()
    
    # Add the player to the room
    if not open_room.add_player(player_id, player_name):
        emit('error', {'message': 'Failed to join room'})
        return
    
    # Join the Socket.IO room for broadcasting
    join_room(room_code)
    player_rooms[player_id] = room_code
    
    print(f'Quick match: Player {player_id} in room {room_code} ({len(open_room.players)}/2 players)')
    
    # Notify the player they joined successfully
    emit('room_joined', {
        'room_code': room_code,
        'player_id': player_id,
        'players_count': len(open_room.players),
        'waiting_for_opponent': len(open_room.players) < 2
    })
    
    # Notify other players in the room
    emit('player_joined', {
        'player_id': player_id,
        'player_name': open_room.player_names.get(player_id, player_name),
        'players_count': len(open_room.players)
    }, room=room_code, include_self=False)
    
    # If room is now full, start the game and broadcast room list update
    if open_room.is_ready():
        broadcast_room_list_update()  # Room is no longer open
        start_game_for_room(room_code)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    player_id = request.sid
    print(f'Client disconnected: {player_id}')
    
    # Remove player from their room if they were in one
    if player_id in player_rooms:
        room_code = player_rooms[player_id]
        room = get_room(room_code)
        
        if room:
            # Check if this is an AI game
            is_ai_game = room_code in ai_games
            
            # Get opponent before removing player
            opponent_id = room.get_opponent(player_id)
            
            # Remove the player from the game
            room.remove_player(player_id)
            
            # For AI games, just clean up - no need to notify anyone
            if is_ai_game:
                # Clean up AI game tracking
                if room_code in ai_games:
                    del ai_games[room_code]
                delete_room(room_code)
            else:
                # Notify opponent that the player left
                if opponent_id:
                    emit('player_left', {
                        'message': 'Your opponent has disconnected',
                        'player_id': player_id
                    }, room=opponent_id)
                    
                    # If game was in progress, opponent wins by default
                    if room.game_started and not room.game_over:
                        room.game_over = True
                        room.winner = opponent_id
                        emit('game_over', {
                            'winner': opponent_id,
                            'reason': 'opponent_disconnected',
                            'message': 'You win! Opponent disconnected.'
                        }, room=opponent_id)
                
                # Clean up empty rooms
                if not room.players:
                    delete_room(room_code)
                
                # Broadcast room list update (room deleted or became open again)
                broadcast_room_list_update()
        
        del player_rooms[player_id]


@socketio.on('join_room')
def handle_join_room(data):
    """Handle player joining a room."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    player_name = data.get('name', f'Player')
    firebase_uid = data.get('uid')  # Firebase UID from client
    
    # Store Firebase UID mapping if provided
    if firebase_uid:
        socket_to_uid[player_id] = firebase_uid
        print(f'[JOIN] Stored UID mapping: {player_id} -> {firebase_uid}')
    
    if not room_code:
        emit('error', {'message': 'Room code is required'})
        return
    
    # Get or create the room
    room = get_room(room_code)
    is_new_room = False
    if not room:
        room = create_room(room_code)
        is_new_room = True
        print(f'Created new room: {room_code}')
    
    # Try to add the player
    if not room.add_player(player_id, player_name):
        emit('error', {'message': 'Room is full (2 players max)'})
        return
    
    # Join the Socket.IO room for broadcasting
    join_room(room_code)
    player_rooms[player_id] = room_code
    
    print(f'Player {player_id} joined room {room_code} ({len(room.players)}/2 players)')
    
    # Broadcast room list update (new room created or room now full)
    broadcast_room_list_update()
    
    # Notify the player they joined successfully
    emit('room_joined', {
        'room_code': room_code,
        'player_id': player_id,
        'players_count': len(room.players),
        'waiting_for_opponent': len(room.players) < 2
    })
    
    # Notify other players in the room
    emit('player_joined', {
        'player_id': player_id,
        'player_name': room.player_names.get(player_id, player_name),
        'players_count': len(room.players)
    }, room=room_code, include_self=False)
    
    # If room is now full, automatically start the game
    if room.is_ready():
        start_game_for_room(room_code)


@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle player leaving a room."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    
    room = get_room(room_code)
    if not room:
        return
    
    # Leave the Socket.IO room
    leave_room(room_code)
    
    # Remove player from game state
    opponent_id = room.get_opponent(player_id)
    room.remove_player(player_id)
    
    if player_id in player_rooms:
        del player_rooms[player_id]
    
    # Notify opponent
    if opponent_id:
        emit('player_left', {
            'message': 'Your opponent has left the game',
            'player_id': player_id
        }, room=opponent_id)
    
    # Clean up empty rooms
    if not room.players:
        delete_room(room_code)
    
    # Broadcast room list update (room deleted or became open again)
    broadcast_room_list_update()


@socketio.on('play_card')
def handle_play_card(data):
    """Handle a player playing a card."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    card_name = data.get('card', '')
    position = data.get('position')  # Optional insertion position
    
    room = get_room(room_code)
    if not room:
        emit('error', {'message': 'Room not found'})
        return
    
    # Attempt to play the card at the specified position
    result = room.play_card(player_id, card_name, position=position)
    
    if not result['success']:
        emit('error', {'message': result['message']})
        return
    
    # Get card info for the played card
    card_info = get_card_info(card_name)
    
    # Check if this is an AI game
    is_ai_game = room_code in ai_games
    
    # Broadcast the card played event to all players in the room
    emit('card_played', {
        'player_id': player_id,
        'player_name': room.player_names.get(player_id, 'Unknown'),
        'card': card_name,
        'card_info': card_info,
        'points_earned': result['points_earned'],
        'effect': result['effect'],
        'message': result['message']
    }, room=room_code)
    
    # Send updated game state to each player
    if is_ai_game:
        send_game_state_to_all_with_ai_flag(room)
    else:
        send_game_state_to_all(room)
    
    # Check if game is over
    if room.game_over:
        # Save the completed game to database
        if is_ai_game:
            bot = ai_games.get(room_code)
            save_completed_game(room, 'ai', bot.difficulty if bot else None)
        else:
            save_completed_game(room, 'pvp')
        
        emit('game_over', {
            'winner': room.winner,
            'winner_name': room.player_names.get(room.winner, 'Unknown'),
            'scores': room.scores,
            'reason': 'win_condition',
            'is_ai_game': is_ai_game
        }, room=room_code)
    elif is_ai_game:
        # Trigger bot turn if it's an AI game and it's the bot's turn
        bot = ai_games.get(room_code)
        if bot and room.get_current_player() == bot.player_id:
            trigger_bot_turn(room_code)


@socketio.on('pass_turn')
def handle_pass_turn(data):
    """Handle a player passing their turn."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    
    room = get_room(room_code)
    if not room:
        emit('error', {'message': 'Room not found'})
        return
    
    # Attempt to pass
    result = room.pass_turn(player_id)
    
    if not result['success']:
        emit('error', {'message': result['message']})
        return
    
    # Check if this is an AI game
    is_ai_game = room_code in ai_games
    
    # Broadcast the pass event to all players in the room
    emit('turn_passed', {
        'player_id': player_id,
        'player_name': room.player_names.get(player_id, 'Unknown'),
        'drew_card': result.get('drew_card'),
        'message': result['message']
    }, room=room_code)
    
    # Send updated game state to each player
    if is_ai_game:
        send_game_state_to_all_with_ai_flag(room)
    else:
        send_game_state_to_all(room)
    
    # Check if game is over
    if room.game_over:
        # Save the completed game to database
        if is_ai_game:
            bot = ai_games.get(room_code)
            save_completed_game(room, 'ai', bot.difficulty if bot else None)
        else:
            save_completed_game(room, 'pvp')
        
        emit('game_over', {
            'winner': room.winner,
            'winner_name': room.player_names.get(room.winner, 'Unknown'),
            'scores': room.scores,
            'reason': 'too_many_passes',
            'is_ai_game': is_ai_game
        }, room=room_code)
    elif is_ai_game:
        # Trigger bot turn if it's an AI game and it's the bot's turn
        bot = ai_games.get(room_code)
        if bot and room.get_current_player() == bot.player_id:
            trigger_bot_turn(room_code)


@socketio.on('request_game_state')
def handle_request_game_state(data):
    """Handle a request for the current game state."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    
    room = get_room(room_code)
    if not room:
        emit('error', {'message': 'Room not found'})
        return
    
    # Send the game state to the requesting player
    game_state = room.get_game_state_for_player(player_id)
    
    # Add AI game info if applicable
    if room_code in ai_games:
        bot = ai_games[room_code]
        game_state['is_ai_game'] = True
        game_state['ai_name'] = bot.name
    
    emit('game_state', game_state)


@socketio.on('use_power')
def handle_use_power(data):
    """Handle a player using a special power."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    power_name = data.get('power', '')
    
    room = get_room(room_code)
    if not room:
        emit('error', {'message': 'Room not found'})
        return
    
    # Attempt to use the power
    result = room.use_power(player_id, power_name)
    
    if not result['success']:
        emit('error', {'message': result['message']})
        return
    
    # Check if this is an AI game
    is_ai_game = room_code in ai_games
    
    # Broadcast the power used event to all players in the room
    emit('power_used', {
        'player_id': player_id,
        'player_name': room.player_names.get(player_id, 'Unknown'),
        'power': power_name,
        'power_info': room.POWERS.get(power_name, {}),
        'message': result['message'],
        'data': result.get('data', {})
    }, room=room_code)
    
    # Send updated game state to each player
    if is_ai_game:
        send_game_state_to_all_with_ai_flag(room)
    else:
        send_game_state_to_all(room)


@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat messages between players."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    message = data.get('message', '').strip()
    
    if not message:
        return
    
    room = get_room(room_code)
    if not room:
        return
    
    # Broadcast the message to the room
    emit('chat_message', {
        'player_id': player_id,
        'player_name': room.player_names.get(player_id, 'Unknown'),
        'message': message[:500]  # Limit message length
    }, room=room_code)


# =============================================================================
# AI GAME HANDLERS
# =============================================================================


@socketio.on('start_ai_game')
def handle_start_ai_game(data):
    """
    Start a new game against an AI opponent.
    
    Data:
        name: Player's display name
        difficulty: 'easy', 'medium', or 'hard'
        room_code: Optional room code to use (if coming from game page)
    """
    player_id = request.sid
    player_name = data.get('name', 'Player')
    difficulty = data.get('difficulty', 'medium')
    requested_room_code = data.get('room_code', '').upper()
    firebase_uid = data.get('uid')  # Firebase UID from client
    
    # Store Firebase UID mapping if provided
    if firebase_uid:
        socket_to_uid[player_id] = firebase_uid
        print(f'[AI GAME] Stored UID mapping: {player_id} -> {firebase_uid}')
    
    print(f'[AI GAME] Received start_ai_game from {player_id}')
    print(f'[AI GAME] Data: name={player_name}, difficulty={difficulty}, room_code={requested_room_code}')
    
    # Validate difficulty
    if difficulty not in ['easy', 'medium', 'hard']:
        difficulty = 'medium'
    
    # Check if player is already in a room
    if player_id in player_rooms:
        emit('error', {'message': 'Already in a room'})
        return
    
    # Use requested room code if provided, otherwise generate one
    room_code = requested_room_code if requested_room_code else generate_room_code()
    room = create_room(room_code)
    
    # Add the human player
    if not room.add_player(player_id, player_name):
        emit('error', {'message': 'Failed to create AI game'})
        delete_room(room_code)
        return
    
    # Create the bot player
    bot = BotPlayer(difficulty)
    
    # Add the bot to the room
    if not room.add_player(bot.player_id, bot.name):
        emit('error', {'message': 'Failed to add AI opponent'})
        delete_room(room_code)
        return
    
    # Track this as an AI game
    ai_games[room_code] = bot
    
    # Join the Socket.IO room
    join_room(room_code)
    player_rooms[player_id] = room_code
    
    print(f'AI Game started: Player {player_id} vs {bot.name} in room {room_code}')
    
    # Notify the player that the room was created
    emit('room_joined', {
        'room_code': room_code,
        'player_id': player_id,
        'players_count': 2,
        'waiting_for_opponent': False,
        'is_ai_game': True,
        'ai_difficulty': difficulty,
        'ai_name': bot.name
    })
    
    # Start the game immediately
    if room.start_game():
        print(f'AI Game started in room {room_code}')
        
        # Record game start time for duration tracking
        record_game_start(room_code)
        
        # Notify the player that the game has started
        emit('game_started', {
            'message': f'Game started against {bot.name}!',
            'room_code': room_code,
            'is_ai_game': True,
            'ai_name': bot.name
        })
        
        # Send initial game state
        game_state = room.get_game_state_for_player(player_id)
        game_state['is_ai_game'] = True
        game_state['ai_name'] = bot.name
        emit('game_state', game_state)
        
        # If it's the bot's turn first, trigger bot's turn
        if room.get_current_player() == bot.player_id:
            trigger_bot_turn(room_code)


def trigger_bot_turn(room_code: str):
    """
    Trigger the bot to take its turn after a delay.
    Runs in a background thread to not block the main thread.
    """
    def bot_turn_task():
        room = get_room(room_code)
        if not room or room.game_over:
            return
        
        bot = ai_games.get(room_code)
        if not bot:
            return
        
        # Verify it's still the bot's turn
        if room.get_current_player() != bot.player_id:
            return
        
        # Wait for the bot's "think time"
        think_time = bot.get_think_time()
        time.sleep(think_time)
        
        # Check again that the game is still valid
        room = get_room(room_code)
        if not room or room.game_over:
            return
        
        if room.get_current_player() != bot.player_id:
            return
        
        # Get the game state for the bot
        game_state = room.get_game_state_for_player(bot.player_id)
        
        # Check if bot should use a power first
        power_to_use = bot.should_use_power(game_state)
        if power_to_use:
            result = room.use_power(bot.player_id, power_to_use)
            if result['success']:
                # Emit power used event
                socketio.emit('power_used', {
                    'player_id': bot.player_id,
                    'player_name': bot.name,
                    'power': power_to_use,
                    'power_info': room.POWERS.get(power_to_use, {}),
                    'message': result['message'],
                    'data': result.get('data', {})
                }, room=room_code)
                
                # Update game state after power use
                game_state = room.get_game_state_for_player(bot.player_id)
        
        # Get playable cards for the bot
        hand = game_state.get('your_hand', [])
        playable = game_state.get('playable_cards', [])
        
        # Bot chooses a card
        card_to_play = bot.choose_card(hand, playable, game_state)
        
        if card_to_play:
            # Play the card at the end (position = None means append)
            result = room.play_card(bot.player_id, card_to_play, position=None)
            
            if result['success']:
                # Get card info
                card_info = get_card_info(card_to_play)
                
                # Broadcast the card played event
                socketio.emit('card_played', {
                    'player_id': bot.player_id,
                    'player_name': bot.name,
                    'card': card_to_play,
                    'card_info': card_info,
                    'points_earned': result['points_earned'],
                    'effect': result['effect'],
                    'message': result['message'],
                    'is_ai': True
                }, room=room_code)
                
                # Send updated game state to the human player
                send_game_state_to_all_with_ai_flag(room)
                
                # Check if game is over
                if room.game_over:
                    # Save the completed game to database
                    save_completed_game(room, 'ai', bot.difficulty)
                    
                    socketio.emit('game_over', {
                        'winner': room.winner,
                        'winner_name': room.player_names.get(room.winner, 'Unknown'),
                        'scores': room.scores,
                        'reason': 'win_condition',
                        'is_ai_game': True
                    }, room=room_code)
                # If it's still the bot's turn (e.g., opponent was skipped), trigger again
                elif room.get_current_player() == bot.player_id:
                    trigger_bot_turn(room_code)
        else:
            # Bot has no valid moves, must pass
            result = room.pass_turn(bot.player_id)
            
            if result['success']:
                # Broadcast the pass event
                socketio.emit('turn_passed', {
                    'player_id': bot.player_id,
                    'player_name': bot.name,
                    'drew_card': result.get('drew_card'),
                    'message': result['message'],
                    'is_ai': True
                }, room=room_code)
                
                # Send updated game state
                send_game_state_to_all_with_ai_flag(room)
                
                # Check if game is over
                if room.game_over:
                    # Save the completed game to database
                    save_completed_game(room, 'ai', bot.difficulty)
                    
                    socketio.emit('game_over', {
                        'winner': room.winner,
                        'winner_name': room.player_names.get(room.winner, 'Unknown'),
                        'scores': room.scores,
                        'reason': 'too_many_passes',
                        'is_ai_game': True
                    }, room=room_code)
                # If it's still the bot's turn, trigger again
                elif room.get_current_player() == bot.player_id:
                    trigger_bot_turn(room_code)
    
    # Run the bot turn in a background thread
    thread = threading.Thread(target=bot_turn_task)
    thread.daemon = True
    thread.start()


def send_game_state_to_all_with_ai_flag(room):
    """Send the appropriate game state to each player in the room, with AI flag."""
    bot = ai_games.get(room.room_code)
    
    for player_id in room.players:
        # Skip bot players
        if bot and player_id == bot.player_id:
            continue
        
        game_state = room.get_game_state_for_player(player_id)
        
        # Add AI game info
        if bot:
            game_state['is_ai_game'] = True
            game_state['ai_name'] = bot.name
        
        socketio.emit('game_state', game_state, room=player_id)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def start_game_for_room(room_code):
    """Start the game for a room when both players are ready."""
    room = get_room(room_code)
    if not room or not room.is_ready():
        return
    
    if room.game_started:
        return
    
    # Start the game
    if room.start_game():
        print(f'Game started in room {room_code}')
        
        # Record game start time for duration tracking
        record_game_start(room_code)
        
        # Notify all players that the game has started
        emit('game_started', {
            'message': 'Game is starting!',
            'room_code': room_code
        }, room=room_code)
        
        # Send initial game state to each player
        send_game_state_to_all(room)


def send_game_state_to_all(room):
    """Send the appropriate game state to each player in the room."""
    for player_id in room.players:
        game_state = room.get_game_state_for_player(player_id)
        emit('game_state', game_state, room=player_id)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


if __name__ == '__main__':
    print("=" * 50)
    print("  Python Syntax Card Game Server")
    print("=" * 50)
    print("")
    print("  Open http://localhost:5000 in your browser")
    print("  Open a second browser window to play multiplayer!")
    print("")
    print("=" * 50)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
