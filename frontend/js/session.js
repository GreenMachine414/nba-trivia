const API_BASE = window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'https://nba-trivia-production.up.railway.app';

export function getToken() {
  return localStorage.getItem('statline_token');
}

export function getUsername() {
  return localStorage.getItem('statline_username');
}

export function setSession(token, username) {
  localStorage.setItem('statline_token', token);
  localStorage.setItem('statline_username', username);
  updateAccountLink();
}

export async function clearSession() {
  const token = getToken();

  if (token) {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
    } catch (err) {
      console.error('Could not delete session server-side:', err);
    }
  }

  localStorage.removeItem('statline_token');
  localStorage.removeItem('statline_username');
  updateAccountLink();
}

export function updateAccountLink() {
  const accountLink = document.getElementById('account-link');
  accountLink.textContent = getUsername() || 'Log In';
}