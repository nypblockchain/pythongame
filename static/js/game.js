/**
 * Python Syntax Card Game - Enhanced Frontend JavaScript
 * Hearthstone-inspired with smooth animations and visual polish
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
let lastPlayedCardsCount = 0;

// Insertion point state
let selectedInsertionIndex = null;  // null means append to end (default)
let selectedCardFromHand = null;    // The card currently selected from hand for insertion
let currentPlayableAtPosition = []; // Cards playable at currently selected position

// Tooltip state
let tooltipTimeout = null;
let tooltipVisible = false;
const TOOLTIP_DELAY = 300; // ms delay before showing tooltip

// Power system state
let powerModalOpen = false;
let peekModalOpen = false;
let peekCountdownInterval = null;

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
    'SYNTAX_COMMA': 'syntax',
    'SPECIAL': 'special'
};

// Category display names
const categoryNames = {
    'LOOP': 'Loop',
    'VARIABLE': 'Var',
    'KEYWORD': 'Key',
    'FUNCTION': 'Func',
    'VALUE': 'Val',
    'OPERATOR': 'Op',
    'SYNTAX_OPEN': 'Syn',
    'SYNTAX_CLOSE': 'Syn',
    'SYNTAX_COLON': 'Syn',
    'SYNTAX_COMMA': 'Syn',
    'SPECIAL': 'Special'
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
    console.log('initHomePage called');
    
    const createBtn = document.getElementById('createGameBtn');
    const joinBtn = document.getElementById('joinGameBtn');
    const quickMatchBtn = document.getElementById('quickMatchBtn');
    const playAIBtn = document.getElementById('playAIBtn');
    const roomInput = document.getElementById('roomCodeInput');
    const nameInput = document.getElementById('playerNameInput');
    const statusDiv = document.getElementById('statusMessage');
    
    console.log('Elements found:', {
        createBtn: !!createBtn,
        joinBtn: !!joinBtn,
        quickMatchBtn: !!quickMatchBtn,
        playAIBtn: !!playAIBtn,
        roomInput: !!roomInput,
        nameInput: !!nameInput
    });
    
    // Load saved name
    if (nameInput && localStorage.getItem('playerName')) {
        nameInput.value = localStorage.getItem('playerName');
        console.log('Loaded saved name:', nameInput.value);
    }
    
    // Add button click effects
    [createBtn, joinBtn, quickMatchBtn, playAIBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('mousedown', () => btn.style.transform = 'scale(0.98)');
            btn.addEventListener('mouseup', () => btn.style.transform = '');
            btn.addEventListener('mouseleave', () => btn.style.transform = '');
        }
    });
    
    // Quick Match button - auto-join or create
    if (quickMatchBtn) {
        quickMatchBtn.addEventListener('click', function() {
            const name = nameInput ? nameInput.value.trim() : '';
            if (name) localStorage.setItem('playerName', name);
            sessionStorage.setItem('playerName', name || 'Player');
            
            // Add loading effect
            this.innerHTML = '<span class="loading-spinner-small"></span><span>Finding match...</span>';
            this.disabled = true;
            
            // Get Firebase UID if available
            const firebaseUid = localStorage.getItem('firebaseUid') || sessionStorage.getItem('firebaseUid');
            
            // Emit quick match event with UID
            socket.emit('quick_match', { 
                name: name || 'Player',
                uid: firebaseUid
            });
        });
    }
    
    // Play vs AI button - open difficulty selection modal
    if (playAIBtn) {
        playAIBtn.addEventListener('click', function() {
            const name = nameInput ? nameInput.value.trim() : '';
            if (name) localStorage.setItem('playerName', name);
            sessionStorage.setItem('playerName', name || 'Player');
            
            // Open AI difficulty selection modal
            openAIModal();
        });
    }
    
    // Setup AI modal handlers
    setupAIModal();
    
    if (createBtn) {
        createBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Create game button clicked');
            
            try {
                const name = nameInput ? nameInput.value.trim() : '';
                console.log('Player name:', name || '(empty)');
                
                // Save name
                localStorage.setItem('playerName', name || 'Player 1');
                sessionStorage.setItem('playerName', name || 'Player 1');
                
                // Show loading state
                this.textContent = 'Creating...';
                this.disabled = true;
                
                // Generate room code and navigate
                const roomCode = generateRoomCode();
                console.log('Generated room code:', roomCode);
                
                const gameUrl = '/game/' + roomCode;
                console.log('Navigating to:', gameUrl);
                
                // Use location.assign for navigation
                window.location.assign(gameUrl);
            } catch (error) {
                console.error('Error creating game:', error);
                this.textContent = 'Create Private Game';
                this.disabled = false;
                alert('Error: ' + error.message);
            }
        });
    } else {
        console.error('createGameBtn not found!');
    }
    
    if (joinBtn) {
        joinBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Join game button clicked');
            
            try {
                const roomCode = roomInput ? roomInput.value.trim().toUpperCase() : '';
                const name = nameInput ? nameInput.value.trim() : '';
                
                if (roomCode.length < 4) {
                    if (statusDiv) statusDiv.innerHTML = '<div class="notification danger">Enter a valid room code</div>';
                    if (roomInput) {
                        roomInput.classList.add('shake');
                        setTimeout(() => roomInput.classList.remove('shake'), 400);
                    }
                    return;
                }
                
                console.log('Joining room:', roomCode, 'as', name || '(empty)');
                
                // Save name
                localStorage.setItem('playerName', name || 'Player 2');
                sessionStorage.setItem('playerName', name || 'Player 2');
                
                // Show loading state
                this.textContent = 'Joining...';
                this.disabled = true;
                
                // Navigate to game page
                window.location.assign('/game/' + roomCode);
            } catch (error) {
                console.error('Error joining game:', error);
                this.textContent = 'Join';
                this.disabled = false;
                alert('Error: ' + error.message);
            }
        });
    } else {
        console.error('joinGameBtn not found!');
    }
    
    if (roomInput) {
        roomInput.addEventListener('keypress', e => { if (e.key === 'Enter' && joinBtn) joinBtn.click(); });
        roomInput.addEventListener('input', function() { this.value = this.value.toUpperCase(); });
    }
    
    // Focus animation for inputs
    [nameInput, roomInput].forEach(input => {
        if (input) {
            input.addEventListener('focus', () => {
                input.parentElement?.classList.add('input-focused');
            });
            input.addEventListener('blur', () => {
                input.parentElement?.classList.remove('input-focused');
            });
        }
    });
    
    // Setup lobby-specific socket events
    setupLobbySocketEvents();
    
    // Request open rooms list on load
    socket.emit('get_open_rooms');
}

// =============================================================================
// LOBBY ROOM LIST
// =============================================================================

/**
 * Set up Socket.IO events for the lobby room list
 */
function setupLobbySocketEvents() {
    // Handle room joined (from quick match)
    socket.on('room_joined', function(data) {
        console.log('Room joined via quick match:', data);
        // Redirect to the game page
        window.location.href = '/game/' + data.room_code;
    });
    
    // Handle room list updates
    socket.on('room_list_update', function(data) {
        console.log('Room list update:', data);
        updateRoomsList(data.rooms);
    });
    
    // Handle errors
    socket.on('error', function(data) {
        console.error('Lobby error:', data);
        const statusDiv = document.getElementById('statusMessage');
        if (statusDiv) {
            statusDiv.innerHTML = `<div class="notification danger">${escapeHtml(data.message)}</div>`;
        }
        
        // Reset quick match button if it was clicked
        const quickMatchBtn = document.getElementById('quickMatchBtn');
        if (quickMatchBtn) {
            quickMatchBtn.innerHTML = `
                <span class="quick-match-icon">⚡</span>
                <span class="quick-match-text">Quick Match</span>
                <span class="quick-match-hint">Auto-join or create game</span>
            `;
            quickMatchBtn.disabled = false;
        }
        
        // Reset AI button and modal if it was used
        const playAIBtn = document.getElementById('playAIBtn');
        if (playAIBtn) {
            playAIBtn.disabled = false;
        }
        closeAIModal();
    });
}

/**
 * Update the rooms list UI with the latest data
 */
function updateRoomsList(rooms) {
    const roomsList = document.getElementById('roomsList');
    const roomsEmpty = document.getElementById('roomsEmpty');
    
    if (!roomsList) return;
    
    // Show empty state if no rooms
    if (!rooms || rooms.length === 0) {
        roomsList.innerHTML = '';
        if (roomsEmpty) {
            roomsEmpty.style.display = 'flex';
        }
        return;
    }
    
    // Hide empty state
    if (roomsEmpty) {
        roomsEmpty.style.display = 'none';
    }
    
    // Build room items HTML
    const roomsHtml = rooms.map((room, index) => `
        <div class="room-item" data-room-code="${escapeHtml(room.room_code)}" style="animation-delay: ${index * 0.05}s">
            <div class="room-info">
                <div class="room-code">${escapeHtml(room.room_code)}</div>
                <div class="room-host">
                    <span class="host-avatar">👤</span>
                    <span class="host-name">${escapeHtml(room.host_name)}</span>
                </div>
            </div>
            <div class="room-players">
                <span class="player-count">
                    <span class="current">${room.players_count}</span>/${room.max_players}
                </span>
                <button class="room-join-btn" onclick="joinRoom('${escapeHtml(room.room_code)}')">
                    Join
                </button>
            </div>
        </div>
    `).join('');
    
    // Check if the rooms have changed to add pulse animation
    const existingRooms = roomsList.querySelectorAll('.room-item');
    const existingCodes = Array.from(existingRooms).map(el => el.dataset.roomCode);
    const newCodes = rooms.map(r => r.room_code);
    const hasNewRoom = newCodes.some(code => !existingCodes.includes(code));
    
    roomsList.innerHTML = roomsHtml;
    
    // Add pulse animation to new rooms
    if (hasNewRoom) {
        rooms.forEach(room => {
            if (!existingCodes.includes(room.room_code)) {
                const roomEl = roomsList.querySelector(`[data-room-code="${room.room_code}"]`);
                if (roomEl) {
                    roomEl.classList.add('pulse-update');
                    setTimeout(() => roomEl.classList.remove('pulse-update'), 500);
                }
            }
        });
    }
}

/**
 * Join a specific room from the room list
 */
function joinRoom(roomCode) {
    const nameInput = document.getElementById('playerNameInput');
    const name = nameInput ? nameInput.value.trim() : '';
    
    if (name) localStorage.setItem('playerName', name);
    sessionStorage.setItem('playerName', name || 'Player');
    
    // Find and disable the join button
    const roomItem = document.querySelector(`[data-room-code="${roomCode}"]`);
    const joinBtn = roomItem?.querySelector('.room-join-btn');
    if (joinBtn) {
        joinBtn.textContent = 'Joining...';
        joinBtn.disabled = true;
    }
    
    // Navigate to the game
    window.location.href = '/game/' + roomCode;
}

// =============================================================================
// AI MODE
// =============================================================================

/**
 * Set up the AI difficulty selection modal
 */
function setupAIModal() {
    const modalOverlay = document.getElementById('aiModalOverlay');
    const modalClose = document.getElementById('aiModalClose');
    const difficultyOptions = document.getElementById('aiDifficultyOptions');
    
    if (!modalOverlay) return;
    
    // Close modal on overlay click
    modalOverlay.addEventListener('click', function(e) {
        if (e.target === modalOverlay) {
            closeAIModal();
        }
    });
    
    // Close modal on close button click
    if (modalClose) {
        modalClose.addEventListener('click', closeAIModal);
    }
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
            closeAIModal();
        }
    });
    
    // Handle difficulty selection
    if (difficultyOptions) {
        difficultyOptions.addEventListener('click', function(e) {
            const difficultyBtn = e.target.closest('.ai-difficulty-btn');
            if (!difficultyBtn) return;
            
            const difficulty = difficultyBtn.dataset.difficulty;
            startAIGame(difficulty);
        });
    }
}

/**
 * Open the AI difficulty selection modal
 */
function openAIModal() {
    const modalOverlay = document.getElementById('aiModalOverlay');
    const difficultyOptions = document.getElementById('aiDifficultyOptions');
    const loadingEl = document.getElementById('aiModalLoading');
    
    if (!modalOverlay) return;
    
    // Reset modal state
    if (difficultyOptions) difficultyOptions.style.display = 'flex';
    if (loadingEl) loadingEl.style.display = 'none';
    
    // Enable all difficulty buttons
    const difficultyBtns = document.querySelectorAll('.ai-difficulty-btn');
    difficultyBtns.forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = '1';
    });
    
    // Show modal
    modalOverlay.classList.add('active');
}

/**
 * Close the AI difficulty selection modal
 */
function closeAIModal() {
    const modalOverlay = document.getElementById('aiModalOverlay');
    if (modalOverlay) {
        modalOverlay.classList.remove('active');
    }
}

/**
 * Start an AI game with the selected difficulty
 * Instead of starting via socket (which gets disconnected on redirect),
 * we store the AI game info and redirect to game page to start there.
 */
function startAIGame(difficulty) {
    console.log('[AI] startAIGame called with difficulty:', difficulty);
    
    if (!difficulty) {
        console.error('[AI] No difficulty provided!');
        return;
    }
    
    const difficultyOptions = document.getElementById('aiDifficultyOptions');
    const loadingEl = document.getElementById('aiModalLoading');
    const playAIBtn = document.getElementById('playAIBtn');
    
    // Show loading state in modal
    if (difficultyOptions) difficultyOptions.style.display = 'none';
    if (loadingEl) loadingEl.style.display = 'flex';
    
    // Disable the AI button
    if (playAIBtn) {
        playAIBtn.disabled = true;
    }
    
    // Get player name
    const nameInput = document.getElementById('playerNameInput');
    const name = nameInput ? nameInput.value.trim() : '';
    
    // Store AI game info in sessionStorage with timestamp for debugging
    const aiGameData = {
        difficulty: difficulty,
        timestamp: Date.now(),
        roomCode: null  // Will be set after generating
    };
    
    // Generate a room code and redirect to game page
    // The game page will detect the AI flag and start the AI game there
    const roomCode = generateRoomCode();
    aiGameData.roomCode = roomCode;
    
    // Store in sessionStorage
    sessionStorage.setItem('aiGameDifficulty', difficulty);
    sessionStorage.setItem('aiGameData', JSON.stringify(aiGameData));
    sessionStorage.setItem('playerName', name || 'Player');
    
    console.log('[AI] Stored in sessionStorage:', aiGameData);
    console.log('[AI] Verification - aiGameDifficulty:', sessionStorage.getItem('aiGameDifficulty'));
    
    const targetUrl = '/game/' + roomCode + '?ai=' + difficulty;
    console.log('[AI] Redirecting to:', targetUrl);
    
    // Use location.assign for clearer navigation
    window.location.assign(targetUrl);
}

/**
 * Handle AI game room joined - extends setupLobbySocketEvents
 */
function setupAIGameSocketEvents() {
    // This is handled in the main room_joined handler
    // AI games redirect to the game page like normal games
}

// =============================================================================
// GAME PAGE
// =============================================================================

function initGamePage() {
    console.log('initGamePage called');
    console.log('Room code:', ROOM_CODE);
    
    playerName = sessionStorage.getItem('playerName') || localStorage.getItem('playerName') || 'Player';
    console.log('Player name:', playerName);
    
    // Check if this is an AI game (from sessionStorage OR URL parameter)
    // SessionStorage is set by startAIGame() on the lobby page before redirect
    // URL parameter is a backup in case sessionStorage fails
    const urlParams = new URLSearchParams(window.location.search);
    const aiFromStorage = sessionStorage.getItem('aiGameDifficulty');
    const aiFromUrl = urlParams.get('ai');
    const aiGameData = sessionStorage.getItem('aiGameData');
    
    // Prefer sessionStorage since it's set right before redirect
    const aiDifficulty = aiFromStorage || aiFromUrl;
    const isAIGame = !!aiDifficulty;
    
    console.log('[AI] ======= AI Game Detection =======');
    console.log('[AI] Full URL:', window.location.href);
    console.log('[AI] URL search string:', window.location.search);
    console.log('[AI] AI from sessionStorage:', aiFromStorage);
    console.log('[AI] AI from URL param:', aiFromUrl);
    console.log('[AI] AI game data:', aiGameData);
    console.log('[AI] Final aiDifficulty:', aiDifficulty);
    console.log('[AI] isAIGame:', isAIGame);
    console.log('[AI] ===================================');
    
    // If URL has ai param but sessionStorage doesn't, something may have gone wrong
    if (aiFromUrl && !aiFromStorage) {
        console.warn('[AI] URL has ai param but sessionStorage is empty - possible cache/redirect issue');
    }
    
    // Clear the AI game flag from sessionStorage after reading
    if (aiFromStorage) {
        sessionStorage.removeItem('aiGameDifficulty');
        sessionStorage.removeItem('aiGameData');
        console.log('[AI] Cleared AI data from sessionStorage');
    }
    
    try {
        setupSocketEvents();
        setupGameControls();
        setupChat();
        setupTooltipGlobalEvents();
        setupPowerButton();
        initSyntaxPreview();
        
        if (isAIGame) {
            // Start AI game - this creates the room with a bot
            console.log('[AI] *** AI GAME MODE DETECTED ***');
            console.log('[AI] Difficulty:', aiDifficulty);
            console.log('[AI] Room code:', ROOM_CODE);
            
            // Show visual feedback that we're in AI mode
            showTurnIndicator(`Starting AI game (${aiDifficulty})...`);
            
            // We need to ensure socket is connected before emitting
            const emitStartAIGame = () => {
                console.log('[AI] Emitting start_ai_game event');
                console.log('[AI] Payload:', { name: playerName, difficulty: aiDifficulty, room_code: ROOM_CODE });
                
                // Get Firebase UID if available
                const firebaseUid = localStorage.getItem('firebaseUid') || sessionStorage.getItem('firebaseUid');
                
                socket.emit('start_ai_game', { 
                    name: playerName, 
                    difficulty: aiDifficulty,
                    room_code: ROOM_CODE,  // Pass the room code from the URL
                    uid: firebaseUid
                });
                
                console.log('[AI] start_ai_game event emitted successfully');
                showNotification('Connecting to AI opponent...', 'info');
            };
            
            // Check connection status and emit appropriately
            if (socket.connected) {
                console.log('[AI] Socket already connected, emitting immediately');
                emitStartAIGame();
            } else {
                console.log('[AI] Socket not connected yet, waiting for connection...');
                // Use a one-time listener for the connect event
                const connectHandler = () => {
                    console.log('[AI] Socket connected, now emitting start_ai_game');
                    emitStartAIGame();
                };
                socket.once('connect', connectHandler);
                
                // Also set a timeout fallback in case connection is delayed
                setTimeout(() => {
                    if (!socket.connected) {
                        console.warn('[AI] Socket connection timeout, retrying...');
                        socket.off('connect', connectHandler);
                        socket.once('connect', emitStartAIGame);
                    }
                }, 3000);
            }
        } else {
            console.log('[AI] Regular game mode (not AI)');
            console.log('[AI] URL had ai param:', aiFromUrl);
            console.log('[AI] SessionStorage had ai:', aiFromStorage);
            // Regular game - join existing room or create new one
            console.log('Emitting join_room event...');
            
            // Get Firebase UID if available
            const firebaseUid = localStorage.getItem('firebaseUid') || sessionStorage.getItem('firebaseUid');
            
            socket.emit('join_room', { 
                room: ROOM_CODE, 
                name: playerName,
                uid: firebaseUid
            });
            console.log('join_room event emitted with uid:', firebaseUid);
        }
    } catch (error) {
        console.error('Error in initGamePage:', error);
    }
    
    // Room code copy
    const roomCodeEl = document.getElementById('roomCode');
    if (roomCodeEl) {
        roomCodeEl.addEventListener('click', function() {
            copyToClipboard(ROOM_CODE);
            showNotification('Room code copied!', 'success');
            
            // Visual feedback
            this.style.transform = 'scale(1.1)';
            setTimeout(() => this.style.transform = '', 200);
        });
    }
    
    if (!isAIGame) {
        showTurnIndicator('Connecting...');
    }
    
    // Add keyboard shortcut hints
    addKeyboardHints();
}

/**
 * Set up global events for tooltip behavior
 */
function setupTooltipGlobalEvents() {
    // Hide tooltip on click elsewhere
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.game-card')) {
            hideCardTooltip();
        }
    });
    
    // Hide tooltip on scroll
    document.addEventListener('scroll', () => {
        hideCardTooltip();
    }, true);
    
    // Hide tooltip on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideCardTooltip();
        }
    });
}

function setupGameControls() {
    const endTurnBtn = document.getElementById('endTurnBtn');
    if (endTurnBtn) {
        endTurnBtn.addEventListener('click', function() {
            if (!this.disabled && isMyTurn) {
                // Add click animation
                this.style.transform = 'scale(0.95)';
                setTimeout(() => this.style.transform = '', 150);
                
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
                } else {
                    // Show shake animation for unplayable card
                    const cardEls = document.querySelectorAll('.your-area .game-card');
                    if (cardEls[idx]) {
                        cardEls[idx].classList.add('shake');
                        setTimeout(() => cardEls[idx].classList.remove('shake'), 400);
                    }
                }
            }
        }
        
        // Space or Enter to end turn
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            if (isMyTurn && (!currentGameState?.playable_cards?.length)) {
                socket.emit('pass_turn', { room: ROOM_CODE });
            }
        }
        
        // C to toggle chat
        if (e.key === 'c' || e.key === 'C') {
            const chatPanel = document.getElementById('chatPanel');
            if (chatPanel) {
                chatPanel.classList.toggle('open');
            }
        }
        
        // P to use power (if available)
        if (e.key === 'p' || e.key === 'P') {
            if (currentGameState?.power_available && currentGameState?.is_your_turn && !powerModalOpen) {
                showPowerModal(currentGameState.powers);
            }
        }
        
        // Escape to close modals or clear insertion selection
        if (e.key === 'Escape') {
            if (powerModalOpen) {
                hidePowerModal();
            } else if (peekModalOpen) {
                hidePeekModal();
            } else if (selectedInsertionIndex !== null) {
                // Clear insertion selection
                resetInsertionSelection();
                showNotification('Insertion point cleared', 'info');
            }
        }
        
        // I key to toggle insertion mode hint
        if (e.key === 'i' || e.key === 'I') {
            if (isMyTurn && currentGameState?.game_started && !currentGameState?.game_over) {
                showNotification('Click + icons between cards to select insertion point', 'info');
            }
        }
    });
}

function addKeyboardHints() {
    // Add subtle keyboard hints to cards
    const style = document.createElement('style');
    style.textContent = `
        .your-area .game-card::before {
            content: attr(data-key);
            position: absolute;
            top: -8px;
            right: -8px;
            width: 18px;
            height: 18px;
            background: var(--bg-primary);
            border: 1px solid var(--text-muted);
            border-radius: 4px;
            font-size: 0.6rem;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 10;
        }
        .your-area:hover .game-card.playable::before {
            opacity: 0.7;
        }
    `;
    document.head.appendChild(style);
}

// =============================================================================
// SOCKET EVENTS
// =============================================================================

function setupSocketEvents() {
    socket.on('room_joined', function(data) {
        console.log('[SOCKET] room_joined received:', data);
        console.log('[SOCKET] is_ai_game:', data.is_ai_game);
        console.log('[SOCKET] waiting_for_opponent:', data.waiting_for_opponent);
        
        // Clean up AI parameter from URL if present
        if (window.location.search.includes('ai=')) {
            const cleanUrl = window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
        }
        
        if (data.is_ai_game) {
            // AI game joined - game should start immediately
            console.log('[SOCKET] AI game confirmed, showing notification');
            showNotification(`Playing against ${data.ai_name || 'AI'}!`, 'success');
        } else if (data.waiting_for_opponent) {
            console.log('[SOCKET] Regular room, waiting for opponent');
            showTurnIndicator('Waiting for opponent...');
            showNotification(`Room ${data.room_code} created! Share this code.`, 'success');
        }
    });
    
    socket.on('player_joined', function(data) {
        showNotification(`${data.player_name} joined!`, 'success');
        // Add a subtle sound-like visual pulse
        pulseElement('.game-board');
    });
    
    socket.on('player_left', function(data) {
        showNotification(data.message, 'warning');
    });
    
    socket.on('game_started', function(data) {
        const message = data.is_ai_game 
            ? `Game started against ${data.ai_name || 'AI'}!` 
            : 'Game starting!';
        showNotification(message, 'success');
        showTurnIndicator('Game Starting!', true);
        
        // Add dramatic entrance effect
        setTimeout(() => {
            document.querySelectorAll('.game-card').forEach((card, i) => {
                card.style.animationDelay = `${i * 0.05}s`;
                card.classList.add('card-enter');
            });
        }, 500);
    });
    
    socket.on('game_state', function(state) {
        console.log('Game state:', state);
        const wasMyTurn = isMyTurn;
        const previousScore = currentGameState?.your_score || 0;
        currentGameState = state;
        
        // Show turn indicator when it becomes your turn
        if (!wasMyTurn && state.is_your_turn && state.game_started && !state.game_over) {
            showTurnIndicator('Your Turn!', true);
            pulseElement('.player-portrait.you');
        }
        
        // Show score popup if score increased
        if (state.your_score > previousScore) {
            const gained = state.your_score - previousScore;
            showScorePopup(gained, true);
        }
        
        updateGameUI(state);
    });
    
    socket.on('card_played', function(data) {
        if (data.player_id !== playerId) {
            showNotification(`${data.player_name} played "${data.card}"`, 'info');
            
            // Show opponent score popup
            if (data.points_earned > 0) {
                showScorePopup(data.points_earned, false);
            }
        }
        
        // Add effect for special cards
        if (data.effect) {
            showSpecialCardEffect(data.effect, data.player_id === playerId);
        }
    });
    
    socket.on('turn_passed', function(data) {
        if (data.player_id !== playerId) {
            showNotification(`${data.player_name} passed${data.drew_card ? ' and drew a card' : ''}`, 'info');
        }
    });
    
    socket.on('chat_message', function(data) {
        addChatMessage(data);
        
        // Show chat bubble notification if chat is closed
        const chatPanel = document.getElementById('chatPanel');
        if (!chatPanel?.classList.contains('open')) {
            const toggle = document.querySelector('.chat-toggle');
            if (toggle) {
                toggle.classList.add('has-message');
                setTimeout(() => toggle.classList.remove('has-message'), 2000);
            }
        }
    });
    
    socket.on('game_over', function(data) {
        showGameOver(data);
    });
    
    socket.on('error', function(data) {
        showNotification(data.message, 'danger');
        
        // Shake the relevant element
        if (data.message.includes('turn')) {
            document.querySelector('.your-area')?.classList.add('shake');
            setTimeout(() => document.querySelector('.your-area')?.classList.remove('shake'), 400);
        }
    });
    
    // Power system events
    socket.on('power_used', function(data) {
        console.log('Power used:', data);
        
        const isPlayer = data.player_id === playerId;
        const powerInfo = data.power_info || {};
        
        // Show power effect animation
        showPowerEffect(data.power, powerInfo.icon || '⚡', data.message, isPlayer);
        
        // Handle specific power effects
        if (data.power === 'peek' && isPlayer && data.data?.peeked_cards) {
            showPeekModal(data.data.peeked_cards);
        }
        
        // Show notification
        if (isPlayer) {
            showNotification(data.message, 'success');
        } else {
            showNotification(`${data.player_name} used ${powerInfo.name || data.power}!`, 'warning');
        }
        
        // Close power modal if open
        hidePowerModal();
    });
}

// =============================================================================
// UI UPDATES
// =============================================================================

function updateGameUI(state) {
    const wasMyTurn = isMyTurn;
    isMyTurn = state.is_your_turn;
    
    // Reset insertion selection when turn changes
    if (wasMyTurn !== state.is_your_turn) {
        resetInsertionSelection();
    }
    
    // Update player portraits with active state
    document.querySelector('.player-portrait.you')?.classList.toggle('active', state.is_your_turn);
    document.querySelector('.player-portrait.opponent')?.classList.toggle('active', !state.is_your_turn && state.game_started);
    
    // Update scores with animation
    updateScore('yourScore', state.your_score);
    updateScore('opponentScore', state.opponent_score);
    
    // Update names
    updateElement('yourName', state.your_name || 'You');
    
    // Update opponent name with AI badge if applicable
    const opponentNameEl = document.getElementById('opponentName');
    if (opponentNameEl) {
        if (state.is_ai_game) {
            opponentNameEl.innerHTML = `${escapeHtml(state.ai_name || state.opponent_name || 'AI')} <span class="ai-badge">🤖 AI</span>`;
            // Update opponent avatar to robot
            const opponentAvatar = document.querySelector('.player-portrait.opponent .portrait-avatar');
            if (opponentAvatar) {
                opponentAvatar.textContent = '🤖';
            }
        } else {
            opponentNameEl.textContent = state.opponent_name || 'Opponent';
        }
    }
    
    // Update turn number
    updateElement('turnNumber', state.turn_number || 1);
    
    // Update deck count
    updateElement('deckCount', state.deck_remaining);
    updateDeckVisual(state.deck_remaining);
    
    // Update progress bars
    updateProgress('yourProgress', state.your_score);
    updateProgress('opponentProgress', state.opponent_score);
    
    // Render hands and played cards
    renderYourHand(state.your_hand || [], state.playable_cards || []);
    renderOpponentHand(state.opponent_card_count || 0);
    renderPlayedCards(state.played_cards || [], state.syntax_info);
    
    // Update end turn button
    updateEndTurnButton(state);
    
    // Update last card hint
    updateLastCardHint(state.played_cards);
    
    // Store played cards count for animation detection
    lastPlayedCardsCount = state.played_cards?.length || 0;
    
    // Update power system UI
    updatePowerUI(state);
    
    // Update syntax preview panel with server-side validation info
    updateSyntaxPreview(state.played_cards, state.syntax_info);
}

function updateScore(id, value) {
    const el = document.getElementById(id);
    if (el) {
        const currentValue = parseInt(el.textContent) || 0;
        if (currentValue !== value) {
            // Animate counting up
            animateValue(el, currentValue, value, 300);
            el.classList.add('score-updated');
            setTimeout(() => el.classList.remove('score-updated'), 500);
        }
    }
}

function animateValue(el, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // Ease out cubic
        
        el.textContent = Math.round(start + (range * eased));
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) {
        const newValue = String(value);
        if (el.textContent !== newValue) {
            el.textContent = newValue;
        }
    }
}

function updateProgress(id, score) {
    const el = document.getElementById(id);
    const progressLabel = document.querySelector('.progress-label');
    
    if (el) {
        // Calculate progress based on relative scores (who's winning)
        const yourScore = currentGameState?.your_score || 0;
        const opponentScore = currentGameState?.opponent_score || 0;
        const totalScore = yourScore + opponentScore;
        
        let percent;
        if (totalScore === 0) {
            percent = 50; // Equal at start
        } else {
            percent = (score / Math.max(totalScore, 1)) * 100;
        }
        
        el.style.width = Math.min(100, percent) + '%';
        
        // Add glow effect when winning
        if (percent > 60) {
            el.style.filter = 'brightness(1.2)';
        } else {
            el.style.filter = '';
        }
    }
    
    // Update the progress label to show deck remaining
    if (progressLabel && currentGameState) {
        progressLabel.textContent = `${currentGameState.deck_remaining || 0} cards left`;
    }
}

function updateDeckVisual(remaining) {
    const deckCards = document.querySelectorAll('.deck-card');
    const deckDisplay = document.querySelector('.deck-display');
    const deckCount = document.getElementById('deckCount');
    
    deckCards.forEach((card, i) => {
        if (remaining <= i * 10) {
            card.style.opacity = '0.3';
        } else {
            card.style.opacity = '1';
        }
    });
    
    // Add warning visual when deck is low
    if (deckDisplay) {
        if (remaining <= 10 && remaining > 0) {
            deckDisplay.classList.add('deck-low');
            if (deckCount) {
                deckCount.style.color = 'var(--accent-red)';
            }
        } else if (remaining === 0) {
            deckDisplay.classList.add('deck-empty');
        } else {
            deckDisplay.classList.remove('deck-low', 'deck-empty');
            if (deckCount) {
                deckCount.style.color = '';
            }
        }
    }
    
    // Show low deck notification once
    if (remaining === 10 && !window.lowDeckWarningShown) {
        showNotification('⚠️ Only 10 cards left in deck!', 'warning');
        window.lowDeckWarningShown = true;
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
    
    // Don't overwrite if in insertion mode
    if (selectedInsertionIndex !== null) {
        return;
    }
    
    el.classList.remove('insertion-mode');
    
    if (!playedCards?.length) {
        el.innerHTML = 'Any starting card is valid';
    } else {
        const lastCard = playedCards[playedCards.length - 1];
        const info = cardData[lastCard];
        if (info) {
            const catName = categoryNames[info.category] || info.category;
            // Add insertion hint if it's player's turn
            let hintText = `Last: ${lastCard} (${catName})`;
            if (isMyTurn && currentGameState?.game_started && !currentGameState?.game_over) {
                hintText += ' <span class="insertion-tip">• Click + to insert</span>';
            }
            el.innerHTML = hintText;
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
        container.innerHTML = '<div class="empty-sequence">No cards in hand</div>';
        return;
    }
    
    container.innerHTML = hand.map((cardName, i) => {
        const card = cardData[cardName] || { category: 'SPECIAL', points: 0 };
        const categoryClass = categoryClasses[card.category] || 'special';
        const catName = categoryNames[card.category] || 'Special';
        const isPlayable = playableCards.includes(cardName);
        const playableClass = isPlayable && isMyTurn ? 'playable' : 'disabled';
        
        return `
            <div class="game-card ${categoryClass} ${playableClass} card-enter"
                 data-card="${escapeHtml(cardName)}"
                 data-key="${i + 1}"
                 onclick="playCard('${escapeHtml(cardName)}')"
                 onmouseenter="highlightInsertionPoint(true)"
                 onmouseleave="highlightInsertionPoint(false)"
                 style="animation-delay: ${i * 0.03}s">
                <span class="card-category">${catName}</span>
                <span class="card-name">${escapeHtml(cardName)}</span>
                <span class="card-points">${card.points}pt</span>
            </div>
        `;
    }).join('');
    
    // Attach tooltip events to each card
    container.querySelectorAll('.game-card').forEach(cardEl => {
        const cardName = cardEl.dataset.card;
        if (cardName) {
            initCardTooltip(cardEl, cardName);
        }
    });
}

/**
 * Highlight the selected or default insertion point when hovering cards
 */
function highlightInsertionPoint(highlight) {
    const playedCards = currentGameState?.played_cards || [];
    const targetIndex = selectedInsertionIndex !== null ? selectedInsertionIndex : playedCards.length;
    const insertionPoint = document.querySelector(`.insertion-point[data-index="${targetIndex}"]`);
    
    if (insertionPoint) {
        insertionPoint.classList.toggle('highlighting', highlight);
    }
}

function renderOpponentHand(count) {
    const container = document.getElementById('opponentCards');
    if (!container) return;
    
    if (count === 0) {
        container.innerHTML = '<div class="empty-sequence">No cards</div>';
        return;
    }
    
    // Only re-render if count changed
    const currentCount = container.querySelectorAll('.game-card').length;
    if (currentCount === count) return;
    
    container.innerHTML = Array(count).fill(0).map((_, i) => `
        <div class="game-card face-down" style="animation-delay: ${i * 0.02}s"></div>
    `).join('');
}

function renderPlayedCards(playedCards, syntaxInfo = null) {
    const container = document.getElementById('playedCards');
    const statusEl = document.getElementById('mainSyntaxStatus');
    const structureEl = document.getElementById('mainCodeStructure');
    
    if (!container) return;
    
    // Render interactive card sequence with insertion points
    const cardSequenceHtml = renderCardSequenceWithInsertions(playedCards || []);
    
    // Also render the code preview below
    let codeStr = '';
    if (playedCards && playedCards.length > 0) {
        if (syntaxInfo && syntaxInfo.formatted_code) {
            codeStr = syntaxInfo.formatted_code;
        } else {
            codeStr = buildPythonCodeForMain(playedCards);
        }
    }
    
    const codePreviewHtml = codeStr ? `
        <div class="code-preview-section">
            <div class="code-preview-label">Python Output:</div>
            <pre class="code-preview-text">${escapeHtml(codeStr)}</pre>
        </div>
    ` : '';
    
    container.innerHTML = cardSequenceHtml + codePreviewHtml;
    
    // Update syntax status
    if (statusEl && syntaxInfo) {
        if (syntaxInfo.is_complete) {
            statusEl.innerHTML = '<span class="status-icon">✓</span> Valid';
            statusEl.className = 'syntax-status main-status valid';
        } else if (syntaxInfo.is_valid_python) {
            statusEl.innerHTML = '<span class="status-icon">⋯</span> Building';
            statusEl.className = 'syntax-status main-status incomplete';
        } else {
            statusEl.innerHTML = '<span class="status-icon">✗</span> Error';
            statusEl.className = 'syntax-status main-status error';
        }
    }
    
    // Update structure badges
    if (structureEl && syntaxInfo && syntaxInfo.code_structure) {
        const struct = syntaxInfo.code_structure;
        const badges = [];
        if (struct.has_loop) badges.push('<span class="struct-badge loop">Loop</span>');
        if (struct.has_condition) badges.push('<span class="struct-badge condition">Condition</span>');
        if (struct.statements > 1) badges.push(`<span class="struct-badge">${struct.statements} lines</span>`);
        structureEl.innerHTML = badges.join('');
    }
}

/**
 * Render the card sequence with clickable insertion points between cards
 */
function renderCardSequenceWithInsertions(playedCards) {
    if (!playedCards || playedCards.length === 0) {
        // Show initial insertion point when no cards played
        return `
            <div class="card-sequence-container">
                <div class="card-sequence empty-sequence">
                    ${createInsertionPointHtml(0)}
                    <span class="empty-hint">Click + to insert, or play a card</span>
                </div>
            </div>
        `;
    }
    
    // Build sequence with insertion points between each card
    let sequenceHtml = '<div class="card-sequence-container"><div class="card-sequence">';
    
    // Add insertion point at the beginning
    sequenceHtml += createInsertionPointHtml(0);
    
    // Add each played card with an insertion point after it
    playedCards.forEach((cardName, index) => {
        const card = cardData[cardName] || { category: 'SPECIAL', points: 0 };
        const categoryClass = categoryClasses[card.category] || 'special';
        const catName = categoryNames[card.category] || 'Special';
        
        sequenceHtml += `
            <div class="played-card ${categoryClass}" 
                 data-card="${escapeHtml(cardName)}"
                 data-index="${index}"
                 title="${escapeHtml(card.description || cardName)}">
                <span class="played-card-name">${escapeHtml(cardName)}</span>
            </div>
        `;
        
        // Add insertion point after each card
        sequenceHtml += createInsertionPointHtml(index + 1);
    });
    
    sequenceHtml += '</div></div>';
    
    return sequenceHtml;
}

/**
 * Build Python code for main display (fallback when no server info)
 */
function buildPythonCodeForMain(playedCards) {
    // Filter out special cards
    const codeCards = playedCards.filter(c => cardData[c] && cardData[c].category !== 'SPECIAL');
    
    if (!codeCards.length) return '';
    
    let code = '';
    let indentLevel = 0;
    let needsNewLine = false;
    
    for (let i = 0; i < codeCards.length; i++) {
        const cardName = codeCards[i];
        const card = cardData[cardName] || {};
        const category = card.category || '';
        
        // New line after colon
        if (needsNewLine) {
            code += '\n' + '    '.repeat(indentLevel);
            needsNewLine = false;
        }
        
        // Add spacing
        if (i > 0) {
            const prevCard = codeCards[i - 1];
            const prevData = cardData[prevCard] || {};
            const prevCat = prevData.category || '';
            
            let needsSpace = true;
            if (prevCat === 'SYNTAX_OPEN') needsSpace = false;
            if (category === 'SYNTAX_CLOSE') needsSpace = false;
            if (category === 'SYNTAX_COLON') needsSpace = false;
            if (prevCat === 'FUNCTION' && category === 'SYNTAX_OPEN') needsSpace = false;
            
            if (needsSpace) code += ' ';
        }
        
        code += cardName;
        
        // After colon, increase indent
        if (category === 'SYNTAX_COLON') {
            indentLevel++;
            needsNewLine = true;
        }
    }
    
    return code;
}

/**
 * Render the main code editor display
 */
function renderMainCodeEditor(code, syntaxInfo) {
    if (!code || !code.trim()) {
        return `
            <div class="code-editor main-editor">
                <div class="code-line empty-line">
                    <span class="line-number">1</span>
                    <span class="line-content"><span class="code-comment"># Play a card to start coding...</span></span>
                </div>
            </div>
        `;
    }
    
    // Split into lines
    const lines = code.split('\n');
    
    // Build HTML for each line
    const linesHtml = lines.map((line, index) => {
        const lineNum = index + 1;
        const highlightedLine = highlightPythonLine(line);
        const isLastLine = index === lines.length - 1;
        
        return `
            <div class="code-line${isLastLine ? ' current-line' : ''}">
                <span class="line-number">${lineNum}</span>
                <span class="line-content">${highlightedLine}${isLastLine ? '<span class="cursor">|</span>' : ''}</span>
            </div>
        `;
    }).join('');
    
    return `<div class="code-editor main-editor">${linesHtml}</div>`;
}

/**
 * Create HTML for an insertion point indicator
 */
function createInsertionPointHtml(index) {
    const isSelected = selectedInsertionIndex === index;
    const isDefault = selectedInsertionIndex === null && index === (currentGameState?.played_cards?.length || 0);
    
    return `
        <div class="insertion-point ${isSelected ? 'selected' : ''} ${isDefault ? 'default' : ''}" 
             data-index="${index}" 
             onclick="selectInsertionPoint(${index})"
             title="Insert card at position ${index}">
            <span class="insertion-indicator">+</span>
        </div>
    `;
}

/**
 * Select an insertion point in the played cards sequence
 */
function selectInsertionPoint(index) {
    // Toggle selection - clicking same point deselects it
    if (selectedInsertionIndex === index) {
        selectedInsertionIndex = null;
    } else {
        selectedInsertionIndex = index;
    }
    
    // Update visual states
    document.querySelectorAll('.insertion-point').forEach(el => {
        const elIndex = parseInt(el.dataset.index);
        el.classList.toggle('selected', elIndex === selectedInsertionIndex);
        el.classList.toggle('default', selectedInsertionIndex === null && 
            elIndex === (currentGameState?.played_cards?.length || 0));
    });
    
    // Update which cards are playable at this position
    updatePlayableCardsForPosition();
    
    // Show notification about selection
    if (selectedInsertionIndex !== null) {
        showInsertionPositionHint(index);
    }
}

/**
 * Show hint about the selected insertion position
 */
function showInsertionPositionHint(index) {
    const playedCards = currentGameState?.played_cards || [];
    let hint = '';
    
    if (index === 0) {
        hint = 'Selected: Insert at the beginning';
    } else if (index >= playedCards.length) {
        hint = 'Selected: Append to end';
    } else {
        const beforeCard = playedCards[index - 1] || 'start';
        const afterCard = playedCards[index] || 'end';
        hint = `Selected: Insert between "${beforeCard}" and "${afterCard}"`;
    }
    
    // Update the hint display
    const hintEl = document.getElementById('lastCardHint');
    if (hintEl) {
        hintEl.innerHTML = `<span class="insertion-hint">${hint}</span>`;
        hintEl.classList.add('insertion-mode');
    }
}

/**
 * Update which cards are marked as playable based on insertion position
 */
async function updatePlayableCardsForPosition() {
    if (!currentGameState?.your_hand || !isMyTurn) return;
    
    const hand = currentGameState.your_hand;
    const playedCards = currentGameState.played_cards || [];
    const insertIndex = selectedInsertionIndex !== null ? selectedInsertionIndex : playedCards.length;
    
    // If inserting at end, use existing playable_cards
    if (insertIndex === playedCards.length) {
        document.querySelectorAll('.your-area .game-card').forEach(cardEl => {
            const cardName = cardEl.dataset.card;
            if (!cardName) return;
            const isPlayable = currentGameState.playable_cards?.includes(cardName);
            cardEl.classList.toggle('playable', isPlayable && isMyTurn);
            cardEl.classList.toggle('disabled', !isPlayable || !isMyTurn);
        });
        // Store current playable cards for this position
        currentPlayableAtPosition = currentGameState.playable_cards || [];
        return;
    }
    
    // For other positions, call the API
    try {
        const response = await fetch('/api/playable-at-position', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hand: hand,
                played_cards: playedCards,
                position: insertIndex,
                last_was_wild: currentGameState.last_was_wild || false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const playableAtPos = data.playable_cards || [];
            currentPlayableAtPosition = playableAtPos;
            
            // Update card visuals
            document.querySelectorAll('.your-area .game-card').forEach(cardEl => {
                const cardName = cardEl.dataset.card;
                if (!cardName) return;
                const isPlayable = playableAtPos.includes(cardName);
                cardEl.classList.toggle('playable', isPlayable && isMyTurn);
                cardEl.classList.toggle('disabled', !isPlayable || !isMyTurn);
            });
        }
    } catch (err) {
        console.error('Error checking playable cards at position:', err);
        // Fall back to default playable cards
        currentPlayableAtPosition = currentGameState.playable_cards || [];
    }
}

/**
 * Update insertion point visual states
 */
function updateInsertionPointStates() {
    document.querySelectorAll('.insertion-point').forEach(el => {
        const index = parseInt(el.dataset.index);
        const isSelected = selectedInsertionIndex === index;
        const isDefault = selectedInsertionIndex === null && 
            index === (currentGameState?.played_cards?.length || 0);
        
        el.classList.toggle('selected', isSelected);
        el.classList.toggle('default', isDefault);
    });
}

// =============================================================================
// CARD PLAYING
// =============================================================================

function playCard(cardName) {
    if (isAnimating || !isMyTurn) {
        console.log('playCard blocked:', { isAnimating, isMyTurn });
        return;
    }
    
    // Check against position-aware playable cards
    const playableCards = currentPlayableAtPosition.length > 0 
        ? currentPlayableAtPosition 
        : (currentGameState?.playable_cards || []);
    
    if (!playableCards.includes(cardName)) {
        showNotification("Can't play that card at this position", 'warning');
        const cardEl = document.querySelector(`.your-area [data-card="${CSS.escape(cardName)}"]`);
        if (cardEl) {
            cardEl.classList.add('shake');
            setTimeout(() => cardEl.classList.remove('shake'), 400);
        }
        return;
    }
    
    console.log('Playing card:', cardName, 'at position:', selectedInsertionIndex);
    
    // Try to animate, but don't let animation errors block the play
    try {
        const cardEl = document.querySelector(`.your-area [data-card="${CSS.escape(cardName)}"]`);
        if (cardEl) {
            animateCardPlay(cardEl);
        }
    } catch (err) {
        console.warn('Animation error (card still plays):', err);
        isAnimating = false;
    }
    
    // Determine the insertion position
    const playedCards = currentGameState?.played_cards || [];
    const position = selectedInsertionIndex !== null ? selectedInsertionIndex : playedCards.length;
    
    // Emit the play_card event with position
    socket.emit('play_card', { 
        room: ROOM_CODE, 
        card: cardName,
        position: position
    });
    
    // Reset insertion selection after playing
    resetInsertionSelection();
}

/**
 * Reset the insertion point selection
 */
function resetInsertionSelection() {
    selectedInsertionIndex = null;
    selectedCardFromHand = null;
    currentPlayableAtPosition = currentGameState?.playable_cards || [];
    
    // Update visual states
    document.querySelectorAll('.insertion-point').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Reset hint display
    const hintEl = document.getElementById('lastCardHint');
    if (hintEl) {
        hintEl.classList.remove('insertion-mode');
    }
    
    // Reset card playability to default (end of sequence)
    document.querySelectorAll('.your-area .game-card').forEach(cardEl => {
        const cardName = cardEl.dataset.card;
        if (!cardName) return;
        const isPlayable = currentGameState?.playable_cards?.includes(cardName);
        cardEl.classList.toggle('playable', isPlayable && isMyTurn);
        cardEl.classList.toggle('disabled', !isPlayable || !isMyTurn);
    });
}

function animateCardPlay(cardEl) {
    isAnimating = true;
    
    const rect = cardEl.getBoundingClientRect();
    const playZone = document.querySelector('.play-zone') || document.getElementById('playedCards');
    
    // If there's a selected insertion point, animate towards it
    let targetEl = null;
    if (selectedInsertionIndex !== null) {
        targetEl = document.querySelector(`.insertion-point[data-index="${selectedInsertionIndex}"]`);
    }
    
    // Fallback if play zone not found
    if (!playZone && !targetEl) {
        console.warn('Play zone not found, skipping animation');
        isAnimating = false;
        return;
    }
    
    const playRect = targetEl ? targetEl.getBoundingClientRect() : playZone.getBoundingClientRect();
    
    // Create flying card clone
    const clone = cardEl.cloneNode(true);
    clone.classList.remove('playable', 'disabled', 'shake');
    clone.style.cssText = `
        position: fixed;
        left: ${rect.left}px;
        top: ${rect.top}px;
        width: ${rect.width}px;
        height: ${rect.height}px;
        z-index: 1000;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        pointer-events: none;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    `;
    document.body.appendChild(clone);
    
    // Hide original
    cardEl.style.opacity = '0';
    cardEl.style.transform = 'scale(0.5)';
    
    // Create particle trail
    createCardTrail(rect.left + rect.width/2, rect.top + rect.height/2);
    
    // Animate to play zone
    requestAnimationFrame(() => {
        clone.style.left = `${playRect.left + playRect.width/2 - rect.width/2}px`;
        clone.style.top = `${playRect.top + playRect.height/2 - rect.height/2}px`;
        clone.style.transform = 'scale(1.2) rotate(5deg)';
    });
    
    // Impact effect
    setTimeout(() => {
        clone.style.transform = 'scale(0.8)';
        clone.style.opacity = '0';
        
        // Create impact particles
        createImpactParticles(
            playRect.left + playRect.width/2,
            playRect.top + playRect.height/2
        );
    }, 350);
    
    setTimeout(() => {
        clone.remove();
        isAnimating = false;
    }, 450);
}

function createCardTrail(x, y) {
    for (let i = 0; i < 5; i++) {
        setTimeout(() => {
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: fixed;
                left: ${x}px;
                top: ${y}px;
                width: 8px;
                height: 8px;
                background: var(--accent-green);
                border-radius: 50%;
                pointer-events: none;
                z-index: 999;
                opacity: 0.8;
                transform: translate(-50%, -50%);
                animation: trailFade 0.5s ease-out forwards;
            `;
            document.body.appendChild(particle);
            setTimeout(() => particle.remove(), 500);
        }, i * 30);
    }
}

function createImpactParticles(x, y) {
    const colors = ['#4ade80', '#4a9eff', '#d4a84b'];
    for (let i = 0; i < 12; i++) {
        const particle = document.createElement('div');
        const angle = (i / 12) * Math.PI * 2;
        const velocity = 50 + Math.random() * 30;
        
        particle.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            width: 6px;
            height: 6px;
            background: ${colors[i % colors.length]};
            border-radius: 50%;
            pointer-events: none;
            z-index: 1000;
            transform: translate(-50%, -50%);
        `;
        document.body.appendChild(particle);
        
        // Animate outward
        const targetX = x + Math.cos(angle) * velocity;
        const targetY = y + Math.sin(angle) * velocity;
        
        particle.animate([
            { left: `${x}px`, top: `${y}px`, opacity: 1, transform: 'translate(-50%, -50%) scale(1)' },
            { left: `${targetX}px`, top: `${targetY}px`, opacity: 0, transform: 'translate(-50%, -50%) scale(0.3)' }
        ], {
            duration: 400,
            easing: 'ease-out'
        });
        
        setTimeout(() => particle.remove(), 400);
    }
}

// Add CSS for trail animation
const trailStyle = document.createElement('style');
trailStyle.textContent = `
    @keyframes trailFade {
        to {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.3);
        }
    }
`;
document.head.appendChild(trailStyle);

// =============================================================================
// SPECIAL EFFECTS
// =============================================================================

function showSpecialCardEffect(effect, isPlayer) {
    const messages = {
        'draw_2': { text: 'Draw 2!', icon: '🃏' },
        'discard_2': { text: 'Discard 2!', icon: '💨' },
        'skip': { text: 'Skip!', icon: '⏭️' },
        'wild': { text: 'Wild!', icon: '🌟' }
    };
    
    const effectData = messages[effect];
    if (!effectData) return;
    
    const effectEl = document.createElement('div');
    effectEl.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0);
        font-size: 3rem;
        font-weight: 800;
        color: ${isPlayer ? 'var(--accent-green)' : 'var(--accent-red)'};
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        z-index: 1000;
        pointer-events: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
    `;
    effectEl.innerHTML = `
        <span style="font-size: 4rem;">${effectData.icon}</span>
        <span>${effectData.text}</span>
    `;
    document.body.appendChild(effectEl);
    
    effectEl.animate([
        { transform: 'translate(-50%, -50%) scale(0)', opacity: 0 },
        { transform: 'translate(-50%, -50%) scale(1.2)', opacity: 1, offset: 0.3 },
        { transform: 'translate(-50%, -50%) scale(1)', opacity: 1, offset: 0.5 },
        { transform: 'translate(-50%, -50%) scale(1)', opacity: 1, offset: 0.8 },
        { transform: 'translate(-50%, -50%) scale(0.8)', opacity: 0 }
    ], {
        duration: 1500,
        easing: 'ease-out'
    });
    
    setTimeout(() => effectEl.remove(), 1500);
}

function showScorePopup(points, isPlayer) {
    const targetEl = document.getElementById(isPlayer ? 'yourScore' : 'opponentScore');
    if (!targetEl) return;
    
    const rect = targetEl.getBoundingClientRect();
    
    const popup = document.createElement('div');
    popup.style.cssText = `
        position: fixed;
        left: ${rect.left + rect.width/2}px;
        top: ${rect.top}px;
        transform: translateX(-50%);
        font-size: 1.5rem;
        font-weight: 700;
        color: ${isPlayer ? 'var(--accent-green)' : 'var(--accent-red)'};
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
        z-index: 100;
        pointer-events: none;
    `;
    popup.textContent = `+${points}`;
    document.body.appendChild(popup);
    
    popup.animate([
        { transform: 'translateX(-50%) translateY(0)', opacity: 1 },
        { transform: 'translateX(-50%) translateY(-40px)', opacity: 0 }
    ], {
        duration: 1000,
        easing: 'ease-out'
    });
    
    setTimeout(() => popup.remove(), 1000);
}

function pulseElement(selector) {
    const el = document.querySelector(selector);
    if (!el) return;
    
    el.animate([
        { transform: 'scale(1)' },
        { transform: 'scale(1.05)' },
        { transform: 'scale(1)' }
    ], {
        duration: 300,
        easing: 'ease-in-out'
    });
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
        setTimeout(() => indicator.classList.remove('visible'), 2500);
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
    
    // Auto remove
    setTimeout(() => {
        notif.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => notif.remove(), 300);
    }, 3500);
    
    // Click to dismiss
    notif.addEventListener('click', () => {
        notif.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => notif.remove(), 300);
    });
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
            <input type="text" id="chatInput" placeholder="Message... (Press C)" maxlength="200">
            <button onclick="sendChat()">Send</button>
        </div>
    `;
    
    document.body.appendChild(toggle);
    document.body.appendChild(panel);
    
    document.getElementById('chatInput').addEventListener('keypress', e => {
        if (e.key === 'Enter') sendChat();
    });
    
    // Add has-message animation style
    const style = document.createElement('style');
    style.textContent = `
        .chat-toggle.has-message {
            animation: chatBounce 0.5s ease infinite;
        }
        @keyframes chatBounce {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
    `;
    document.head.appendChild(style);
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
        const yourScore = data.scores[playerId] || 0;
        const opponentScore = Object.entries(data.scores)
            .filter(([id]) => id !== playerId)
            .map(([, score]) => score)[0] || 0;
        scoresEl.textContent = `You: ${yourScore} | Opponent: ${opponentScore}`;
    }
    
    if (reasonEl) {
        const reasons = {
            'win_condition': 'Deck depleted - Highest score wins!',
            'too_many_passes': 'Opponent could not play',
            'opponent_disconnected': 'Opponent disconnected'
        };
        reasonEl.textContent = reasons[data.reason] || '';
    }
    
    // Populate final code preview
    populateFinalCodePreview();
    
    // Populate game stats
    populateGameStats();
    
    // Populate learned concepts
    populateLearnedConcepts();
    
    // Setup share button
    setupShareButton();
    
    // Delay modal slightly for dramatic effect
    setTimeout(() => {
        if (modal) {
            new bootstrap.Modal(modal).show();
        }
        
        if (isWinner) {
            createConfetti();
        } else {
            createDefeatEffect();
        }
    }, 500);
}

/**
 * Populate the final code preview in game over modal
 */
function populateFinalCodePreview() {
    const codeBlock = document.getElementById('finalCodeBlock');
    if (!codeBlock || !currentGameState?.played_cards) return;
    
    const playedCards = currentGameState.played_cards.filter(card => {
        const cardInfo = cardData[card];
        return cardInfo && cardInfo.category !== 'SPECIAL';
    });
    
    if (playedCards.length === 0) {
        document.getElementById('finalCodeSection').style.display = 'none';
        return;
    }
    
    const codeStr = buildPythonCode(currentGameState.played_cards);
    // Remove the cursor from final code
    const finalCode = codeStr.replace(' █', '').replace('█', '');
    const highlighted = highlightPythonSyntaxForPreview(finalCode, currentGameState.played_cards);
    // Remove cursor span
    codeBlock.innerHTML = `<code>${highlighted.replace(/<span class="code-cursor">█<\/span>/, '')}</code>`;
}

/**
 * Populate game statistics
 */
function populateGameStats() {
    const cardsPlayedEl = document.getElementById('statCardsPlayed');
    const turnsEl = document.getElementById('statTurns');
    const deckRemainingEl = document.getElementById('statDeckRemaining');
    
    if (currentGameState) {
        if (cardsPlayedEl) {
            const nonSpecialCards = (currentGameState.played_cards || []).filter(card => {
                const cardInfo = cardData[card];
                return cardInfo && cardInfo.category !== 'SPECIAL';
            });
            cardsPlayedEl.textContent = nonSpecialCards.length;
        }
        if (turnsEl) turnsEl.textContent = currentGameState.turn_number || 0;
        if (deckRemainingEl) deckRemainingEl.textContent = currentGameState.deck_remaining || 0;
    }
}

/**
 * Populate learned concepts badges
 */
function populateLearnedConcepts() {
    const learnedSection = document.getElementById('learnedSection');
    const badgesContainer = document.getElementById('learnedBadges');
    
    if (!learnedSection || !badgesContainer || !currentGameState?.played_cards) return;
    
    // Get unique categories used
    const categoriesUsed = new Set();
    const categoryDisplayNames = {
        'LOOP': 'Loops',
        'VARIABLE': 'Variables',
        'KEYWORD': 'Keywords',
        'FUNCTION': 'Functions',
        'VALUE': 'Values',
        'OPERATOR': 'Operators',
        'SYNTAX_OPEN': 'Syntax',
        'SYNTAX_CLOSE': 'Syntax',
        'SYNTAX_COLON': 'Syntax'
    };
    
    currentGameState.played_cards.forEach(card => {
        const cardInfo = cardData[card];
        if (cardInfo && cardInfo.category !== 'SPECIAL') {
            const displayName = categoryDisplayNames[cardInfo.category];
            if (displayName) {
                categoriesUsed.add(displayName);
            }
        }
    });
    
    if (categoriesUsed.size === 0) {
        learnedSection.style.display = 'none';
        return;
    }
    
    const categoryClasses = {
        'Loops': 'loop',
        'Variables': 'variable',
        'Keywords': 'keyword',
        'Functions': 'function',
        'Values': 'value',
        'Operators': 'operator',
        'Syntax': 'syntax'
    };
    
    let badgesHtml = '';
    let delay = 0;
    categoriesUsed.forEach(category => {
        const cssClass = categoryClasses[category] || 'keyword';
        badgesHtml += `<span class="learned-badge ${cssClass}" style="animation-delay: ${delay}s">${category}</span>`;
        delay += 0.1;
    });
    
    badgesContainer.innerHTML = badgesHtml;
    learnedSection.style.display = 'block';
}

/**
 * Setup share button functionality
 */
function setupShareButton() {
    const shareBtn = document.getElementById('shareResultBtn');
    if (!shareBtn) return;
    
    shareBtn.onclick = async () => {
        const yourScore = currentGameState?.your_score || 0;
        const opponentScore = currentGameState?.opponent_score || 0;
        const isWinner = currentGameState?.winner === playerId;
        
        const shareText = `🐍 Python Card Game Result:\n${isWinner ? '🏆 Victory!' : '😔 Defeat'}\nScore: ${yourScore} - ${opponentScore}\n\nPlay at: ${window.location.origin}`;
        
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Python Card Game Result',
                    text: shareText,
                    url: window.location.origin
                });
            } catch (err) {
                // User cancelled or share failed
                copyToClipboard(shareText);
                showNotification('Result copied to clipboard!', 'success');
            }
        } else {
            copyToClipboard(shareText);
            showNotification('Result copied to clipboard!', 'success');
        }
    };
}

function createConfetti() {
    const colors = ['#4ade80', '#4a9eff', '#d4a84b', '#a78bfa', '#f87171', '#22d3ee'];
    for (let i = 0; i < 100; i++) {
        setTimeout(() => {
            const conf = document.createElement('div');
            const size = 6 + Math.random() * 8;
            const isSquare = Math.random() > 0.5;
            
            conf.style.cssText = `
                position: fixed;
                width: ${size}px;
                height: ${isSquare ? size : size * 0.4}px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                left: ${Math.random() * 100}vw;
                top: -20px;
                z-index: 10000;
                pointer-events: none;
                border-radius: ${isSquare ? '2px' : '0'};
            `;
            document.body.appendChild(conf);
            
            conf.animate([
                { top: '-20px', transform: 'rotate(0deg)', opacity: 1 },
                { top: '100vh', transform: `rotate(${360 + Math.random() * 360}deg)`, opacity: 0.7 }
            ], {
                duration: 2500 + Math.random() * 1500,
                easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
            });
            
            setTimeout(() => conf.remove(), 4000);
        }, i * 30);
    }
}

function createDefeatEffect() {
    // Subtle grey overlay effect
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        inset: 0;
        background: radial-gradient(circle, transparent 30%, rgba(0, 0, 0, 0.3) 100%);
        z-index: 9999;
        pointer-events: none;
        animation: defeatFade 1s ease-out forwards;
    `;
    document.body.appendChild(overlay);
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes defeatFade {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    setTimeout(() => overlay.remove(), 5000);
}

// =============================================================================
// CARD TOOLTIP SYSTEM
// =============================================================================

/**
 * Initialize tooltip events for a card element
 */
function initCardTooltip(cardEl, cardName) {
    cardEl.addEventListener('mouseenter', (e) => {
        clearTimeout(tooltipTimeout);
        tooltipTimeout = setTimeout(() => {
            showCardTooltip(cardName, e);
        }, TOOLTIP_DELAY);
    });
    
    cardEl.addEventListener('mousemove', (e) => {
        if (tooltipVisible) {
            positionTooltip(e);
        }
    });
    
    cardEl.addEventListener('mouseleave', () => {
        clearTimeout(tooltipTimeout);
        hideCardTooltip();
    });
    
    // Touch support for mobile
    cardEl.addEventListener('touchstart', (e) => {
        // Toggle tooltip on touch
        if (tooltipVisible) {
            hideCardTooltip();
        } else {
            showCardTooltip(cardName, e.touches[0]);
        }
    }, { passive: true });
}

/**
 * Show the card tooltip with Python tips
 */
function showCardTooltip(cardName, event) {
    const tooltip = document.getElementById('cardTooltip');
    const card = cardData[cardName];
    
    if (!tooltip || !card) return;
    
    // Update tooltip content
    const nameEl = document.getElementById('tooltipCardName');
    const categoryEl = document.getElementById('tooltipCategory');
    const pointsEl = document.getElementById('tooltipPoints');
    const tipEl = document.getElementById('tooltipTip');
    const exampleEl = document.getElementById('tooltipExample');
    const statusEl = document.getElementById('tooltipStatus');
    const reasonEl = document.getElementById('tooltipReason');
    
    if (nameEl) nameEl.textContent = cardName;
    if (categoryEl) categoryEl.textContent = getCategoryDisplayName(card.category);
    if (pointsEl) pointsEl.textContent = `${card.points}pt`;
    
    // Python tip
    if (tipEl) {
        tipEl.textContent = card.python_tip || card.description || 'No description available.';
    }
    
    // Code example with syntax highlighting
    if (exampleEl) {
        const example = card.example || '';
        exampleEl.innerHTML = highlightPythonSyntax(example);
    }
    
    // Playability status
    const isPlayable = currentGameState?.playable_cards?.includes(cardName);
    const isYourTurn = currentGameState?.is_your_turn;
    
    if (statusEl) {
        statusEl.className = 'tooltip-status ' + (isPlayable && isYourTurn ? 'playable' : 'unplayable');
        const statusIcon = statusEl.querySelector('.tooltip-status-icon');
        const statusText = statusEl.querySelector('.tooltip-status-text');
        
        if (isPlayable && isYourTurn) {
            if (statusIcon) statusIcon.textContent = '✓';
            if (statusText) statusText.textContent = 'Playable';
        } else {
            if (statusIcon) statusIcon.textContent = '✗';
            if (statusText) statusText.textContent = 'Cannot Play';
        }
    }
    
    // Reason why card can/cannot be played
    if (reasonEl) {
        reasonEl.textContent = getPlayabilityReason(cardName, card, isPlayable, isYourTurn);
    }
    
    // Set category for accent color
    tooltip.setAttribute('data-category', card.category);
    
    // Position and show
    positionTooltip(event);
    tooltip.classList.add('visible');
    tooltipVisible = true;
}

/**
 * Position the tooltip near the cursor/card
 */
function positionTooltip(event) {
    const tooltip = document.getElementById('cardTooltip');
    if (!tooltip) return;
    
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let x = event.clientX || event.pageX;
    let y = event.clientY || event.pageY;
    
    // Offset from cursor
    const offsetX = 15;
    const offsetY = -10;
    
    // Calculate position
    let left = x + offsetX;
    let top = y + offsetY - tooltipRect.height;
    
    // Keep tooltip within viewport (horizontal)
    if (left + tooltipRect.width > viewportWidth - 20) {
        left = x - tooltipRect.width - offsetX;
    }
    if (left < 20) {
        left = 20;
    }
    
    // Keep tooltip within viewport (vertical)
    if (top < 20) {
        top = y + 25; // Show below cursor instead
    }
    if (top + tooltipRect.height > viewportHeight - 20) {
        top = viewportHeight - tooltipRect.height - 20;
    }
    
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
}

/**
 * Hide the card tooltip
 */
function hideCardTooltip() {
    const tooltip = document.getElementById('cardTooltip');
    if (tooltip) {
        tooltip.classList.remove('visible');
    }
    tooltipVisible = false;
}

/**
 * Get display name for a category
 */
function getCategoryDisplayName(category) {
    const names = {
        'LOOP': 'Loop',
        'VARIABLE': 'Variable',
        'KEYWORD': 'Keyword',
        'FUNCTION': 'Function',
        'VALUE': 'Value',
        'OPERATOR': 'Operator',
        'SYNTAX_OPEN': 'Syntax',
        'SYNTAX_CLOSE': 'Syntax',
        'SYNTAX_COLON': 'Syntax',
        'SPECIAL': 'Special Card'
    };
    return names[category] || category;
}

/**
 * Get reason why a card can or cannot be played
 */
function getPlayabilityReason(cardName, card, isPlayable, isYourTurn) {
    if (!currentGameState?.game_started) {
        return 'Waiting for game to start';
    }
    
    if (currentGameState?.game_over) {
        return 'Game has ended';
    }
    
    if (!isYourTurn) {
        return "Wait for your turn";
    }
    
    if (isPlayable) {
        if (card.category === 'SPECIAL') {
            return 'Special cards can always be played';
        }
        const lastCard = currentGameState?.last_played_card;
        if (lastCard) {
            return `Can follow "${lastCard}"`;
        }
        return 'Valid starting card';
    }
    
    // Not playable - explain why
    const lastCard = currentGameState?.last_played_card;
    const lastCategory = lastCard ? (cardData[lastCard]?.category || 'unknown') : 'START';
    
    // Check for parenthesis balance issue
    if (cardName === ')' && (currentGameState?.open_paren_count || 0) <= 0) {
        return 'No open parenthesis to close';
    }
    
    // General incompatibility
    if (lastCard) {
        return `Cannot follow "${lastCard}" (${getCategoryDisplayName(lastCategory)})`;
    }
    
    return 'Cannot be played as starting card';
}

/**
 * Apply basic Python syntax highlighting to code
 */
function highlightPythonSyntax(code) {
    if (!code) return '';
    
    // Escape HTML first
    let highlighted = escapeHtml(code);
    
    // Highlight comments (must be done first to avoid conflicts)
    highlighted = highlighted.replace(/(#[^\n]*)/g, '<span class="code-comment">$1</span>');
    
    // Highlight strings (single and double quotes)
    highlighted = highlighted.replace(/(&quot;[^&]*&quot;|&#39;[^&#]*&#39;|'[^']*'|"[^"]*")/g, '<span class="code-string">$1</span>');
    
    // Highlight f-strings
    highlighted = highlighted.replace(/\bf(&quot;|&#39;|'|")/g, '<span class="code-string">f$1</span>');
    
    // Highlight keywords
    const keywords = ['for', 'while', 'if', 'else', 'elif', 'def', 'return', 'class', 'import', 'from', 'in', 'not', 'and', 'or', 'is', 'True', 'False', 'None', 'try', 'except', 'finally', 'with', 'as', 'lambda', 'pass', 'break', 'continue', 'yield', 'raise', 'global', 'nonlocal'];
    keywords.forEach(kw => {
        const regex = new RegExp(`\\b(${kw})\\b`, 'g');
        highlighted = highlighted.replace(regex, '<span class="code-keyword">$1</span>');
    });
    
    // Highlight built-in functions
    const builtins = ['print', 'range', 'len', 'input', 'int', 'str', 'float', 'list', 'dict', 'set', 'tuple', 'sum', 'max', 'min', 'abs', 'round', 'sorted', 'enumerate', 'zip', 'map', 'filter', 'open', 'type'];
    builtins.forEach(fn => {
        const regex = new RegExp(`\\b(${fn})(\\()`, 'g');
        highlighted = highlighted.replace(regex, '<span class="code-function">$1</span>$2');
    });
    
    // Highlight numbers
    highlighted = highlighted.replace(/\b(\d+\.?\d*)\b/g, '<span class="code-number">$1</span>');
    
    return highlighted;
}

// =============================================================================
// POWER SYSTEM
// =============================================================================

/**
 * Update power-related UI elements
 */
function updatePowerUI(state) {
    const powerIndicator = document.getElementById('powerIndicator');
    const powerProgress = document.getElementById('powerProgress');
    const activeEffectIndicator = document.getElementById('activeEffectIndicator');
    
    // Show/hide power button
    if (powerIndicator) {
        if (state.power_available && state.is_your_turn && !powerModalOpen) {
            powerIndicator.style.display = 'block';
        } else {
            powerIndicator.style.display = 'none';
        }
    }
    
    // Update power progress bar
    if (powerProgress) {
        const progressFill = document.getElementById('powerProgressFill');
        const progressText = document.getElementById('powerProgressText');
        
        if (state.power_available) {
            // Power is ready
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = 'READY!';
            powerProgress.classList.add('ready');
        } else {
            const turnsPlayed = state.turns_played || 0;
            const turnsUntil = state.turns_until_power || 5;
            const progress = ((5 - turnsUntil) / 5) * 100;
            
            if (progressFill) progressFill.style.width = `${progress}%`;
            if (progressText) progressText.textContent = `${turnsUntil} turn${turnsUntil !== 1 ? 's' : ''}`;
            powerProgress.classList.remove('ready');
        }
    }
    
    // Show/hide active effect indicator
    if (activeEffectIndicator) {
        if (state.active_effect) {
            const effectInfo = getEffectDisplayInfo(state.active_effect);
            const effectIcon = document.getElementById('effectIcon');
            const effectText = document.getElementById('effectText');
            
            if (effectIcon) effectIcon.textContent = effectInfo.icon;
            if (effectText) effectText.textContent = effectInfo.name;
            
            activeEffectIndicator.style.display = 'flex';
        } else {
            activeEffectIndicator.style.display = 'none';
        }
    }
    
    // Show block indicator on portraits
    const yourPortrait = document.querySelector('.player-portrait.you');
    const opponentPortrait = document.querySelector('.player-portrait.opponent');
    
    if (yourPortrait) {
        yourPortrait.classList.toggle('blocked', state.is_blocked || false);
    }
    
    // Auto-show power modal when power becomes available and it's player's turn
    if (state.power_available && state.is_your_turn && !powerModalOpen && state.game_started && !state.game_over) {
        // Small delay to avoid interrupting other UI updates
        setTimeout(() => {
            if (currentGameState?.power_available && currentGameState?.is_your_turn && !powerModalOpen) {
                showPowerModal(state.powers);
            }
        }, 500);
    }
}

/**
 * Get display info for an effect
 */
function getEffectDisplayInfo(effectName) {
    const effects = {
        'double_points': { name: '2X Points Active!', icon: '⚡' },
        'blocked': { name: 'Blocked!', icon: '🛡️' }
    };
    return effects[effectName] || { name: effectName, icon: '✨' };
}

/**
 * Show the power selection modal
 */
function showPowerModal(powers) {
    const overlay = document.getElementById('powerModalOverlay');
    const optionsContainer = document.getElementById('powerOptions');
    
    if (!overlay || !optionsContainer || powerModalOpen) return;
    
    // Build power options HTML
    const powersHtml = Object.entries(powers || {}).map(([key, power]) => `
        <div class="power-option" data-power="${key}" onclick="selectPower('${key}')">
            <span class="power-option-icon">${power.icon || '⚡'}</span>
            <div class="power-option-name">${power.name || key}</div>
            <div class="power-option-desc">${power.description || ''}</div>
        </div>
    `).join('');
    
    optionsContainer.innerHTML = powersHtml;
    
    // Show modal
    overlay.classList.add('visible');
    powerModalOpen = true;
    
    // Setup skip button
    const skipBtn = document.getElementById('powerSkipBtn');
    if (skipBtn) {
        skipBtn.onclick = hidePowerModal;
    }
}

/**
 * Hide the power selection modal
 */
function hidePowerModal() {
    const overlay = document.getElementById('powerModalOverlay');
    if (overlay) {
        overlay.classList.remove('visible');
    }
    powerModalOpen = false;
}

/**
 * Select and use a power
 */
function selectPower(powerName) {
    if (!powerName || !currentGameState?.is_your_turn) return;
    
    console.log('Selecting power:', powerName);
    
    // Emit power usage to server
    socket.emit('use_power', {
        room: ROOM_CODE,
        power: powerName
    });
    
    // Add visual feedback on the selected option
    const selectedOption = document.querySelector(`[data-power="${powerName}"]`);
    if (selectedOption) {
        selectedOption.style.transform = 'scale(0.95)';
        selectedOption.style.borderColor = 'var(--accent-green)';
    }
}

/**
 * Show power effect animation
 */
function showPowerEffect(powerName, icon, message, isPlayer) {
    const effectEl = document.createElement('div');
    effectEl.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0);
        font-size: 3rem;
        font-weight: 800;
        color: ${isPlayer ? 'var(--accent-gold)' : 'var(--accent-purple)'};
        text-shadow: 0 4px 30px rgba(212, 168, 75, 0.6);
        z-index: 10000;
        pointer-events: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 15px;
    `;
    effectEl.innerHTML = `
        <span style="font-size: 5rem;">${icon}</span>
        <span style="font-size: 1.5rem; text-transform: uppercase; letter-spacing: 3px;">${powerName.replace('_', ' ')}</span>
    `;
    document.body.appendChild(effectEl);
    
    effectEl.animate([
        { transform: 'translate(-50%, -50%) scale(0) rotate(-10deg)', opacity: 0 },
        { transform: 'translate(-50%, -50%) scale(1.3) rotate(5deg)', opacity: 1, offset: 0.3 },
        { transform: 'translate(-50%, -50%) scale(1) rotate(0deg)', opacity: 1, offset: 0.5 },
        { transform: 'translate(-50%, -50%) scale(1) rotate(0deg)', opacity: 1, offset: 0.8 },
        { transform: 'translate(-50%, -50%) scale(0.8) rotate(10deg)', opacity: 0 }
    ], {
        duration: 2000,
        easing: 'ease-out'
    });
    
    setTimeout(() => effectEl.remove(), 2000);
}

/**
 * Show peek modal with opponent's cards
 */
function showPeekModal(cards) {
    const overlay = document.getElementById('peekModalOverlay');
    const cardsContainer = document.getElementById('peekedCards');
    const countdownEl = document.getElementById('peekCountdown');
    
    if (!overlay || !cardsContainer) return;
    
    // Clear any existing countdown
    if (peekCountdownInterval) {
        clearInterval(peekCountdownInterval);
    }
    
    // Build cards HTML
    const cardsHtml = cards.map((cardName, i) => {
        const card = cardData[cardName] || { category: 'SPECIAL', points: 0 };
        const categoryClass = categoryClasses[card.category] || 'special';
        
        return `
            <div class="game-card ${categoryClass}" style="animation-delay: ${i * 0.1}s">
                <span class="card-category">${categoryNames[card.category] || 'Special'}</span>
                <span class="card-name">${escapeHtml(cardName)}</span>
                <span class="card-points">${card.points}pt</span>
            </div>
        `;
    }).join('');
    
    cardsContainer.innerHTML = cardsHtml;
    
    // Show modal
    overlay.classList.add('visible');
    peekModalOpen = true;
    
    // Start countdown
    let countdown = 5;
    if (countdownEl) countdownEl.textContent = countdown;
    
    peekCountdownInterval = setInterval(() => {
        countdown--;
        if (countdownEl) countdownEl.textContent = countdown;
        
        if (countdown <= 0) {
            clearInterval(peekCountdownInterval);
            hidePeekModal();
        }
    }, 1000);
}

/**
 * Hide peek modal
 */
function hidePeekModal() {
    const overlay = document.getElementById('peekModalOverlay');
    if (overlay) {
        overlay.classList.remove('visible');
    }
    peekModalOpen = false;
    
    if (peekCountdownInterval) {
        clearInterval(peekCountdownInterval);
        peekCountdownInterval = null;
    }
}

/**
 * Setup power button click handler
 */
function setupPowerButton() {
    const powerBtn = document.getElementById('usePowerBtn');
    if (powerBtn) {
        powerBtn.addEventListener('click', () => {
            if (currentGameState?.power_available && currentGameState?.is_your_turn) {
                showPowerModal(currentGameState.powers);
            }
        });
    }
}

// =============================================================================
// SYNTAX PREVIEW PANEL
// =============================================================================

let syntaxPreviewCollapsed = false;

/**
 * Initialize the syntax preview panel
 */
function initSyntaxPreview() {
    const toggleBtn = document.getElementById('syntaxToggleBtn');
    const preview = document.getElementById('syntaxPreview');
    
    if (toggleBtn && preview) {
        toggleBtn.addEventListener('click', () => {
            syntaxPreviewCollapsed = !syntaxPreviewCollapsed;
            preview.classList.toggle('collapsed', syntaxPreviewCollapsed);
            
            const icon = toggleBtn.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = syntaxPreviewCollapsed ? '+' : '−';
            }
        });
    }
}

/**
 * Update the syntax preview with the current played cards
 * Now uses server-side Python validation via ast.parse()
 */
function updateSyntaxPreview(playedCards, syntaxInfo = null) {
    const codeEl = document.getElementById('syntaxCode');
    const previewEl = document.getElementById('syntaxPreview');
    const statusEl = document.getElementById('syntaxStatus');
    const suggestionsEl = document.getElementById('syntaxSuggestions');
    const structureEl = document.getElementById('codeStructure');
    
    if (!codeEl || !previewEl) return;
    
    if (!playedCards || playedCards.length === 0) {
        codeEl.innerHTML = renderCodeEditorEmpty();
        previewEl.classList.remove('syntax-valid', 'syntax-error', 'syntax-incomplete');
        if (statusEl) statusEl.textContent = '';
        if (suggestionsEl) suggestionsEl.innerHTML = '';
        if (structureEl) structureEl.innerHTML = '';
        return;
    }
    
    // Use server-provided formatted code if available
    let codeStr;
    if (syntaxInfo && syntaxInfo.formatted_code) {
        codeStr = syntaxInfo.formatted_code;
    } else if (syntaxInfo && syntaxInfo.python_code) {
        codeStr = syntaxInfo.python_code;
    } else {
        codeStr = buildPythonCode(playedCards);
    }
    
    // Render code with line numbers like a real IDE
    const codeHtml = renderCodeEditor(codeStr, syntaxInfo);
    codeEl.innerHTML = codeHtml;
    
    // Update validation status from server (uses ast.parse())
    previewEl.classList.remove('syntax-valid', 'syntax-error', 'syntax-incomplete');
    
    if (syntaxInfo) {
        if (syntaxInfo.is_complete) {
            previewEl.classList.add('syntax-valid');
            if (statusEl) {
                statusEl.innerHTML = '<span class="status-icon">✓</span> Valid Python';
                statusEl.className = 'syntax-status valid';
            }
        } else if (syntaxInfo.is_valid_python) {
            previewEl.classList.add('syntax-incomplete');
            if (statusEl) {
                statusEl.innerHTML = '<span class="status-icon">⋯</span> Building...';
                statusEl.className = 'syntax-status incomplete';
            }
        } else {
            previewEl.classList.add('syntax-error');
            if (statusEl) {
                statusEl.innerHTML = `<span class="status-icon">✗</span> ${escapeHtml(syntaxInfo.syntax_error || 'Syntax error')}`;
                statusEl.className = 'syntax-status error';
            }
        }
        
        // Show code structure info
        if (structureEl && syntaxInfo.code_structure) {
            const struct = syntaxInfo.code_structure;
            const badges = [];
            if (struct.has_loop) badges.push('<span class="struct-badge loop">Loop</span>');
            if (struct.has_condition) badges.push('<span class="struct-badge condition">Condition</span>');
            if (struct.statements > 1) badges.push(`<span class="struct-badge">${struct.statements} statements</span>`);
            structureEl.innerHTML = badges.join('');
        }
        
        // Show suggested card categories
        if (suggestionsEl && syntaxInfo.suggested_categories && syntaxInfo.suggested_categories.length > 0) {
            const suggestionBadges = syntaxInfo.suggested_categories.map(cat => {
                const catClass = categoryClasses[cat] || 'keyword';
                const catName = categoryNames[cat] || cat;
                return `<span class="suggestion-badge ${catClass}">${catName}</span>`;
            }).join('');
            suggestionsEl.innerHTML = `<span class="suggestions-label">Next:</span> ${suggestionBadges}`;
        } else if (suggestionsEl) {
            suggestionsEl.innerHTML = '';
        }
    }
    
    // Scroll to show new code
    const previewBody = document.getElementById('syntaxPreviewBody');
    if (previewBody) {
        previewBody.scrollTop = previewBody.scrollHeight;
    }
}

/**
 * Render empty code editor state
 */
function renderCodeEditorEmpty() {
    return `
        <div class="code-editor">
            <div class="code-line">
                <span class="line-number">1</span>
                <span class="line-content"><span class="code-comment"># Play cards to build Python code...</span></span>
            </div>
        </div>
    `;
}

/**
 * Render code like an IDE with line numbers and syntax highlighting
 */
function renderCodeEditor(code, syntaxInfo) {
    if (!code || !code.trim()) {
        return renderCodeEditorEmpty();
    }
    
    // Split into lines
    const lines = code.split('\n');
    
    // Build HTML for each line
    const linesHtml = lines.map((line, index) => {
        const lineNum = index + 1;
        const highlightedLine = highlightPythonLine(line);
        const isLastLine = index === lines.length - 1;
        
        return `
            <div class="code-line${isLastLine ? ' current-line' : ''}">
                <span class="line-number">${lineNum}</span>
                <span class="line-content">${highlightedLine}${isLastLine ? '<span class="cursor">|</span>' : ''}</span>
            </div>
        `;
    }).join('');
    
    return `<div class="code-editor">${linesHtml}</div>`;
}

/**
 * Highlight a single line of Python code
 */
function highlightPythonLine(line) {
    if (!line) return '';
    
    // First escape HTML
    let highlighted = escapeHtml(line);
    
    // Preserve leading whitespace (indentation)
    const leadingSpaces = line.match(/^(\s*)/)[1];
    const indentHtml = leadingSpaces.replace(/ /g, '&nbsp;').replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
    
    // Get the content without leading spaces
    let content = highlighted.substring(leadingSpaces.length);
    
    // Highlight comments first
    if (content.includes('#')) {
        const commentIdx = content.indexOf('#');
        const beforeComment = content.substring(0, commentIdx);
        const comment = content.substring(commentIdx);
        content = highlightPythonTokens(beforeComment) + `<span class="code-comment">${comment}</span>`;
    } else {
        content = highlightPythonTokens(content);
    }
    
    return indentHtml + content;
}

/**
 * Highlight Python tokens (keywords, functions, etc.)
 */
function highlightPythonTokens(text) {
    if (!text) return '';
    
    // Keywords (purple/magenta)
    const keywords = ['for', 'while', 'if', 'else', 'elif', 'def', 'return', 'class', 
                      'import', 'from', 'in', 'not', 'and', 'or', 'is', 'True', 'False', 
                      'None', 'try', 'except', 'finally', 'with', 'as', 'lambda', 'pass', 
                      'break', 'continue', 'yield', 'raise', 'global', 'nonlocal'];
    
    // Built-in functions (cyan/blue)
    const builtins = ['print', 'range', 'len', 'input', 'int', 'str', 'float', 'list', 
                      'dict', 'set', 'tuple', 'sum', 'max', 'min', 'abs', 'round', 
                      'sorted', 'enumerate', 'zip', 'map', 'filter', 'open', 'type'];
    
    // Variable names we recognize (red/orange)
    const variables = ['x', 'i', 'n', 'item', 'result'];
    
    // Tokenize the text
    let result = '';
    let i = 0;
    
    while (i < text.length) {
        // Check for string literals
        if (text[i] === '"' || text[i] === "'") {
            const quote = text[i];
            let end = i + 1;
            while (end < text.length && text[end] !== quote) {
                if (text[end] === '\\') end++; // Skip escaped chars
                end++;
            }
            end++; // Include closing quote
            result += `<span class="code-string">${text.substring(i, end)}</span>`;
            i = end;
            continue;
        }
        
        // Check for numbers
        if (/\d/.test(text[i])) {
            let end = i;
            while (end < text.length && /[\d.]/.test(text[end])) end++;
            result += `<span class="code-number">${text.substring(i, end)}</span>`;
            i = end;
            continue;
        }
        
        // Check for identifiers/keywords
        if (/[a-zA-Z_]/.test(text[i])) {
            let end = i;
            while (end < text.length && /[a-zA-Z0-9_]/.test(text[end])) end++;
            const word = text.substring(i, end);
            
            if (keywords.includes(word)) {
                result += `<span class="code-keyword">${word}</span>`;
            } else if (builtins.includes(word)) {
                result += `<span class="code-function">${word}</span>`;
            } else if (variables.includes(word)) {
                result += `<span class="code-variable">${word}</span>`;
            } else {
                result += `<span class="code-identifier">${word}</span>`;
            }
            i = end;
            continue;
        }
        
        // Operators
        if ('+-*/<>=!'.includes(text[i])) {
            // Check for multi-char operators
            const twoChar = text.substring(i, i + 2);
            if (['==', '!=', '<=', '>=', '+=', '-=', '*=', '/='].includes(twoChar)) {
                result += `<span class="code-operator">${twoChar}</span>`;
                i += 2;
                continue;
            }
            result += `<span class="code-operator">${text[i]}</span>`;
            i++;
            continue;
        }
        
        // Syntax characters (parens, colon, brackets)
        if ('()[]{}:,'.includes(text[i])) {
            result += `<span class="code-syntax">${text[i]}</span>`;
            i++;
            continue;
        }
        
        // Whitespace and other characters
        result += text[i];
        i++;
    }
    
    return result;
}

/**
 * Build Python code string from played cards
 */
function buildPythonCode(playedCards) {
    let code = '';
    let indentLevel = 0;
    let lastCategory = 'START';
    let needsIndent = false;
    
    for (let i = 0; i < playedCards.length; i++) {
        const cardName = playedCards[i];
        const card = cardData[cardName] || {};
        const category = card.category || 'SPECIAL';
        
        // Skip special cards in the code output
        if (category === 'SPECIAL') {
            continue;
        }
        
        // Handle indentation after colon
        if (needsIndent) {
            code += '\n' + '    '.repeat(indentLevel);
            needsIndent = false;
        }
        
        // Add spacing based on category transitions
        if (i > 0 && category !== 'SPECIAL') {
            const prevCard = playedCards[i - 1];
            const prevCardData = cardData[prevCard] || {};
            const prevCategory = prevCardData.category || 'SPECIAL';
            
            // Add space before most categories
            if (prevCategory !== 'SYNTAX_OPEN' && 
                category !== 'SYNTAX_CLOSE' && 
                category !== 'SYNTAX_COLON' &&
                prevCategory !== 'SPECIAL') {
                
                // No space after ( or before )
                if (prevCategory !== 'FUNCTION' && cardName !== '(') {
                    code += ' ';
                }
            }
        }
        
        // Add the card
        code += cardName;
        
        // Handle colon - increase indent and start new line
        if (category === 'SYNTAX_COLON') {
            indentLevel++;
            needsIndent = true;
        }
        
        lastCategory = category;
    }
    
    // Add a cursor indicator if there's more to come
    if (lastCategory !== 'SYNTAX_COLON') {
        code += ' █';
    } else {
        code += '█';
    }
    
    return code;
}

/**
 * Highlight Python syntax for the preview panel
 */
function highlightPythonSyntaxForPreview(code, playedCards) {
    if (!code) return '';
    
    // Escape HTML first
    let highlighted = escapeHtml(code);
    
    // Remove cursor temporarily
    highlighted = highlighted.replace(' █', '').replace('█', '');
    
    // Find the last card to highlight it
    const lastCard = playedCards[playedCards.length - 1];
    const lastCardData = cardData[lastCard] || {};
    const lastCardEscaped = escapeHtml(lastCard);
    
    // Keywords (purple)
    const keywords = ['for', 'while', 'if', 'else', 'elif', 'def', 'return', 'class', 'import', 'from', 'in', 'not', 'and', 'or', 'is', 'True', 'False', 'None', 'try', 'except', 'finally', 'with', 'as', 'lambda', 'pass', 'break', 'continue'];
    keywords.forEach(kw => {
        const regex = new RegExp(`\\b(${kw})\\b`, 'g');
        highlighted = highlighted.replace(regex, '<span class="code-keyword">$1</span>');
    });
    
    // Built-in functions (blue)
    const builtins = ['print', 'range', 'len', 'input', 'int', 'str', 'float', 'list', 'dict', 'set', 'tuple', 'sum', 'max', 'min', 'abs', 'round', 'sorted', 'enumerate', 'zip', 'map', 'filter', 'open', 'type'];
    builtins.forEach(fn => {
        const regex = new RegExp(`\\b(${fn})\\b`, 'g');
        highlighted = highlighted.replace(regex, '<span class="code-function">$1</span>');
    });
    
    // Variables (reddish)
    const variables = ['x', 'i', 'n', 'item', 'result'];
    variables.forEach(v => {
        const regex = new RegExp(`\\b(${v})\\b`, 'g');
        highlighted = highlighted.replace(regex, '<span class="code-variable">$1</span>');
    });
    
    // Numbers (orange)
    highlighted = highlighted.replace(/\b(\d+\.?\d*)\b/g, '<span class="code-number">$1</span>');
    
    // Strings
    highlighted = highlighted.replace(/(&quot;[^&]*&quot;|"[^"]*")/g, '<span class="code-string">$1</span>');
    
    // Operators
    const operators = ['\\+', '-', '\\*', '/', '==', '!=', '&lt;=', '&gt;=', '&lt;', '&gt;', '=', '\\+='];
    operators.forEach(op => {
        const regex = new RegExp(`(${op})`, 'g');
        highlighted = highlighted.replace(regex, '<span class="code-operator">$1</span>');
    });
    
    // Syntax (parentheses, colon)
    highlighted = highlighted.replace(/(\(|\)|:)/g, '<span class="code-syntax">$1</span>');
    
    // Add cursor back with special styling
    highlighted += '<span class="code-cursor">█</span>';
    
    return highlighted;
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
    if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(text);
    } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.cssText = 'position: fixed; opacity: 0;';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
    }
}

// =============================================================================
// INTERACTIVE TUTORIAL SYSTEM
// =============================================================================

/**
 * TutorialManager - Handles the step-by-step interactive tutorial
 */
class TutorialManager {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.overlay = null;
        this.highlight = null;
        this.tooltip = null;
        
        // Tutorial step definitions
        this.steps = [
            {
                id: 'welcome',
                title: 'Welcome to Python Card Game!',
                content: `
                    <p>Learn to build Python code through card battles!</p>
                    <p>This quick tutorial will show you the basics. You can replay it anytime by clicking the <strong>?</strong> button.</p>
                `,
                target: null, // No target - centered modal
                position: 'center',
                isWelcome: true
            },
            {
                id: 'your-hand',
                title: 'Your Hand',
                content: `
                    <p>These are your cards. Each card represents a piece of Python syntax.</p>
                    <div class="tutorial-mini-cards">
                        <div class="tutorial-mini-card loop">for</div>
                        <div class="tutorial-mini-card variable">i</div>
                        <div class="tutorial-mini-card keyword">in</div>
                        <div class="tutorial-mini-card function">range</div>
                        <div class="tutorial-mini-card value">10</div>
                    </div>
                    <p><strong>Glowing cards</strong> can be played on your turn. Dimmed cards cannot be played right now.</p>
                `,
                target: '.your-area .hand-container',
                position: 'top'
            },
            {
                id: 'card-types',
                title: 'Card Categories',
                content: `
                    <p>Cards are color-coded by type:</p>
                    <div class="tutorial-card-grid">
                        <div class="tutorial-card-example">
                            <div class="tutorial-mini-card loop">for</div>
                            <span class="tutorial-card-label">Loop</span>
                        </div>
                        <div class="tutorial-card-example">
                            <div class="tutorial-mini-card variable">x</div>
                            <span class="tutorial-card-label">Variable</span>
                        </div>
                        <div class="tutorial-card-example">
                            <div class="tutorial-mini-card keyword">if</div>
                            <span class="tutorial-card-label">Keyword</span>
                        </div>
                        <div class="tutorial-card-example">
                            <div class="tutorial-mini-card function">print</div>
                            <span class="tutorial-card-label">Function</span>
                        </div>
                        <div class="tutorial-card-example">
                            <div class="tutorial-mini-card value">10</div>
                            <span class="tutorial-card-label">Value</span>
                        </div>
                        <div class="tutorial-card-example">
                            <div class="tutorial-mini-card operator">==</div>
                            <span class="tutorial-card-label">Operator</span>
                        </div>
                    </div>
                    <p>Each type can only follow certain other types - just like real Python!</p>
                `,
                target: '.your-area .hand-container',
                position: 'top'
            },
            {
                id: 'play-zone',
                title: 'The Code Zone',
                content: `
                    <p>Cards you play appear here, building a Python program.</p>
                    <p>Click the <strong>+</strong> icons to insert cards at different positions, not just at the end!</p>
                    <div class="tutorial-example">for i in range(10):</div>
                `,
                target: '.play-zone',
                position: 'bottom'
            },
            {
                id: 'insertion',
                title: 'Flexible Insertion',
                content: `
                    <p>Unlike traditional card games, you can insert cards <strong>anywhere</strong> in the sequence!</p>
                    <p>Click a <strong>+</strong> icon between cards to select an insertion point, then click a card from your hand.</p>
                `,
                target: '.play-zone',
                position: 'bottom'
            },
            {
                id: 'scoring',
                title: 'Scoring Points',
                content: `
                    <p>Each card has a point value:</p>
                    <div class="tutorial-scoring-grid">
                        <div class="tutorial-score-row">
                            <span class="tutorial-score-label">Common (1pt)</span>
                            <div class="tutorial-score-cards">
                                <div class="tutorial-mini-card small variable">x</div>
                                <div class="tutorial-mini-card small value">10</div>
                                <div class="tutorial-mini-card small operator">+</div>
                            </div>
                        </div>
                        <div class="tutorial-score-row">
                            <span class="tutorial-score-label">Uncommon (2pt)</span>
                            <div class="tutorial-score-cards">
                                <div class="tutorial-mini-card small loop">for</div>
                                <div class="tutorial-mini-card small function">range</div>
                                <div class="tutorial-mini-card small keyword">if</div>
                            </div>
                        </div>
                        <div class="tutorial-score-row">
                            <span class="tutorial-score-label">Rare (3pt)</span>
                            <div class="tutorial-score-cards">
                                <div class="tutorial-mini-card small keyword rare">def</div>
                                <div class="tutorial-mini-card small keyword rare">return</div>
                            </div>
                        </div>
                    </div>
                `,
                target: '.player-portrait.you',
                position: 'left'
            },
            {
                id: 'special-cards',
                title: 'Special Cards',
                content: `
                    <p>Golden <strong class="tutorial-card-badge special">Special</strong> cards have unique effects:</p>
                    <div class="tutorial-special-cards">
                        <div class="tutorial-special-item">
                            <div class="tutorial-mini-card special">Wild</div>
                            <span class="tutorial-special-desc">Plays as any category</span>
                        </div>
                        <div class="tutorial-special-item">
                            <div class="tutorial-mini-card special">Skip</div>
                            <span class="tutorial-special-desc">Skip opponent's turn</span>
                        </div>
                        <div class="tutorial-special-item">
                            <div class="tutorial-mini-card special">Draw 2</div>
                            <span class="tutorial-special-desc">Opponent draws 2 cards</span>
                        </div>
                    </div>
                `,
                target: '.your-area .hand-container',
                position: 'top'
            },
            {
                id: 'powers',
                title: 'Special Powers',
                content: `
                    <p>Every <strong>5 turns</strong>, you earn a special power!</p>
                    <p>Powers include double points, peeking at opponent's cards, and more.</p>
                    <p>Watch the power progress bar to see when it's ready.</p>
                `,
                target: '.power-progress',
                position: 'left'
            },
            {
                id: 'opponent',
                title: 'Your Opponent',
                content: `
                    <p>Your opponent's cards are shown face-down here.</p>
                    <p>You're competing to have the <strong>highest score</strong> when the deck runs out!</p>
                `,
                target: '.opponent-area',
                position: 'bottom'
            },
            {
                id: 'deck',
                title: 'The Deck',
                content: `
                    <p>Cards remaining in the deck. When it's empty, the game ends!</p>
                    <p>If you can't play any card, you must <strong>pass</strong> and draw a card.</p>
                `,
                target: '.deck-display',
                position: 'left'
            },
            {
                id: 'ready',
                title: 'Ready to Play!',
                content: `
                    <p>You're all set! Remember:</p>
                    <p><strong>1.</strong> Play cards to build valid Python code</p>
                    <p><strong>2.</strong> Insert cards anywhere using + icons</p>
                    <p><strong>3.</strong> Highest score when deck empties wins!</p>
                    <p>Good luck and have fun learning Python! 🐍</p>
                `,
                target: null,
                position: 'center',
                isWelcome: true
            }
        ];
    }
    
    /**
     * Initialize the tutorial DOM elements
     */
    init() {
        // Create overlay (dark background for centered modals)
        this.overlay = document.createElement('div');
        this.overlay.className = 'tutorial-overlay';
        this.overlay.id = 'tutorialOverlay';
        
        // Create highlight box (creates spotlight effect with box-shadow)
        this.highlight = document.createElement('div');
        this.highlight.className = 'tutorial-highlight';
        this.highlight.id = 'tutorialHighlight';
        this.highlight.style.display = 'none';
        
        // Create tooltip (must be added AFTER highlight for z-index stacking)
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'tutorial-tooltip';
        this.tooltip.id = 'tutorialTooltip';
        
        // Add to DOM in correct order for z-index stacking:
        // 1. Overlay (z-index: 9999) - for centered modal backgrounds
        // 2. Highlight (z-index: 10000) - creates spotlight with box-shadow
        // 3. Tooltip (z-index: 10001) - must be above everything
        document.body.appendChild(this.overlay);
        document.body.appendChild(this.highlight);
        document.body.appendChild(this.tooltip);
        
        // Create help button
        this.createHelpButton();
        
        // Check if tutorial should auto-start
        this.checkFirstVisit();
    }
    
    /**
     * Create the floating help button
     */
    createHelpButton() {
        console.log('[Tutorial] Creating help button...');
        const helpBtn = document.createElement('button');
        helpBtn.className = 'tutorial-help-btn';
        helpBtn.id = 'tutorialHelpBtn';
        helpBtn.innerHTML = '?';
        helpBtn.title = 'Show Tutorial';
        helpBtn.addEventListener('click', () => this.start());
        document.body.appendChild(helpBtn);
        console.log('[Tutorial] Help button added to DOM');
    }
    
    /**
     * Check if this is the user's first visit
     * Note: Auto-start is disabled - tutorial is accessible via the "?" button
     */
    checkFirstVisit() {
        // Tutorial is now manually triggered via the "?" button
        // The lobby has its own tutorial for first-time users
        // This in-game tutorial helps with gameplay specifics
    }
    
    /**
     * Start the tutorial
     */
    start() {
        this.currentStep = 0;
        this.isActive = true;
        this.overlay.classList.add('active');
        this.tooltip.classList.add('active');
        this.showStep(0);
    }
    
    /**
     * End the tutorial
     */
    end() {
        this.isActive = false;
        this.overlay.classList.remove('active');
        this.tooltip.classList.remove('active');
        this.highlight.style.display = 'none';
        
        // Show completion notification
        if (typeof showNotification === 'function') {
            showNotification('Tutorial completed! Click ? anytime to replay.', 'success');
        }
    }
    
    /**
     * Skip the tutorial
     */
    skip() {
        this.isActive = false;
        this.overlay.classList.remove('active');
        this.tooltip.classList.remove('active');
        this.highlight.style.display = 'none';
    }
    
    /**
     * Show a specific step
     */
    showStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.steps.length) {
            this.end();
            return;
        }
        
        this.currentStep = stepIndex;
        const step = this.steps[stepIndex];
        
        // Update highlight position
        let hasHighlight = false;
        if (step.target) {
            const targetEl = document.querySelector(step.target);
            if (targetEl) {
                this.positionHighlight(targetEl);
                this.highlight.style.display = 'block';
                hasHighlight = true;
            } else {
                this.highlight.style.display = 'none';
            }
        } else {
            this.highlight.style.display = 'none';
        }
        
        // Toggle no-highlight class for centered modals (welcome/end screens)
        if (hasHighlight) {
            this.overlay.classList.remove('no-highlight');
        } else {
            this.overlay.classList.add('no-highlight');
        }
        
        // Render tooltip content
        this.renderTooltip(step, stepIndex);
        
        // Position tooltip
        this.positionTooltip(step);
    }
    
    /**
     * Position the highlight box around an element
     */
    positionHighlight(element) {
        const rect = element.getBoundingClientRect();
        const padding = 10;
        
        this.highlight.style.left = (rect.left - padding) + 'px';
        this.highlight.style.top = (rect.top - padding) + 'px';
        this.highlight.style.width = (rect.width + padding * 2) + 'px';
        this.highlight.style.height = (rect.height + padding * 2) + 'px';
    }
    
    /**
     * Render the tooltip content
     */
    renderTooltip(step, stepIndex) {
        const isFirst = stepIndex === 0;
        const isLast = stepIndex === this.steps.length - 1;
        
        // Build progress dots
        const progressDots = this.steps.map((_, i) => {
            let className = 'tutorial-progress-dot';
            if (i < stepIndex) className += ' completed';
            if (i === stepIndex) className += ' current';
            return `<div class="${className}"></div>`;
        }).join('');
        
        // Build navigation buttons
        let navHtml = '<div class="tutorial-nav">';
        navHtml += `<button class="tutorial-btn skip" onclick="tutorialManager.skip()">Skip</button>`;
        navHtml += '<div style="display: flex; gap: 10px;">';
        
        if (!isFirst) {
            navHtml += `<button class="tutorial-btn prev" onclick="tutorialManager.showStep(${stepIndex - 1})">Back</button>`;
        }
        
        if (isLast) {
            navHtml += `<button class="tutorial-btn finish" onclick="tutorialManager.end()">Start Playing!</button>`;
        } else {
            navHtml += `<button class="tutorial-btn next" onclick="tutorialManager.showStep(${stepIndex + 1})">Next</button>`;
        }
        
        navHtml += '</div></div>';
        
        // Render full tooltip
        if (step.isWelcome) {
            this.tooltip.innerHTML = `
                <div class="tutorial-welcome">
                    <div class="tutorial-welcome-icon">🐍</div>
                    <h2>${step.title}</h2>
                    <div class="tutorial-content">${step.content}</div>
                    <div class="tutorial-progress">${progressDots}</div>
                    ${navHtml}
                </div>
            `;
        } else {
            this.tooltip.innerHTML = `
                <div class="tutorial-progress">${progressDots}</div>
                <div class="tutorial-header">
                    <div class="tutorial-step-number">${stepIndex}</div>
                    <h3 class="tutorial-title">${step.title}</h3>
                </div>
                <div class="tutorial-content">${step.content}</div>
                ${navHtml}
            `;
        }
    }
    
    /**
     * Position the tooltip relative to the target element
     */
    positionTooltip(step) {
        // Remove old arrow classes
        this.tooltip.classList.remove('arrow-top', 'arrow-bottom', 'arrow-left', 'arrow-right');
        
        if (step.position === 'center' || !step.target) {
            // Center the tooltip
            this.tooltip.style.left = '50%';
            this.tooltip.style.top = '50%';
            this.tooltip.style.transform = 'translate(-50%, -50%)';
            return;
        }
        
        const targetEl = document.querySelector(step.target);
        if (!targetEl) {
            this.tooltip.style.left = '50%';
            this.tooltip.style.top = '50%';
            this.tooltip.style.transform = 'translate(-50%, -50%)';
            return;
        }
        
        const targetRect = targetEl.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const margin = 25;
        
        let left, top;
        
        switch (step.position) {
            case 'top':
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                top = targetRect.top - tooltipRect.height - margin;
                this.tooltip.classList.add('arrow-top');
                break;
            case 'bottom':
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                top = targetRect.bottom + margin;
                this.tooltip.classList.add('arrow-bottom');
                break;
            case 'left':
                left = targetRect.left - tooltipRect.width - margin;
                top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                this.tooltip.classList.add('arrow-left');
                break;
            case 'right':
                left = targetRect.right + margin;
                top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                this.tooltip.classList.add('arrow-right');
                break;
            default:
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                top = targetRect.bottom + margin;
        }
        
        // Keep tooltip in viewport
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        if (left < 20) left = 20;
        if (left + tooltipRect.width > viewportWidth - 20) {
            left = viewportWidth - tooltipRect.width - 20;
        }
        if (top < 20) top = 20;
        if (top + tooltipRect.height > viewportHeight - 20) {
            top = viewportHeight - tooltipRect.height - 20;
        }
        
        this.tooltip.style.left = left + 'px';
        this.tooltip.style.top = top + 'px';
        this.tooltip.style.transform = 'none';
    }
    
    /**
     * Handle window resize
     */
    handleResize() {
        if (this.isActive) {
            this.showStep(this.currentStep);
        }
    }
}

// Create global tutorial manager instance
let tutorialManager = null;

/**
 * Initialize the tutorial system when the game page loads
 */
function initTutorial() {
    console.log('[Tutorial] Initializing tutorial system...');
    
    // Prevent double initialization
    if (tutorialManager) {
        console.log('[Tutorial] Already initialized');
        return;
    }
    
    tutorialManager = new TutorialManager();
    tutorialManager.init();
    console.log('[Tutorial] Tutorial manager created and initialized');
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (tutorialManager) {
            tutorialManager.handleResize();
        }
    });
    
    // Handle escape key to close tutorial
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && tutorialManager?.isActive) {
            tutorialManager.skip();
        }
    });
}

// Note: Tutorial is initialized from game.html after the game loads
// This prevents race conditions with other initialization
