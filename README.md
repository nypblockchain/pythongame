# Python Syntax Card Game

A browser-based 1v1 card game where players compete by playing Python syntax cards. Built with Flask and Socket.IO for real-time multiplayer gameplay.

## Game Overview

- Players take turns playing Python syntax cards (like `for`, `x`, `in`, `range`, etc.)
- Cards must follow logical sequencing rules (e.g., `for` → `x` → `in` → `range`)
- Each card has point values: Common (1pt), Uncommon (2pts), Rare (3pts)
- Special cards add strategy: Draw 2, Skip, Wild
- **Win Condition**: First player to reach 50 points wins!

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + Flask |
| Real-time | Flask-SocketIO |
| Frontend | HTML + CSS + JavaScript |
| Styling | Bootstrap 5 |

## Project Structure

```
pythongame-1/
├── app.py                 # Main Flask application
├── game_logic.py          # Card rules, deck, game state
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css      # Card designs, animations
│   └── js/
│       └── game.js        # Frontend game logic, Socket.IO
└── templates/
    ├── index.html         # Home/lobby page
    └── game.html          # Main game board
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

### 4. Run the Server

```bash
python app.py
```

The server will start at `http://localhost:5000`

## How to Play

1. Open `http://localhost:5000` in your browser
2. Click **"Create New Game"** to generate a room code
3. Share the room code with your opponent
4. Your opponent enters the code and clicks **"Join Game"**
5. Take turns playing cards that follow valid Python syntax sequences
6. First to 50 points wins!

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

## Development Status

- [x] Phase 1: Project Setup
- [ ] Phase 2: Game Logic Backend
- [ ] Phase 3: Flask Server and Routes
- [ ] Phase 4: Frontend HTML Structure
- [ ] Phase 5: Frontend JavaScript Logic
- [ ] Phase 6: Styling and Polish
- [ ] Phase 7: Testing and Deployment

## Team Members

- Add your team members here

## License

This project is for educational purposes.
