# Python Syntax Card Game

A browser-based 1v1 card game where players compete by playing Python syntax cards. Built with Flask and Socket.IO for real-time multiplayer gameplay, featuring AI opponents and Firebase authentication.

## Game Overview

- Players take turns playing Python syntax cards (like `for`, `x`, `in`, `range`, etc.)
- Cards must follow logical sequencing rules (e.g., `for` → `x` → `in` → `range`)
- Each card has point values: Common (1pt), Uncommon (2pts), Rare (3pts)
- Special cards add strategy: Draw 2, Skip, Wild
- **Win Condition**: First player to reach 50 points wins!

## Features

- **Real-time Multiplayer**: Play against friends with room codes
- **Quick Match**: Auto-join available games or create new ones
- **AI Opponents**: Practice against bots with Easy, Medium, or Hard difficulty
- **User Accounts**: Firebase authentication with email/password
- **Leaderboard**: Track wins and compete for rankings
- **User Profiles**: View your stats, game history, and win rate

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + Flask |
| Real-time | Flask-SocketIO |
| Frontend | HTML + CSS + JavaScript |
| Styling | Bootstrap 5 |
| Authentication | Firebase Auth |
| Database | In-memory (Firestore optional) |
| Deployment | Render |

## Project Structure

```
pythongame-1/
├── app.py                 # Main Flask application with Socket.IO
├── game_logic.py          # Card rules, deck, game state, AI bot
├── auth.py                # Authentication helpers and decorators
├── database.py            # Database operations (Firestore)
├── firebase_config.py     # Firebase initialization
├── requirements.txt       # Python dependencies
├── render.yaml            # Render deployment configuration
├── Procfile               # Heroku/Render process file
├── runtime.txt            # Python version specification
├── static/
│   ├── css/
│   │   └── style.css      # Card designs, animations, UI styling
│   └── js/
│       ├── game.js        # Frontend game logic, Socket.IO
│       └── auth.js        # Firebase authentication client
└── templates/
    ├── index.html         # Home/lobby page
    ├── game.html          # Main game board
    ├── profile.html       # User profile page
    └── leaderboard.html   # Rankings page
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/pythongame-1.git
cd pythongame-1
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
py -m venv venv
.\venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Firebase (Optional)

For user authentication features:

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Email/Password authentication
3. Generate a service account key (Project Settings → Service Accounts)
4. Set environment variables:
   ```bash
   export FIREBASE_CREDENTIALS='{"your": "service-account-json"}'
   export FIREBASE_PROJECT_ID='your-project-id'
   ```

The game works without Firebase - authentication features will be disabled.

### 5. Run the Server

```bash
python app.py
```

The server will start at `http://localhost:5000`

## How to Play

### Multiplayer (PvP)

1. Open `http://localhost:5000` in your browser
2. Click **"Create New Game"** to generate a room code
3. Share the room code with your opponent
4. Your opponent enters the code and clicks **"Join Game"**
5. Take turns playing cards that follow valid Python syntax sequences
6. First to 50 points wins!

### vs AI

1. Click **"Play vs AI"** on the home page
2. Select difficulty: Easy, Medium, or Hard
3. Play against the AI bot
4. The AI adapts its strategy based on difficulty level

### Quick Match

1. Click **"Quick Match"** to auto-join an available game
2. If no games are available, one will be created for you
3. Wait for an opponent to join

## Card Categories

| Category | Examples | Points |
|----------|----------|--------|
| Loop | `for`, `while` | 2 pts |
| Variable | `x`, `i`, `n` | 1 pt |
| Keyword | `in`, `if`, `else` | 2 pts |
| Function | `range`, `print`, `len` | 2 pts |
| Value | `1`, `10`, `True`, `False` | 1 pt |
| Syntax | `(`, `)`, `:` | 1 pt |
| Special | Draw 2, Skip, Wild | 0 pts |

## AI Difficulty Levels

| Level | Behavior |
|-------|----------|
| Easy | Random valid card selection, great for learning |
| Medium | Prioritizes high-point cards, fair challenge |
| Hard | Strategic play with combos and blocking tactics |

## API Endpoints

### Game APIs
- `GET /api/cards` - Get all card definitions
- `GET /api/rooms` - List open rooms
- `POST /api/validate-syntax` - Validate Python syntax from cards
- `POST /api/check-card` - Check if a card can be played

### User APIs (Requires Auth)
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update profile
- `GET /api/user/stats` - Get game statistics
- `GET /api/user/games` - Get game history

### Leaderboard
- `GET /api/leaderboard` - Get top players
- `GET /api/leaderboard/advanced` - Leaderboard with sorting options

## Deployment to Render

1. Push your code to GitHub
2. Create a new Web Service on [render.com](https://render.com)
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml` configuration
5. Add environment variables in Render dashboard:
   - `SECRET_KEY` (auto-generated)
   - `FIREBASE_CREDENTIALS` (your Firebase service account JSON)
   - `FIREBASE_PROJECT_ID` (your Firebase project ID)
6. Deploy!

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask session secret key |
| `FIREBASE_CREDENTIALS` | No | Firebase service account JSON |
| `FIREBASE_PROJECT_ID` | No | Firebase project ID |

## Development Status

- [x] Phase 1: Project Setup
- [x] Phase 2: Game Logic Backend
- [x] Phase 3: Flask Server and Routes
- [x] Phase 4: Frontend HTML Structure
- [x] Phase 5: Frontend JavaScript Logic
- [x] Phase 6: Styling and Polish
- [x] Phase 7: AI Opponents
- [x] Phase 8: User Authentication
- [x] Phase 9: Leaderboard & Stats
- [x] Phase 10: Deployment Configuration

## License

This project is for educational purposes.
