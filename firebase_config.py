"""
Firebase Admin SDK Configuration

This module initializes the Firebase Admin SDK for authentication and Firestore database.

================================================================================
SETUP INSTRUCTIONS
================================================================================

STEP 1: Firebase Console Setup
------------------------------
1. Go to Firebase Console (https://console.firebase.google.com)
2. Create a new project or select an existing one
3. Enable Authentication:
   - Go to Build > Authentication > Sign-in method
   - Enable "Email/Password" provider
4. Enable Firestore Database:
   - Go to Build > Firestore Database
   - Click "Create database"
   - Start in "test mode" for development (change to production rules later)
5. Get credentials:
   - Go to Project Settings (gear icon) > Service Accounts
   - Select "Python" tab
   - Click "Generate new private key" to download JSON file

STEP 2: Local Development Setup
-------------------------------
Option A (Recommended):
   - Save the downloaded JSON file as 'firebase-credentials.json' in project root
   - The file is already in .gitignore so it won't be committed

Option B:
   - Save the JSON file anywhere
   - Set environment variable: FIREBASE_CREDENTIALS_PATH=/path/to/your/file.json

================================================================================
RENDER DEPLOYMENT INSTRUCTIONS
================================================================================

When you're ready to deploy to Render:

STEP 1: Prepare Your Credentials
--------------------------------
1. Open your local 'firebase-credentials.json' file
2. Copy the ENTIRE contents (the whole JSON object including { and })
   It should look something like this:
   
   {
     "type": "service_account",
     "project_id": "pythongame-7b673",
     "private_key_id": "...",
     "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
     "client_email": "...",
     "client_id": "...",
     ...
   }

STEP 2: Set Up Render Dashboard
-------------------------------
1. Go to https://dashboard.render.com
2. Create a new Web Service or select your existing one
3. Go to "Environment" tab
4. Add these environment variables:

   FIREBASE_CREDENTIALS
   --------------------
   - Click "Add Environment Variable"
   - Key: FIREBASE_CREDENTIALS
   - Value: Paste the ENTIRE JSON contents from step 1 (all on one line is fine)
   - Click Save

   FIREBASE_PROJECT_ID
   -------------------
   - Key: FIREBASE_PROJECT_ID  
   - Value: pythongame-7b673
   
   SECRET_KEY (for Flask sessions)
   -------------------------------
   - Key: SECRET_KEY
   - Value: Click "Generate" or enter a random string

STEP 3: Deploy
--------------
1. Push your code to GitHub (if not already connected)
2. Render will automatically deploy, or click "Manual Deploy"
3. Check the logs to verify "Firebase initialized successfully" appears

TROUBLESHOOTING
---------------
- "Firebase credentials not found": Check FIREBASE_CREDENTIALS is set correctly
- "Error parsing FIREBASE_CREDENTIALS": Make sure you copied the complete JSON
- "Invalid service account": Regenerate the key in Firebase Console

================================================================================

Environment Variables Summary:
- FIREBASE_CREDENTIALS: JSON string containing the service account credentials
- FIREBASE_CREDENTIALS_PATH: Path to the credentials JSON file (for local dev)
- FIREBASE_PROJECT_ID: Firebase project ID (optional, extracted from credentials)
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Global variables to track initialization state
_firebase_app = None
_firestore_client = None


def _get_credentials():
    """
    Get Firebase credentials from environment variables or local file.
    
    Priority:
    1. FIREBASE_CREDENTIALS environment variable (JSON string)
    2. FIREBASE_CREDENTIALS_PATH environment variable (file path)
    3. Local 'firebase-credentials.json' file
    
    Returns:
        firebase_admin.credentials.Certificate or None
    """
    # Option 1: JSON string in environment variable
    creds_json = os.environ.get('FIREBASE_CREDENTIALS')
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            return credentials.Certificate(creds_dict)
        except json.JSONDecodeError as e:
            print(f"Error parsing FIREBASE_CREDENTIALS: {e}")
            return None
    
    # Option 2: Path from environment variable
    creds_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    if creds_path and os.path.exists(creds_path):
        try:
            return credentials.Certificate(creds_path)
        except Exception as e:
            print(f"Error loading credentials from {creds_path}: {e}")
            return None
    
    # Option 3: Default local file
    local_creds_path = os.path.join(os.path.dirname(__file__), 'firebase-credentials.json')
    if os.path.exists(local_creds_path):
        try:
            return credentials.Certificate(local_creds_path)
        except Exception as e:
            print(f"Error loading credentials from {local_creds_path}: {e}")
            return None
    
    return None


def initialize_firebase():
    """
    Initialize the Firebase Admin SDK.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    global _firebase_app, _firestore_client
    
    # Check if already initialized
    if _firebase_app is not None:
        return True
    
    # Check if initialized by another module
    try:
        _firebase_app = firebase_admin.get_app()
        _firestore_client = firestore.client()
        return True
    except ValueError:
        # Not initialized yet, continue with initialization
        pass
    
    creds = _get_credentials()
    
    if creds is None:
        print("Warning: Firebase credentials not found. Firebase features will be disabled.")
        print("See firebase_config.py for setup instructions.")
        return False
    
    try:
        # Get project ID from environment or let it be extracted from credentials
        project_id = os.environ.get('FIREBASE_PROJECT_ID')
        
        options = {}
        if project_id:
            options['projectId'] = project_id
        
        _firebase_app = firebase_admin.initialize_app(creds, options)
        _firestore_client = firestore.client()
        print("Firebase initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False


def get_firestore_client():
    """
    Get the Firestore database client.
    
    Returns:
        firestore.Client or None: Firestore client if initialized, None otherwise
    """
    global _firestore_client
    
    if _firestore_client is None:
        if not initialize_firebase():
            return None
    
    return _firestore_client


def get_auth():
    """
    Get the Firebase Auth module.
    
    Returns:
        firebase_admin.auth module or None: Auth module if initialized, None otherwise
    """
    if _firebase_app is None:
        if not initialize_firebase():
            return None
    
    return auth


def is_firebase_initialized():
    """
    Check if Firebase has been successfully initialized.
    
    Returns:
        bool: True if Firebase is initialized and ready, False otherwise
    """
    return _firebase_app is not None


def verify_id_token(id_token):
    """
    Verify a Firebase ID token from the client.
    
    Args:
        id_token (str): The Firebase ID token to verify
        
    Returns:
        dict or None: Decoded token claims if valid, None if invalid or Firebase not initialized
    """
    if not is_firebase_initialized():
        return None
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError:
        print("Invalid ID token")
        return None
    except auth.ExpiredIdTokenError:
        print("Expired ID token")
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None


def get_user(uid):
    """
    Get a user record by UID.
    
    Args:
        uid (str): The user's Firebase UID
        
    Returns:
        firebase_admin.auth.UserRecord or None: User record if found, None otherwise
    """
    if not is_firebase_initialized():
        return None
    
    try:
        return auth.get_user(uid)
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


# Firestore collection references (for convenience)
def get_users_collection():
    """Get reference to the 'users' collection."""
    db = get_firestore_client()
    if db:
        return db.collection('users')
    return None


def get_games_collection():
    """Get reference to the 'games' collection."""
    db = get_firestore_client()
    if db:
        return db.collection('games')
    return None
