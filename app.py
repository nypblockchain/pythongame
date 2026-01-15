"""
Python Syntax Card Game - Main Flask Application
A browser-based 1v1 card game where players compete by playing Python syntax cards.
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from game_logic import (
    create_room, get_room, delete_room,
    get_card_info, CARDS
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'python-card-game-secret-key'

# Initialize Socket.IO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Track which player is in which room (socket_id: room_code)
player_rooms = {}

# =============================================================================
# HTTP ROUTES
# =============================================================================


@app.route('/')
def index():
    """Home page - game lobby."""
    return render_template('index.html')


@app.route('/game/<room_code>')
def game(room_code):
    """Game board page."""
    return render_template('game.html', room_code=room_code)


@app.route('/api/cards')
def get_cards():
    """API endpoint to get all card definitions."""
    return CARDS


# =============================================================================
# SOCKET.IO EVENT HANDLERS
# =============================================================================


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f'Client connected: {request.sid}')


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
            # Get opponent before removing player
            opponent_id = room.get_opponent(player_id)
            
            # Remove the player from the game
            room.remove_player(player_id)
            
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
        
        del player_rooms[player_id]


@socketio.on('join_room')
def handle_join_room(data):
    """Handle player joining a room."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    player_name = data.get('name', f'Player')
    
    if not room_code:
        emit('error', {'message': 'Room code is required'})
        return
    
    # Get or create the room
    room = get_room(room_code)
    if not room:
        room = create_room(room_code)
        print(f'Created new room: {room_code}')
    
    # Try to add the player
    if not room.add_player(player_id, player_name):
        emit('error', {'message': 'Room is full (2 players max)'})
        return
    
    # Join the Socket.IO room for broadcasting
    join_room(room_code)
    player_rooms[player_id] = room_code
    
    print(f'Player {player_id} joined room {room_code} ({len(room.players)}/2 players)')
    
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


@socketio.on('play_card')
def handle_play_card(data):
    """Handle a player playing a card."""
    player_id = request.sid
    room_code = data.get('room', '').upper()
    card_name = data.get('card', '')
    
    room = get_room(room_code)
    if not room:
        emit('error', {'message': 'Room not found'})
        return
    
    # Attempt to play the card
    result = room.play_card(player_id, card_name)
    
    if not result['success']:
        emit('error', {'message': result['message']})
        return
    
    # Get card info for the played card
    card_info = get_card_info(card_name)
    
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
    send_game_state_to_all(room)
    
    # Check if game is over
    if room.game_over:
        emit('game_over', {
            'winner': room.winner,
            'winner_name': room.player_names.get(room.winner, 'Unknown'),
            'scores': room.scores,
            'reason': 'win_condition'
        }, room=room_code)


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
    
    # Broadcast the pass event to all players in the room
    emit('turn_passed', {
        'player_id': player_id,
        'player_name': room.player_names.get(player_id, 'Unknown'),
        'drew_card': result.get('drew_card'),
        'message': result['message']
    }, room=room_code)
    
    # Send updated game state to each player
    send_game_state_to_all(room)
    
    # Check if game is over
    if room.game_over:
        emit('game_over', {
            'winner': room.winner,
            'winner_name': room.player_names.get(room.winner, 'Unknown'),
            'scores': room.scores,
            'reason': 'too_many_passes'
        }, room=room_code)


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
    emit('game_state', game_state)


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
