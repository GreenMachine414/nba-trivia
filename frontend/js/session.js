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

export function clearSession() {
  localStorage.removeItem('statline_token');
  localStorage.removeItem('statline_username');
  updateAccountLink();
}

export function updateAccountLink() {
  const accountLink = document.getElementById('account-link');
  accountLink.textContent = getUsername() || 'Log In';
}