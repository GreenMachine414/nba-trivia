import { setSession, clearSession, getToken, getUsername } from './session.js';

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'https://nba-trivia-zc1c.onrender.com';
  
const accountPanel = document.getElementById('account-panel');

export function renderAccountScreen() {
  const username = getUsername();
  if (username) {
    renderSignedIn(username);
  } else {
    renderAuthForms();
  }
}

function renderAuthForms() {
  accountPanel.innerHTML = `
    <h2 class="screen-heading">Account</h2>

    <form class="auth-form" id="login-form">
      <p class="auth-form-title">Log in</p>
      <input class="auth-input" type="text" name="username" placeholder="Username" required>
      <input class="auth-input" type="password" name="password" placeholder="Password" required>
      <button class="auth-submit-btn" type="submit">Log In</button>
      <p class="auth-error" id="login-error"></p>
    </form>

    <p class="auth-toggle">
      No account? <a href="#" id="show-signup">Sign up</a>
    </p>

    <form class="auth-form hidden" id="signup-form">
      <p class="auth-form-title">Create an account</p>
      <input class="auth-input" type="text" name="username" placeholder="Username" required minlength="3">
      <input class="auth-input" type="password" name="password" placeholder="Password (min 8 characters)" required minlength="8">
      <button class="auth-submit-btn" type="submit">Sign Up</button>
      <p class="auth-error" id="signup-error"></p>
    </form>

    <p class="auth-toggle hidden" id="show-login-wrap">
      Already have an account? <a href="#" id="show-login">Log in</a>
    </p>
  `;

  const loginForm = document.getElementById('login-form');
  const signupForm = document.getElementById('signup-form');
  const showSignup = document.getElementById('show-signup');
  const showLogin = document.getElementById('show-login');
  const showLoginWrap = document.getElementById('show-login-wrap');
  const toggleLine = loginForm.nextElementSibling;

  showSignup.addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.classList.add('hidden');
    toggleLine.classList.add('hidden');
    signupForm.classList.remove('hidden');
    showLoginWrap.classList.remove('hidden');
  });

  showLogin.addEventListener('click', (e) => {
    e.preventDefault();
    signupForm.classList.add('hidden');
    showLoginWrap.classList.add('hidden');
    loginForm.classList.remove('hidden');
    toggleLine.classList.remove('hidden');
  });

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    await handleAuthSubmit('/auth/login', {
      username: formData.get('username'),
      password: formData.get('password'),
    }, 'login-error');
  });

  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(signupForm);
    await handleAuthSubmit('/auth/signup', {
      username: formData.get('username'),
      password: formData.get('password'),
    }, 'signup-error');
  });
}

async function handleAuthSubmit(endpoint, body, errorElId) {
  const errorEl = document.getElementById(errorElId);
  errorEl.textContent = '';

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      errorEl.textContent = data.detail || 'Something went wrong.';
      return;
    }

    setSession(data.token, data.username);
    renderAccountScreen();
  } catch (err) {
    errorEl.textContent = `Couldn't reach the backend: ${err.message}`;
  }
}

async function renderSignedIn(username) {
  accountPanel.innerHTML = `
    <h2 class="screen-heading">Account</h2>
    <p class="account-username">Signed in as ${username}</p>

    <div class="stat-grid" id="account-stat-grid">
      <div class="stat-cell"><div class="stat-value">—</div><div class="stat-label">Games Played</div></div>
      <div class="stat-cell"><div class="stat-value">—</div><div class="stat-label">Avg Score</div></div>
    </div>

    <button class="auth-submit-btn" id="logout-btn">Log Out</button>
  `;

  document.getElementById('logout-btn').addEventListener('click', () => {
    clearSession();
    renderAccountScreen();
  });

  try {
    const response = await fetch(`${API_BASE}/users/me/stats`, {
      headers: { 'Authorization': `Bearer ${getToken()}` },
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearSession();
        renderAccountScreen();
      }
      return;
    }

    const stats = await response.json();
    const grid = document.getElementById('account-stat-grid');

    const avgDisplay = stats.average_score !== null && stats.average_score !== undefined
      ? stats.average_score.toFixed(1)
      : '—';

    grid.innerHTML = `
      <div class="stat-cell"><div class="stat-value">${stats.games_played}</div><div class="stat-label">Games Played</div></div>
      <div class="stat-cell"><div class="stat-value">${avgDisplay}</div><div class="stat-label">Avg Score</div></div>
    `;
  } catch (err) {
    console.error('Could not load stats:', err);
  }
}