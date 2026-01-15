/**
 * Python Syntax Card Game - Frontend JavaScript
 * Hearthstone-inspired minimalist theme
 */

// =============================================================================
// GLOBAL STATE
// =============================================================================

let socket = null;
let playerId = null;
let playerName = '';
let isMyTurn = false;
let currentGameState = null;
let cardData = {};
let isAnimating = false;

// Card category to CSS class mapping
const categoryClasses = {
    'LOOP': 'loop',
    'VARIABLE': 'variable',
    'KEYWORD': 'keyword',
    'FUNCTION': 'function',
    'VALUE': 'value',
    'OPERATOR': 'operator',
    'SYNTAX_OPEN': 'syntax',
    'SYNTAX_CLOSE': 'syntax',
    'SYNTAX_COLON': 'syntax',
    'SPECIAL': 'special'
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        playerId = socket.id;
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        showNotification('Disconnected from server. Please refresh.', 'danger');
    });
    
    // Fetch card data
    fetch('/api/cards')
        .then(response => response.json())
        .then(data => {
            cardData = data;
            console.log('Loaded', Object.keys(data).length, 'cards');
        })
        .catch(err => console.error('Failed to load cards:', err));
    
    // Initialize appropriate page
    if (document.getElementById('createGameBtn')) {
        initHomePage();
    } else if (typeof ROOM_CODE !== 'undefined') {
        initGamePage();
    }
});

// =============================================================================
// HOME PAGE
// =============================================================================

function initHomePage() {
    const createBtn = document.getElementById('createGameBtn');
    const joinBtn = document.getElementById('joinGameBtn');
    const roomInput = document.getElementById('roomCodeInput');
    const nameInput = document.getElementById('playerNameInput');
    const statusDiv = document.getElementById('statusMessage');
    
    // Load saved name
    if (nameInput && localStorage.getItem('playerName')) {
        nameInput.value = localStorage.getItem('playerName');
    }
    
    createBtn.addEventListener('click', function() {
        const name = nameInput ? nameInput.value.trim() : '';
        if (name) localStorage.setItem('playerName', name);
        sessionStorage.setItem('playerName', name || 'Player 1');
        
        const roomCode = generateRoomCode();
        if (statusDiv) statusDiv.innerHTML = '<div class="notification">Creating room...</div>';
        window.location.href = '/game/' + roomCode;
    });
    
    joinBtn.addEventListener('click', function() {
        const roomCode = roomInput.value.trim().toUpperCase();
        const name = nameInput ? nameInput.value.trim() : '';
        
        if (roomCode.length < 4) {
            if (statusDiv) statusDiv.innerHTML = '<div class="notification danger">Enter a valid room code</div>';
            return;
        }
        
        if (name) localStorage.setItem('playerName', name);
        sessionStorage.setItem('playerName', name || 'Player 2');
        window.location.href = '/game/' + roomCode;
    });
    
    roomInput.addEventListener('keypress', e => { if (e.key === 'Enter') joinBtn.click(); });
    roomInput.addEventListener('input', function() { this.value = this.value.toUpperCase(); });
}

// =============================================================================
// GAME PAGE
// =============================================================================

function initGamePage() {
    console.log('Initializing game:', ROOM_CODE);
    playerName = sessionStorage.getItem('playerName') || 'Player';
    
    setupSocketEvents();
    setupGameControls();
    setupChat();
    
    socket.emit('join_room', { room: ROOM_CODE, name: playerName });
    
    // Room code copy
    const roomCodeEl = document.getElementById('roomCode');
    if (roomCodeEl) {
        roomCodeEl.addEventListener('click', function() {
            copyToClipboard(ROOM_CODE);
            showNotification('Room code copied!', 'success');
        });
    }
    
    showTurnIndicator('Connecting...');
}

function setupGameControls() {
    const endTurnBtn = document.getElementById('endTurnBtn');
    if (endTurnBtn) {
        endTurnBtn.addEventListener('click', function() {
            if (!this.disabled && isMyTurn) {
                socket.emit('pass_turn', { room: ROOM_CODE });
            }
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.target.matches('input, textarea')) return;
        
        // Number keys to play cards
        if (e.key >= '1' && e.key <= '9') {
            const idx = parseInt(e.key) - 1;
            if (currentGameState?.your_hand?.[idx]) {
                const card = currentGameState.your_hand[idx];
                if (currentGameState.playable_cards?.includes(card)) {
                    playCard(card);
                }
            }
        }
        
        // Space to end turn
        if (e.key === ' ' || e.key === 'Enter') {
            if (isMyTurn && (!currentGameState?.playable_cards?.length)) {
                socket.emit('pass_turn', { room: ROOM_CODE });
            }
        }
    });
}

// =============================================================================
// SOCKET EVENTS
// =============================================================================

function setupSocketEvents() {
    socket.on('room_joined', function(data) {
        console.log('Joined room:', data);
        if (data.waiting_for_opponent) {
            showTurnIndicator('Waiting for opponent...');
            showNotification(`Room ${data.room_code} created! Share this code.`, 'info');
        }
    });
    
    socket.on('player_joined', function(data) {
        showNotification(`${data.player_name} joined!`, 'success');
    });
    
    socket.on('player_left', function(data) {
        showNotification(data.message, 'warning');
    });
    
    socket.on('game_started', function(data) {
        showNotification('Game starting!', 'success');
        showTurnIndicator('Game Starting!', true);
    });
    
    socket.on('game_state', function(state) {
        console.log('Game state:', state);
        const wasMyTurn = isMyTurn;
        currentGameState = state;
        
        if (!wasMyTurn && state.is_your_turn && state.game_started && !state.game_over) {
            showTurnIndicator('Your Turn!', true);
        }
        
        updateGameUI(state);
    });
    
    socket.on('card_played', function(data) {
        if (data.player_id !== playerId) {
            showNotification(`${data.player_name} played "${data.card}"`, 'info');
        }
    });
    
    socket.on('turn_passed', function(data) {
        if (data.player_id !== playerId) {
            showNotification(`${data.player_name} passed`, 'info');
        }
    });
    
    socket.on('chat_message', function(data) {
        addChatMessage(data);
    });
    
    socket.on('game_over', function(data) {
        showGameOver(data);
    });
    
    socket.on('error', function(data) {
        showNotification(data.message, 'danger');
    });
}

// =============================================================================
// UI UPDATES
// =============================================================================

function updateGameUI(state) {
    isMyTurn = state.is_your_turn;
    
    // Update scores
    updateElement('yourScore', state.your_score);
    updateElement('opponentScore', state.opponent_score);
    
    // Update names
    updateElement('yourName', state.your_name || 'You');
    updateElement('opponentName', state.opponent_name || 'Opponent');
    
    // Update turn number
    updateElement('turnNumber', state.turn_number || 1);
    
    // Update deck count
    updateElement('deckCount', state.deck_remaining);
    
    // Update progress bars
    updateProgress('yourProgress', state.your_score);
    updateProgress('opponentProgress', state.opponent_score);
    
    // Render hands and played cards
    renderYourHand(state.your_hand || [], state.playable_cards || []);
    renderOpponentHand(state.opponent_card_count || 0);
    renderPlayedCards(state.played_cards || []);
    
    // Update end turn button
    updateEndTurnButton(state);
    
    // Update last card hint
    updateLastCardHint(state.played_cards);
}

function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) {
        const newValue = String(value);
        if (el.textContent !== newValue) {
            el.textContent = newValue;
            el.classList.add('score-updated');
            setTimeout(() => el.classList.remove('score-updated'), 400);
        }
    }
}

function updateProgress(id, score) {
    const el = document.getElementById(id);
    if (el) {
        const percent = Math.min(100, (score / 50) * 100);
        el.style.width = percent + '%';
    }
}

function updateEndTurnButton(state) {
    const btn = document.getElementById('endTurnBtn');
    if (!btn) return;
    
    const canAct = state.game_started && !state.game_over && state.is_your_turn;
    const hasPlayable = state.playable_cards?.length > 0;
    
    btn.disabled = !canAct || hasPlayable;
    
    const subtext = btn.querySelector('.btn-subtext');
    if (subtext) {
        if (!canAct) {
            subtext.textContent = "Not your turn";
        } else if (hasPlayable) {
            subtext.textContent = "Play a card";
        } else {
            subtext.textContent = "";
        }
    }
}

function updateLastCardHint(playedCards) {
    const el = document.getElementById('lastCardHint');
    if (!el) return;
    
    if (!playedCards?.length) {
        el.textContent = 'Any starting card is valid';
    } else {
        const lastCard = playedCards[playedCards.length - 1];
        const info = cardData[lastCard];
        if (info) {
            el.textContent = `Last: ${lastCard} (${info.category})`;
        }
    }
}

// =============================================================================
// CARD RENDERING
// =============================================================================

function renderYourHand(hand, playableCards) {
    const container = document.getElementById('yourCards');
    if (!container) return;
    
    if (!hand.length) {
        container.innerHTML = '<div class="empty-sequence">No cards</div>';
        return;
    }
    
    container.innerHTML = hand.map((cardName, i) => {
        const card = cardData[cardName] || { category: 'SPECIAL', points: 0 };
        const categoryClass = categoryClasses[card.category] || 'special';
        const isPlayable = playableCards.includes(cardName);
        const playableClass = isPlayable && isMyTurn ? 'playable' : 'disabled';
        
        return `
            <div class="game-card ${categoryClass} ${playableClass} card-enter"
                 data-card="${escapeHtml(cardName)}"
                 onclick="playCard('${escapeHtml(cardName)}')"
                 style="animation-delay: ${i * 0.05}s">
                <span class="card-category">${formatCategory(card.category)}</span>
                <span class="card-name">${escapeHtml(cardName)}</span>
                <span class="card-points">${card.points}pt</span>
            </div>
        `;
    }).join('');
}

function renderOpponentHand(count) {
    const container = document.getElementById('opponentCards');
    if (!container) return;
    
    if (count === 0) {
        container.innerHTML = '<div class="empty-sequence">No cards</div>';
        return;
    }
    
    container.innerHTML = Array(count).fill(0).map((_, i) => `
        <div class="game-card face-down" style="animation-delay: ${i * 0.02}s"></div>
    `).join('');
}

function renderPlayedCards(playedCards) {
    const container = document.getElementById('playedCards');
    if (!container) return;
    
    if (!playedCards.length) {
        container.innerHTML = '<div class="empty-sequence">Play a card to begin</div>';
        return;
    }
    
    // Show last 15 cards
    const maxShow = 15;
    const cards = playedCards.slice(-maxShow);
    const hasMore = playedCards.length > maxShow;
    
    let html = '';
    if (hasMore) {
        html += `<div class="more-indicator">+${playedCards.length - maxShow}</div>`;
    }
    
    html += cards.map((cardName, i) => {
        const card = cardData[cardName] || { category: 'SPECIAL' };
        const categoryClass = categoryClasses[card.category] || 'special';
        const isLast = i === cards.length - 1;
        
        return `
            <div class="game-card played ${categoryClass} ${isLast ? 'last-played' : ''}">
                <span class="card-name">${escapeHtml(cardName)}</span>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

function formatCategory(cat) {
    if (!cat) return '';
    return cat.replace('SYNTAX_', '').substring(0, 5);
}

// =============================================================================
// CARD PLAYING
// =============================================================================

function playCard(cardName) {
    if (isAnimating || !isMyTurn) return;
    
    if (!currentGameState?.playable_cards?.includes(cardName)) {
        showNotification("Can't play that card now", 'warning');
        return;
    }
    
    const cardEl = document.querySelector(`[data-card="${CSS.escape(cardName)}"]`);
    if (cardEl) {
        animateCardPlay(cardEl);
    }
    
    socket.emit('play_card', { room: ROOM_CODE, card: cardName });
}

function animateCardPlay(cardEl) {
    isAnimating = true;
    
    const rect = cardEl.getBoundingClientRect();
    const playZone = document.querySelector('.play-zone');
    const playRect = playZone.getBoundingClientRect();
    
    const clone = cardEl.cloneNode(true);
    clone.style.cssText = `
        position: fixed;
        left: ${rect.left}px;
        top: ${rect.top}px;
        width: ${rect.width}px;
        height: ${rect.height}px;
        z-index: 1000;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        pointer-events: none;
    `;
    document.body.appendChild(clone);
    
    cardEl.style.opacity = '0';
    cardEl.style.transform = 'scale(0)';
    
    requestAnimationFrame(() => {
        clone.style.left = `${playRect.left + playRect.width / 2 - rect.width / 2}px`;
        clone.style.top = `${playRect.top + playRect.height / 2 - rect.height / 2}px`;
        clone.style.transform = 'scale(1.1)';
    });
    
    setTimeout(() => {
        clone.remove();
        isAnimating = false;
    }, 350);
}

// =============================================================================
// TURN INDICATOR
// =============================================================================

function showTurnIndicator(text, autoHide = false) {
    const indicator = document.getElementById('turnIndicator');
    if (!indicator) return;
    
    const textEl = indicator.querySelector('.turn-text');
    if (textEl) textEl.textContent = text;
    
    indicator.classList.remove('your-turn');
    if (text.includes('Your Turn')) {
        indicator.classList.add('your-turn');
    }
    
    indicator.classList.add('visible');
    
    if (autoHide) {
        setTimeout(() => indicator.classList.remove('visible'), 2000);
    }
}

// =============================================================================
// NOTIFICATIONS
// =============================================================================

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    
    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;
    
    container.appendChild(notif);
    
    setTimeout(() => {
        notif.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}

// =============================================================================
// CHAT
// =============================================================================

function setupChat() {
    // Create chat elements
    const toggle = document.createElement('button');
    toggle.className = 'chat-toggle';
    toggle.innerHTML = '💬';
    toggle.onclick = () => panel.classList.toggle('open');
    
    const panel = document.createElement('div');
    panel.className = 'chat-panel';
    panel.id = 'chatPanel';
    panel.innerHTML = `
        <div class="chat-header">
            <span>Chat</span>
            <button class="chat-close" onclick="document.getElementById('chatPanel').classList.remove('open')">×</button>
        </div>
        <div class="chat-messages" id="chatMessages"></div>
        <div class="chat-input-area">
            <input type="text" id="chatInput" placeholder="Message..." maxlength="200">
            <button onclick="sendChat()">Send</button>
        </div>
    `;
    
    document.body.appendChild(toggle);
    document.body.appendChild(panel);
    
    document.getElementById('chatInput').addEventListener('keypress', e => {
        if (e.key === 'Enter') sendChat();
    });
}

function sendChat() {
    const input = document.getElementById('chatInput');
    if (!input?.value.trim()) return;
    
    socket.emit('chat_message', { room: ROOM_CODE, message: input.value.trim() });
    input.value = '';
}

function addChatMessage(data) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    
    const isOwn = data.player_id === playerId;
    const msg = document.createElement('div');
    msg.className = `chat-message ${isOwn ? 'own' : 'other'}`;
    msg.innerHTML = `<span class="chat-sender">${escapeHtml(data.player_name)}</span>${escapeHtml(data.message)}`;
    
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

// =============================================================================
// GAME OVER
// =============================================================================

function showGameOver(data) {
    const modal = document.getElementById('gameOverModal');
    const resultEl = document.getElementById('gameResult');
    const scoresEl = document.getElementById('finalScores');
    const reasonEl = document.getElementById('gameEndReason');
    
    const isWinner = data.winner === playerId;
    
    if (resultEl) {
        resultEl.textContent = isWinner ? 'Victory!' : 'Defeat';
        resultEl.className = `game-result ${isWinner ? 'win' : 'lose'}`;
    }
    
    if (scoresEl && data.scores) {
        const scores = Object.entries(data.scores)
            .map(([id, score]) => `${id === playerId ? 'You' : 'Opponent'}: ${score}`)
            .join(' • ');
        scoresEl.textContent = scores;
    }
    
    if (reasonEl) {
        const reasons = {
            'win_condition': 'Reached 50 points!',
            'too_many_passes': 'Opponent could not play',
            'opponent_disconnected': 'Opponent disconnected'
        };
        reasonEl.textContent = reasons[data.reason] || '';
    }
    
    if (modal) {
        new bootstrap.Modal(modal).show();
    }
    
    if (isWinner) createConfetti();
}

function createConfetti() {
    const colors = ['#4ade80', '#4a9eff', '#d4a84b', '#a78bfa', '#f87171'];
    for (let i = 0; i < 80; i++) {
        const conf = document.createElement('div');
        conf.style.cssText = `
            position: fixed;
            width: 8px;
            height: 8px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            left: ${Math.random() * 100}vw;
            top: -10px;
            z-index: 10000;
            pointer-events: none;
            animation: confettiFall ${2 + Math.random() * 2}s linear forwards;
        `;
        document.body.appendChild(conf);
        setTimeout(() => conf.remove(), 4000);
    }
}

// =============================================================================
// UTILITIES
// =============================================================================

function generateRoomCode() {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    return Array(6).fill(0).map(() => chars[Math.floor(Math.random() * chars.length)]).join('');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function copyToClipboard(text) {
    navigator.clipboard?.writeText(text) || (() => {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
    })();
}
