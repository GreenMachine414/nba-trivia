import { getToken } from './session.js';
import { showScreen } from './screens.js';
import { invalidateStatsCache } from './auth.js';

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'https://nba-trivia-production.up.railway.app';

const SECTIONS = [
  {
    title: 'Background',
    keys: ['position', 'height', 'team', 'season', 'college', 'overall_pick'],
  },
  {
    title: 'Per game',
    keys: ['ppg', 'rpg', 'apg', 'bpg', 'spg'],
  },
  {
    title: 'Awards',
    keys: ['awards'],
  },
];

const METRIC_LABELS = {
  position: 'Position',
  height: 'Height',
  team: 'Team',
  season: 'Season',
  college: 'College',
  overall_pick: 'Draft pick',
  ppg: 'PPG',
  rpg: 'RPG',
  apg: 'APG',
  bpg: 'BPG',
  spg: 'SPG',
  awards: 'Awards',
};

const TOTAL_ROUNDS = 5;

const gpPanel = document.getElementById('gp-panel');

let currentRound = 0;
let metrics = null;
let trend = [];
let revealOrder = [];
let roundRevealCounts = [];
let answerHash = null;
let searchDebounce = null;
let chartInstance = null;
let gameInProgress = false;

export function isGuessPlayerGameInProgress() {
  return gameInProgress;
}

export function endGuessPlayerGame() {
  gameInProgress = false;
}

async function hashGuess(text) {
  const normalized = text.trim().toLowerCase();
  const data = new TextEncoder().encode(normalized);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

export async function startGuessPlayerGame() {
  currentRound = 1;
  gameInProgress = true;
  showScreen('guess-player');
  gpPanel.innerHTML = '<p class="trivia-loading">Loading player…</p>';

  try {
    const response = await fetch(`${API_BASE}/guess-player/start`);
    if (!response.ok) throw new Error(`Request failed (${response.status})`);

    const data = await response.json();
    if (data.error) {
      gpPanel.innerHTML = `<p class="trivia-loading">${data.error}</p>`;
      return;
    }

    metrics = data.metrics;
    trend = data.trend;
    revealOrder = data.reveal_order;
    roundRevealCounts = data.round_reveal_counts;
    answerHash = data.answer_hash;

    renderRound();
  } catch (err) {
    gpPanel.innerHTML = `<p class="trivia-loading">Couldn't reach the backend: ${err.message}</p>`;
  }
}

function renderRound() {
  const revealCount = roundRevealCounts[currentRound - 1];
  const revealedKeys = new Set(revealOrder.slice(0, revealCount));

  const sectionsHtml = SECTIONS.map(section => `
    <div class="gp-section">
      <p class="gp-section-title">${section.title}</p>
      <div class="gp-stat-grid gp-cols-${section.keys.length}">
        ${section.keys.map(key => {
          const revealed = revealedKeys.has(key);
          return `
            <div class="gp-stat-cell ${revealed ? '' : 'gp-hidden'}">
              <div class="gp-stat-value">${revealed ? metrics[key] : '?'}</div>
              <div class="gp-stat-label">${METRIC_LABELS[key]}</div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `).join('');

  const trendRevealed = revealedKeys.has('trend');

  gpPanel.innerHTML = `
    <div class="gp-layout">
      <div class="gp-main">
        <div class="gp-round-row">
          <span class="progress-label">Round ${currentRound} of ${TOTAL_ROUNDS}</span>
        </div>
        ${sectionsHtml}
        <div class="gp-section">
          <p class="gp-section-title">Career trend</p>
          <div class="gp-chart-wrap ${trendRevealed ? '' : 'gp-hidden'}">
            ${trendRevealed
              ? '<canvas id="gp-trend-chart" role="img" aria-label="Line chart of a career stat trend across seasons"></canvas>'
              : '<div class="gp-chart-placeholder">?</div>'}
          </div>
        </div>
      </div>
      <div class="gp-guess-panel" id="gp-guess-panel">
        <p class="gp-guess-title">Guess the player</p>
        <input type="text" class="gp-search-input" id="gp-search-input" placeholder="Start typing a name…" autocomplete="off">
        <div class="gp-search-results" id="gp-search-results"></div>
        <button class="next-btn gp-lock-btn" id="gp-lock-btn" disabled>Lock in guess</button>
        <p class="trivia-feedback" id="gp-feedback"></p>
      </div>
    </div>
  `;

  if (trendRevealed) {
    renderTrendChart();
  }

  const searchInput = document.getElementById('gp-search-input');
  const searchResults = document.getElementById('gp-search-results');
  const lockBtn = document.getElementById('gp-lock-btn');
  let selectedName = null;

  searchInput.addEventListener('input', () => {
    selectedName = null;
    lockBtn.disabled = true;

    clearTimeout(searchDebounce);
    const query = searchInput.value.trim();

    if (query.length < 2) {
      searchResults.innerHTML = '';
      return;
    }

    searchDebounce = setTimeout(async () => {
      try {
        const response = await fetch(`${API_BASE}/guess-player/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        searchResults.innerHTML = data.names.map(name => `
          <div class="gp-search-result" data-name="${name}">${name}</div>
        `).join('');

        searchResults.querySelectorAll('.gp-search-result').forEach(el => {
          el.addEventListener('click', () => {
            selectedName = el.dataset.name;
            searchInput.value = selectedName;
            searchResults.innerHTML = '';
            lockBtn.disabled = false;
          });
        });
      } catch (err) {
        console.error('Search failed:', err);
      }
    }, 200);
  });

  lockBtn.addEventListener('click', () => submitRoundGuess(selectedName));
}

function renderTrendChart() {
  const canvas = document.getElementById('gp-trend-chart');
  if (!canvas || trend.length === 0) return;

  if (chartInstance) {
    chartInstance.destroy();
  }

  chartInstance = new Chart(canvas, {
    type: 'line',
    data: {
      labels: trend.map(t => t.season),
      datasets: [{
        data: trend.map(t => t.value),
        borderColor: '#FFB627',
        backgroundColor: 'rgba(255, 182, 39, 0.12)',
        fill: true,
        tension: 0.3,
        pointRadius: 3,
        pointBackgroundColor: '#FFB627',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false },
      },
      scales: {
        y: {
          display: true,
          ticks: { color: '#9C9284', font: { size: 10 } },
          grid: { color: 'rgba(244, 241, 234, 0.06)' },
        },
        x: {
          display: true,
          ticks: { color: '#9C9284', font: { size: 9 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 6 },
          grid: { display: false },
        },
      },
    },
  });
}

async function submitRoundGuess(guess) {
  if (!guess) return;

  const guessHash = await hashGuess(guess);
  const correct = guessHash === answerHash;

  if (correct) {
    showResult(true);
    return;
  }

  if (currentRound >= TOTAL_ROUNDS) {
    showResult(false);
    return;
  }

  currentRound += 1;
  renderRound();

  const feedback = document.getElementById('gp-feedback');
  if (feedback) {
    feedback.textContent = 'Incorrect';
    feedback.classList.add('incorrect');
  }
}

function showResult(correct) {
  gameInProgress = false;

  gpPanel.innerHTML = `
    <h2 class="screen-heading">${correct ? 'Correct!' : 'Out of rounds'}</h2>
    <p class="trivia-desc-static">
      ${correct
        ? `You got it in round ${currentRound} of ${TOTAL_ROUNDS}.`
        : `The player was hidden — better luck next time.`}
    </p>
    <button class="next-btn" id="gp-play-again-btn">Play Again</button>
  `;

  document.getElementById('gp-play-again-btn').addEventListener('click', startGuessPlayerGame);

  recordGuessPlayerResult(correct, currentRound);
}

export async function recordGuessPlayerResult(correct, roundsUsed) {
  const token = getToken();
  if (!token) return;

  try {
    await fetch(`${API_BASE}/guess-player/record`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ correct, rounds_used: roundsUsed }),
    });
    invalidateStatsCache();
  } catch (err) {
    console.error('Could not record guess-player result:', err);
  }
}