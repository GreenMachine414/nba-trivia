const API_BASE = window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'https://nba-trivia-production.up.railway.app';

const leaderboardList = document.getElementById('leaderboard-list');
const leaderboardTitle = document.querySelector('.leaderboard-title');

let triviaData = null;
let guessPlayerData = null;
let currentGameMode = 'trivia';

export function initLeaderboardTabs() {
  leaderboardTitle.textContent = 'Statline Leaderboard';

  document.getElementById('tab-trivia').addEventListener('click', () => {
    currentGameMode = 'trivia';
    setActiveModeTab('tab-trivia');
    renderCurrentMode();
  });

  document.getElementById('tab-guess-player').addEventListener('click', () => {
    currentGameMode = 'guess_player';
    setActiveModeTab('tab-guess-player');
    renderCurrentMode();
  });
}

function setActiveModeTab(activeId) {
  document.querySelectorAll('.leaderboard-mode-tab').forEach(btn => {
    btn.classList.toggle('active', btn.id === activeId);
  });
}

export async function loadLeaderboard() {
  leaderboardList.innerHTML = '<p class="trivia-loading">Loading leaderboard…</p>';

  try {
    const [triviaResponse, guessPlayerResponse] = await Promise.all([
      fetch(`${API_BASE}/leaderboard/nba_trivia`),
      fetch(`${API_BASE}/leaderboard/guess_player`),
    ]);

    triviaData = triviaResponse.ok ? await triviaResponse.json() : null;
    guessPlayerData = guessPlayerResponse.ok ? await guessPlayerResponse.json() : null;

    renderCurrentMode();
  } catch (err) {
    leaderboardList.innerHTML = `<p class="trivia-loading">Couldn't load leaderboard: ${err.message}</p>`;
  }
}

function renderCurrentMode() {
  const data = currentGameMode === 'trivia' ? triviaData : guessPlayerData;
  const rows = currentGameMode === 'trivia'
    ? data?.by_average_score
    : data?.by_win_pct;

  if (!rows || rows.length === 0) {
    leaderboardList.innerHTML = '<p class="trivia-loading">No games played yet.</p>';
    return;
  }

  leaderboardList.innerHTML = rows.map((row, i) => `
    <div class="leaderboard-row">
      <span class="leaderboard-rank">${i + 1}</span>
      <span class="leaderboard-username">${row.username}</span>
      <span class="leaderboard-value">${
        currentGameMode === 'trivia' ? row.average_score : `${row.win_pct}%`
      }</span>
    </div>
  `).join('');
}