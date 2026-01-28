/**
 * Python Syntax Card Game - Authentication Module
 * Handles Firebase authentication, user profile, and leaderboard
 */

// =============================================================================
// FIREBASE CONFIGURATION
// =============================================================================

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCCGYaBp2cHREU99RdQKutoqhEGCfva_8A",
    authDomain: "pythongame-7b673.firebaseapp.com",
    projectId: "pythongame-7b673",
    storageBucket: "pythongame-7b673.firebasestorage.app",
    messagingSenderId: "444834425195",
    appId: "1:444834425195:web:17523219688d8ff2f4042e",
    measurementId: "G-RVHKPDFVD6"
};

// =============================================================================
// AUTH STATE
// =============================================================================

let firebaseApp = null;
let firebaseAuth = null;
let currentUser = null;
let authToken = null;
let authInitialized = false;
let authAvailable = false;
let isGuestMode = false;

// =============================================================================
// INITIALIZATION
// =============================================================================

/**
 * Initialize the authentication module
 */
async function initAuth() {
    // Always start fresh - clear any previous session
    isGuestMode = false;
    localStorage.removeItem('guestMode');
    currentUser = null;
    authToken = null;
    
    // Check if auth is available on the server (with timeout)
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
        
        const response = await fetch('/api/auth/status', { signal: controller.signal });
        clearTimeout(timeoutId);
        
        const data = await response.json();
        authAvailable = data.available;
        
        if (!authAvailable) {
            console.log('Authentication not configured on server - showing auth gate anyway');
        }
    } catch (error) {
        console.log('Auth status check skipped:', error.name === 'AbortError' ? 'timeout' : error.message);
        authAvailable = false;
    }
    
    // Initialize Firebase
    try {
        firebaseApp = firebase.initializeApp(firebaseConfig);
        firebaseAuth = firebase.auth();
        
        // Sign out any existing user so we always start with login screen
        if (firebaseAuth.currentUser) {
            await firebaseAuth.signOut();
            console.log('Signed out previous session');
        }
        
        // Listen for auth state changes
        firebaseAuth.onAuthStateChanged(handleAuthStateChange);
        
        authInitialized = true;
        console.log('Firebase Auth initialized');
        
        // Show login screen
        showAuthGate();
    } catch (error) {
        console.error('Failed to initialize Firebase:', error);
        // Show auth gate even if Firebase fails
        showAuthGate();
    }
}

/**
 * Handle Firebase auth state changes
 */
async function handleAuthStateChange(user) {
    console.log('Auth state changed:', user ? user.email : 'signed out');
    
    if (user) {
        // User is signed in
        currentUser = user;
        isGuestMode = false;
        localStorage.removeItem('guestMode');
        
        // Store Firebase UID for game.js to access
        localStorage.setItem('firebaseUid', user.uid);
        sessionStorage.setItem('firebaseUid', user.uid);
        console.log('Stored Firebase UID:', user.uid);
        
        // Hide auth gate and show main content IMMEDIATELY - don't wait for token
        hideAuthGate();
        updateAuthUI();
        
        // Update the player name input with display name
        const nameInput = document.getElementById('playerNameInput');
        if (nameInput && user.displayName) {
            nameInput.value = user.displayName;
            localStorage.setItem('playerName', user.displayName);
        }
        
        // Get the ID token in background (non-blocking with timeout)
        // Note: Server verification is skipped - game works with client-side auth only
        if (!authToken) {
            (async () => {
                try {
                    const tokenPromise = user.getIdToken();
                    const timeoutPromise = new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Token timeout')), 5000)
                    );
                    authToken = await Promise.race([tokenPromise, timeoutPromise]);
                    console.log('Auth token obtained');
                    // Skip server verification - it's not needed for game functionality
                    // Profile/stats can be fetched later when user views profile
                } catch (error) {
                    console.log('Token fetch skipped:', error.message);
                }
            })();
        }
        
    } else {
        // User is signed out
        currentUser = null;
        authToken = null;
        
        // Check if guest mode
        if (isGuestMode) {
            hideAuthGate();
        } else {
            showAuthGate();
        }
        
        updateAuthUI();
    }
}

/**
 * Verify the token with the server
 * Non-blocking with timeout - game works even if this fails
 */
async function verifyTokenWithServer() {
    if (!authToken) return null;
    
    // Create an AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    try {
        const response = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            return data.user;
        }
    } catch (error) {
        clearTimeout(timeoutId);
        // Log but don't throw - game should work without server verification
        if (error.name === 'AbortError') {
            console.log('Token verification timed out (server may be slow) - continuing without server verification');
        } else {
            console.log('Token verification failed:', error.message || error);
        }
    }
    
    return null;
}

// =============================================================================
// AUTH GATE (Login/Register Screen)
// =============================================================================

/**
 * Show the auth gate (blocks main content)
 */
function showAuthGate() {
    console.log('showAuthGate called');
    const gate = document.getElementById('authGate');
    const mainContent = document.getElementById('mainContent');
    const authHeader = document.getElementById('authHeader');
    
    console.log('Gate element:', gate);
    console.log('MainContent element:', mainContent);
    
    if (gate) {
        gate.style.display = 'flex';
    }
    if (mainContent) {
        mainContent.style.display = 'none';
    }
    // Hide the top-right auth header on the login screen
    if (authHeader) {
        authHeader.style.display = 'none';
    }
}

/**
 * Hide the auth gate and show main content
 */
function hideAuthGate() {
    console.log('hideAuthGate called');
    const gate = document.getElementById('authGate');
    const mainContent = document.getElementById('mainContent');
    const authHeader = document.getElementById('authHeader');
    
    console.log('Gate element:', gate);
    console.log('MainContent element:', mainContent);
    
    if (gate) {
        gate.style.display = 'none';
        console.log('Gate hidden');
    } else {
        console.error('authGate element not found!');
    }
    
    if (mainContent) {
        mainContent.style.display = 'block';
        console.log('MainContent shown');
    } else {
        console.error('mainContent element not found!');
    }
    
    // Show the auth header when logged in
    if (authHeader) {
        authHeader.style.display = 'block';
    }
    
    // Also hide the modal if it's open
    hideAuthModal();
}

/**
 * Continue as guest
 */
function continueAsGuest() {
    isGuestMode = true;
    localStorage.setItem('guestMode', 'true');
    hideAuthGate();
    updateAuthUI();
}

// =============================================================================
// AUTH UI UPDATES
// =============================================================================

/**
 * Update the auth-related UI based on current state
 */
function updateAuthUI() {
    const authStatus = document.getElementById('authStatus');
    if (!authStatus) return;
    
    // Always show auth header
    const authHeader = document.getElementById('authHeader');
    if (authHeader) {
        authHeader.style.display = 'block';
    }
    
    // Update the player name input based on auth state
    updatePlayerNameInput();
    
    if (currentUser) {
        // User is logged in - show profile, leaderboard, and logout buttons
        const displayName = currentUser.displayName || currentUser.email?.split('@')[0] || 'Player';
        authStatus.innerHTML = `
            <a href="/profile" class="auth-user-btn" id="userProfileBtn">
                <span class="auth-avatar">👤</span>
                <span class="auth-username">${escapeHtml(displayName)}</span>
            </a>
            <a href="/leaderboard" class="auth-leaderboard-btn" id="headerLeaderboardBtn" title="Leaderboard">
                🏆
            </a>
            <button class="auth-logout-btn" id="headerLogoutBtn" title="Logout">
                🚪
            </button>
        `;
        
        // Setup logout button (profile and leaderboard are now links)
        document.getElementById('headerLogoutBtn')?.addEventListener('click', handleLogout);
    } else if (isGuestMode) {
        // Guest mode
        authStatus.innerHTML = `
            <span class="auth-guest-label">Guest</span>
            <button class="auth-login-btn" id="showLoginBtn">
                Login
            </button>
            <a href="/leaderboard" class="auth-leaderboard-btn" id="headerLeaderboardBtn" title="Leaderboard">
                🏆
            </a>
        `;
        
        // Setup login button (leaderboard is now a link)
        document.getElementById('showLoginBtn')?.addEventListener('click', showAuthModal);
    } else {
        // Not logged in, not guest - this shouldn't happen normally
        authStatus.innerHTML = `
            <button class="auth-login-btn" id="showLoginBtn">
                Login / Register
            </button>
        `;
        document.getElementById('showLoginBtn')?.addEventListener('click', showAuthModal);
    }
}

/**
 * Update the player name input based on authentication state
 * - Authenticated users: locked to their display name
 * - Guest users: editable
 */
function updatePlayerNameInput() {
    const nameInput = document.getElementById('playerNameInput');
    if (!nameInput) return;
    
    if (currentUser) {
        // Authenticated user - lock the input to their display name
        const displayName = currentUser.displayName || currentUser.email?.split('@')[0] || 'Player';
        nameInput.value = displayName;
        nameInput.disabled = true;
        nameInput.readOnly = true;
        nameInput.classList.add('locked');
        nameInput.title = 'Logged in as ' + displayName;
        nameInput.placeholder = displayName;
        localStorage.setItem('playerName', displayName);
        sessionStorage.setItem('playerName', displayName);
    } else if (isGuestMode) {
        // Guest mode - allow editing
        nameInput.disabled = false;
        nameInput.readOnly = false;
        nameInput.classList.remove('locked');
        nameInput.title = '';
        nameInput.placeholder = 'Your name';
        // Load any previously saved guest name
        const savedName = localStorage.getItem('playerName');
        if (savedName && !nameInput.value) {
            nameInput.value = savedName;
        }
    }
}

// =============================================================================
// AUTH MODAL
// =============================================================================

/**
 * Show the auth modal
 */
function showAuthModal() {
    const overlay = document.getElementById('authModalOverlay');
    if (overlay) {
        overlay.classList.add('visible');
        // Focus on email input
        setTimeout(() => {
            document.getElementById('loginEmail')?.focus();
        }, 100);
    }
}

/**
 * Hide the auth modal
 */
function hideAuthModal() {
    const overlay = document.getElementById('authModalOverlay');
    if (overlay) {
        overlay.classList.remove('visible');
    }
    
    // Clear form errors
    const loginError = document.getElementById('loginError');
    const registerError = document.getElementById('registerError');
    if (loginError) loginError.textContent = '';
    if (registerError) registerError.textContent = '';
    
    // Reset button states
    document.querySelectorAll('.auth-submit-btn').forEach(btn => {
        const btnText = btn.querySelector('.btn-text');
        const btnLoading = btn.querySelector('.btn-loading');
        if (btnText) btnText.style.display = 'inline';
        if (btnLoading) btnLoading.style.display = 'none';
        btn.disabled = false;
    });
    
    // Clear form inputs
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    if (loginForm) loginForm.reset();
    if (registerForm) registerForm.reset();
}

/**
 * Switch between login and register tabs
 */
function switchAuthTab(tab) {
    const tabs = document.querySelectorAll('.auth-tab');
    const forms = document.querySelectorAll('.auth-form');
    
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    forms.forEach(f => f.classList.toggle('active', f.id === `${tab}Form`));
    
    // Clear errors
    document.getElementById('loginError').textContent = '';
    document.getElementById('registerError').textContent = '';
    
    // Focus on first input
    setTimeout(() => {
        if (tab === 'login') {
            document.getElementById('loginEmail')?.focus();
        } else {
            document.getElementById('registerName')?.focus();
        }
    }, 100);
}

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');
    const submitBtn = e.target.querySelector('.auth-submit-btn');
    
    // Show loading state
    submitBtn.querySelector('.btn-text').style.display = 'none';
    submitBtn.querySelector('.btn-loading').style.display = 'inline-flex';
    submitBtn.disabled = true;
    errorEl.textContent = '';
    
    try {
        const userCredential = await firebaseAuth.signInWithEmailAndPassword(email, password);
        console.log('Login successful:', userCredential.user.email);
        
        // Get token (with timeout to prevent hanging)
        console.log('Getting token...');
        try {
            const tokenPromise = userCredential.user.getIdToken();
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Token timeout')), 3000)
            );
            authToken = await Promise.race([tokenPromise, timeoutPromise]);
            console.log('Token obtained');
        } catch (tokenErr) {
            console.log('Token fetch skipped:', tokenErr.message);
        }
        currentUser = userCredential.user;
        
        // Skip server verification - game works with client-side auth only
        
        // Update player name
        const nameInput = document.getElementById('playerNameInput');
        if (nameInput && userCredential.user.displayName) {
            nameInput.value = userCredential.user.displayName;
            localStorage.setItem('playerName', userCredential.user.displayName);
        }
        
        console.log('About to hide modal and gate...');
        
        // Close modal and hide gate
        hideAuthModal();
        hideAuthGate();
        updateAuthUI();
        
        console.log('UI updated successfully');
        
        // Reset button
        submitBtn.querySelector('.btn-text').style.display = 'inline';
        submitBtn.querySelector('.btn-loading').style.display = 'none';
        submitBtn.disabled = false;
        
        // Reload page to ensure clean state with proper socket connection
        window.location.reload();
        
    } catch (error) {
        console.error('Login error:', error);
        errorEl.textContent = getAuthErrorMessage(error.code);
        
        // Reset button
        submitBtn.querySelector('.btn-text').style.display = 'inline';
        submitBtn.querySelector('.btn-loading').style.display = 'none';
        submitBtn.disabled = false;
    }
}

/**
 * Handle register form submission
 */
async function handleRegister(e) {
    e.preventDefault();
    
    const displayName = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    const errorEl = document.getElementById('registerError');
    const submitBtn = e.target.querySelector('.auth-submit-btn');
    
    // Validate passwords match
    if (password !== passwordConfirm) {
        errorEl.textContent = 'Passwords do not match';
        return;
    }
    
    // Show loading state
    submitBtn.querySelector('.btn-text').style.display = 'none';
    submitBtn.querySelector('.btn-loading').style.display = 'inline-flex';
    submitBtn.disabled = true;
    errorEl.textContent = '';
    
    try {
        // Create the user in Firebase Auth
        const userCredential = await firebaseAuth.createUserWithEmailAndPassword(email, password);
        console.log('Registration successful:', userCredential.user.email);
        
        // Update display name with short timeout (non-critical)
        if (displayName) {
            try {
                const updatePromise = userCredential.user.updateProfile({
                    displayName: displayName
                });
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Profile update timeout')), 2000)
                );
                await Promise.race([updatePromise, timeoutPromise]);
                console.log('Display name updated');
            } catch (profileError) {
                // Non-critical - continue without display name update
                console.log('Display name update skipped:', profileError.message);
            }
        }
        
        // Get token with short timeout
        console.log('Getting token...');
        try {
            const tokenPromise = userCredential.user.getIdToken();
            const tokenTimeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Token fetch timeout')), 2000)
            );
            authToken = await Promise.race([tokenPromise, tokenTimeoutPromise]);
            console.log('Token obtained');
        } catch (tokenError) {
            console.log('Token fetch failed:', tokenError.message);
            // Continue anyway - the user is created
        }
        
        currentUser = userCredential.user;
        
        // Skip server verification - game works with client-side auth only
        // Profile will be created when user accesses profile features
        
        // Update player name
        const nameInput = document.getElementById('playerNameInput');
        if (nameInput) {
            const name = displayName || email.split('@')[0];
            nameInput.value = name;
            localStorage.setItem('playerName', name);
        }
        
        console.log('About to hide modal and gate...');
        
        // Close modal and hide gate
        hideAuthModal();
        hideAuthGate();
        updateAuthUI();
        
        console.log('UI updated successfully');
        
        // Reset button
        submitBtn.querySelector('.btn-text').style.display = 'inline';
        submitBtn.querySelector('.btn-loading').style.display = 'none';
        submitBtn.disabled = false;
        
        // Reload page to ensure clean state with proper socket connection
        window.location.reload();
        
    } catch (error) {
        console.error('Register error:', error);
        errorEl.textContent = getAuthErrorMessage(error.code);
        
        // Reset button
        submitBtn.querySelector('.btn-text').style.display = 'inline';
        submitBtn.querySelector('.btn-loading').style.display = 'none';
        submitBtn.disabled = false;
    }
}

/**
 * Get user-friendly error message from Firebase error code
 */
function getAuthErrorMessage(code) {
    const messages = {
        'auth/email-already-in-use': 'Email is already registered',
        'auth/invalid-email': 'Invalid email address',
        'auth/weak-password': 'Password is too weak (min 6 characters)',
        'auth/user-not-found': 'No account found with this email',
        'auth/wrong-password': 'Incorrect password',
        'auth/invalid-credential': 'Invalid email or password',
        'auth/too-many-requests': 'Too many attempts. Please try again later',
        'auth/network-request-failed': 'Network error. Check your connection'
    };
    
    return messages[code] || 'An error occurred. Please try again.';
}

// =============================================================================
// PROFILE MODAL
// =============================================================================

/**
 * Show the profile modal
 */
async function showProfileModal() {
    const overlay = document.getElementById('profileModalOverlay');
    if (!overlay || !currentUser) return;
    
    // Update profile info
    document.getElementById('profileName').textContent = currentUser.displayName || 'Player';
    document.getElementById('profileEmail').textContent = currentUser.email || '';
    
    // Fetch user stats
    try {
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const stats = data.profile?.stats || {};
            
            document.getElementById('statGamesPlayed').textContent = stats.gamesPlayed || 0;
            document.getElementById('statGamesWon').textContent = stats.gamesWon || 0;
            
            const winRate = stats.gamesPlayed > 0 
                ? Math.round((stats.gamesWon / stats.gamesPlayed) * 100) 
                : 0;
            document.getElementById('statWinRate').textContent = `${winRate}%`;
            document.getElementById('statHighScore').textContent = stats.highestScore || 0;
        }
    } catch (error) {
        console.error('Failed to fetch profile:', error);
    }
    
    overlay.classList.add('visible');
}

/**
 * Hide the profile modal
 */
function hideProfileModal() {
    const overlay = document.getElementById('profileModalOverlay');
    if (overlay) {
        overlay.classList.remove('visible');
    }
}

/**
 * Handle logout
 */
async function handleLogout() {
    try {
        await firebaseAuth.signOut();
        hideProfileModal();
        
        // Clear auth state
        currentUser = null;
        authToken = null;
        isGuestMode = false;
        
        // Clear stored auth-related data
        localStorage.removeItem('guestMode');
        localStorage.removeItem('playerName');
        sessionStorage.removeItem('playerName');
        
        // Show auth gate after logout
        showAuthGate();
        updateAuthUI();
        
        // Reload to ensure clean state
        window.location.reload();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// =============================================================================
// LEADERBOARD MODAL
// =============================================================================

/**
 * Show the leaderboard modal
 */
async function showLeaderboardModal() {
    const overlay = document.getElementById('leaderboardModalOverlay');
    const content = document.getElementById('leaderboardContent');
    if (!overlay || !content) return;
    
    // Show loading state
    content.innerHTML = `
        <div class="leaderboard-loading">
            <div class="loading-spinner"></div>
            <span>Loading leaderboard...</span>
        </div>
    `;
    
    overlay.classList.add('visible');
    
    // Fetch leaderboard
    try {
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch('/api/leaderboard?limit=20', { headers });
        
        if (response.ok) {
            const data = await response.json();
            renderLeaderboard(data.leaderboard, data.currentUserUid);
        } else {
            content.innerHTML = `
                <div class="leaderboard-error">
                    <span>Failed to load leaderboard</span>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to fetch leaderboard:', error);
        content.innerHTML = `
            <div class="leaderboard-error">
                <span>Failed to load leaderboard</span>
            </div>
        `;
    }
}

/**
 * Render the leaderboard
 */
function renderLeaderboard(leaderboard, currentUserUid) {
    const content = document.getElementById('leaderboardContent');
    if (!content) return;
    
    if (!leaderboard || leaderboard.length === 0) {
        content.innerHTML = `
            <div class="leaderboard-empty">
                <span>🏆</span>
                <p>No players yet. Be the first!</p>
            </div>
        `;
        return;
    }
    
    const html = leaderboard.map((player, index) => {
        const isCurrentUser = player.uid === currentUserUid;
        const rankIcon = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${player.rank}`;
        
        return `
            <div class="leaderboard-item ${isCurrentUser ? 'current-user' : ''}">
                <span class="lb-rank">${rankIcon}</span>
                <span class="lb-name">${escapeHtml(player.displayName)}</span>
                <span class="lb-wins">${player.gamesWon} wins</span>
                <span class="lb-winrate">${player.winRate}%</span>
            </div>
        `;
    }).join('');
    
    content.innerHTML = `<div class="leaderboard-list">${html}</div>`;
}

/**
 * Hide the leaderboard modal
 */
function hideLeaderboardModal() {
    const overlay = document.getElementById('leaderboardModalOverlay');
    if (overlay) {
        overlay.classList.remove('visible');
    }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Get the current auth token (for API calls)
 */
function getAuthToken() {
    return authToken;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return currentUser !== null;
}

// =============================================================================
// EVENT LISTENERS
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize auth
    initAuth();
    
    // Auth gate buttons
    document.getElementById('gateLoginBtn')?.addEventListener('click', () => {
        switchAuthTab('login');
        showAuthModal();
    });
    document.getElementById('gateRegisterBtn')?.addEventListener('click', () => {
        switchAuthTab('register');
        showAuthModal();
    });
    document.getElementById('gateGuestBtn')?.addEventListener('click', continueAsGuest);
    
    // Auth modal events
    document.getElementById('authModalClose')?.addEventListener('click', hideAuthModal);
    document.getElementById('authModalOverlay')?.addEventListener('click', (e) => {
        if (e.target.id === 'authModalOverlay') hideAuthModal();
    });
    
    // Auth tab switching
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => switchAuthTab(tab.dataset.tab));
    });
    
    // Form submissions
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    
    // Profile modal events
    document.getElementById('profileModalClose')?.addEventListener('click', hideProfileModal);
    document.getElementById('profileModalOverlay')?.addEventListener('click', (e) => {
        if (e.target.id === 'profileModalOverlay') hideProfileModal();
    });
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    document.getElementById('viewLeaderboardBtn')?.addEventListener('click', () => {
        hideProfileModal();
        showLeaderboardModal();
    });
    
    // Leaderboard modal events
    document.getElementById('leaderboardModalClose')?.addEventListener('click', hideLeaderboardModal);
    document.getElementById('leaderboardModalOverlay')?.addEventListener('click', (e) => {
        if (e.target.id === 'leaderboardModalOverlay') hideLeaderboardModal();
    });
    
    // Escape key to close modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideAuthModal();
            hideProfileModal();
            hideLeaderboardModal();
        }
    });
});

// Export functions for use in other modules
window.authModule = {
    getAuthToken,
    isAuthenticated,
    showAuthModal,
    showLeaderboardModal,
    continueAsGuest
};
