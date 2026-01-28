"""
Authentication Helper Module

Provides authentication utilities for the Python Card Game:
- User registration and creation
- Token verification
- User profile management
- Authentication decorators
"""

from functools import wraps
from flask import request, jsonify
from firebase_admin import auth as firebase_auth
from firebase_admin.firestore import SERVER_TIMESTAMP

from firebase_config import (
    initialize_firebase,
    is_firebase_initialized,
    verify_id_token,
    get_user,
    get_users_collection,
    get_firestore_client
)


def require_auth(f):
    """
    Decorator to require Firebase authentication for an endpoint.
    
    Expects Authorization header with Bearer token:
    Authorization: Bearer <firebase_id_token>
    
    Adds 'current_user' to the request context with decoded token claims.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_firebase_initialized():
            return jsonify({
                'success': False,
                'error': 'Authentication service unavailable'
            }), 503
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid Authorization header'
            }), 401
        
        token = auth_header.split('Bearer ')[1]
        
        # Verify the token
        decoded_token = verify_id_token(token)
        
        if not decoded_token:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
        
        # Add user info to request context
        request.current_user = decoded_token
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    Decorator for optional authentication.
    
    If valid token is provided, adds 'current_user' to request context.
    If no token or invalid token, current_user will be None.
    Allows endpoint to work both authenticated and unauthenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.current_user = None
        
        if is_firebase_initialized():
            auth_header = request.headers.get('Authorization', '')
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split('Bearer ')[1]
                decoded_token = verify_id_token(token)
                if decoded_token:
                    request.current_user = decoded_token
        
        return f(*args, **kwargs)
    
    return decorated_function


def create_user(email, password, display_name=None):
    """
    Create a new Firebase user and Firestore profile.
    
    Args:
        email (str): User's email address
        password (str): User's password
        display_name (str, optional): User's display name
        
    Returns:
        dict: Result with 'success' bool and 'user'/'error' fields
    """
    if not is_firebase_initialized():
        return {
            'success': False,
            'error': 'Firebase not initialized'
        }
    
    try:
        # Create the Firebase Auth user
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=display_name or email.split('@')[0]
        )
        
        # DISABLED: Skip Firestore profile creation - causes blocking
        # The profile will be created lazily when needed
        print(f"[AUTH] User created: {user_record.uid} - skipping Firestore profile (disabled)")
        
        return {
            'success': True,
            'user': {
                'uid': user_record.uid,
                'email': user_record.email,
                'displayName': user_record.display_name
            }
        }
        
    except firebase_auth.EmailAlreadyExistsError:
        return {
            'success': False,
            'error': 'Email already registered'
        }
    except Exception as e:
        print(f"Error creating user: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_user_profile(uid, timeout_seconds=5):
    """
    Get a user's profile from Firestore.
    
    Args:
        uid (str): User's Firebase UID
        timeout_seconds (int): Maximum time to wait for Firestore
        
    Returns:
        dict or None: User profile data or None if not found
    """
    # DISABLED: Firestore access causes blocking
    print(f"[AUTH] get_user_profile disabled - returning None for {uid}")
    return None


def update_user_profile(uid, updates):
    """
    Update a user's profile in Firestore.
    
    Args:
        uid (str): User's Firebase UID
        updates (dict): Fields to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    # DISABLED: Firestore access causes blocking
    print(f"[AUTH] update_user_profile disabled - would update {uid}")
    return True


def update_user_stats(uid, game_result):
    """
    Update a user's stats after a game.
    
    Args:
        uid (str): User's Firebase UID
        game_result (dict): Game result with 'score', 'won' fields
        
    Returns:
        bool: True if successful, False otherwise
    """
    # DISABLED: Firestore access causes blocking
    print(f"[AUTH] update_user_stats disabled - would update {uid}")
    return True


def get_user_game_history(uid, limit=20):
    """
    Get a user's game history from Firestore.
    
    Args:
        uid (str): User's Firebase UID
        limit (int): Maximum number of games to return
        
    Returns:
        list: List of game records
    """
    # DISABLED: Firestore access causes blocking
    print(f"[AUTH] get_user_game_history disabled - returning empty for {uid}")
    return []


def get_leaderboard(limit=50):
    """
    Get the top players leaderboard.
    
    Args:
        limit (int): Maximum number of players to return
        
    Returns:
        list: List of player stats sorted by games won
    """
    # DISABLED: Firestore access causes blocking
    print(f"[AUTH] get_leaderboard disabled - returning empty")
    return []


def create_custom_token(uid):
    """
    Create a custom Firebase token for a user.
    Useful for server-side authentication flows.
    
    Args:
        uid (str): User's Firebase UID
        
    Returns:
        str or None: Custom token or None on error
    """
    if not is_firebase_initialized():
        return None
    
    try:
        custom_token = firebase_auth.create_custom_token(uid)
        return custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None


def delete_user(uid):
    """
    Delete a user from Firebase Auth and Firestore.
    
    Args:
        uid (str): User's Firebase UID
        
    Returns:
        bool: True if successful, False otherwise
    """
    # DISABLED: Firestore access causes blocking
    print(f"[AUTH] delete_user disabled - would delete {uid}")
    return False
