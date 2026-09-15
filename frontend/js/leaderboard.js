const API_BASE = window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'https://nba-trivia-production.up.railway.app';

let leaderboardData = null;
let leaderboardSort = 'games_played';

export async function loadLeaderboard() {
  const list = document.getElementById('leaderboard-list');
  list.innerHTML = '<p class="trivia-loading">Loading leaderboard…</p>';

  try {
    const response = await fetch(`${API_BASE}/leaderboard/nba_trivia`);
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }
    leaderboardData = await response.json();
    renderLeaderboard();
  } catch (err) {
    list.innerHTML = `<p class="trivia-loading">Couldn't load leaderboard: ${err.message}</p>`;
  }
}

// Interpolates hue from red (0) to green (120) as the score climbs
// from 0 to 10, so the ring color itself communicates performance
// at a glance, not just the number in the middle.
function scoreColor(value) {
  const clamped = Math.max(0, Math.min(10, value));
  const hue = (clamped / 10) * 120;
  return `hsl(${hue}, 70%, 50%)`;
}

function renderLeaderboard() {
  const list = document.getElementById('leaderboard-list');
  if (!leaderboardData) return;

  if (leaderboardSort === 'games_played') {
    const entries = leaderboardData.by_games_played;
    if (entries.length === 0) {
      list.innerHTML = '<p class="trivia-loading">No games played yet.</p>';
      return;
    }
    list.innerHTML = entries.map((entry, i) => `
      <div class="leaderboard-row">
        <span class="leaderboard-rank">${i + 1}</span>
        <span class="leaderboard-username">${entry.username}</span>
        <span class="leaderboard-value">${entry.games_played}</span>
      </div>
    `).join('');
  } else {
    const entries = leaderboardData.by_average_score;
    if (entries.length === 0) {
      list.innerHTML = '<p class="trivia-loading">No completed games yet.</p>';
      return;
    }
    list.innerHTML = entries.map((entry, i) => `
      <div class="leaderboard-row">
        <span class="leaderboard-rank">${i + 1}</span>
        <span class="leaderboard-username">${entry.username}</span>
        <span class="leaderboard-value" style="color:${scoreColor(entry.average_score)}">${entry.average_score.toFixed(1)}</span>
      </div>
    `).join('');
  }
}

export function initLeaderboardTabs() {
  document.querySelectorAll('.leaderboard-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.leaderboard-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      leaderboardSort = tab.dataset.sort;
      renderLeaderboard();
    });
  });
}