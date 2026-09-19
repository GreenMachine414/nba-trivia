import { getToken } from './session.js';
import { showScreen } from './screens.js';

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'https://nba-trivia-production.up.railway.app';

const questionTypeColors = {
  'Season Average': '#6E93A6',
  'Career Path': '#9B7EBD',
  'Draft': '#4A9B7F',
  'Player Identity': '#C97B4A',
  'Coaching Staff': '#5B7DB1',
  'Awards': '#B0559C',
};

const questionEndpoints = [
  '/trivia/season_average',
  '/trivia/career_path',
  '/trivia/missing_stat',
  '/trivia/season_guess',
  '/trivia/team_guess',
  '/trivia/missing_stop',
  '/trivia/team_count',
  '/trivia/draft_player',
  '/trivia/overall_pick',
  '/trivia/draft_organization',
  '/trivia/player_from_organization',
  '/trivia/jersey_player',
  '/trivia/jersey_number',
  '/trivia/career_jerseys',
  '/trivia/coaching_staff',
  '/trivia/head_coach',
  '/trivia/award_winner',
  '/trivia/career_resume',
];

const TOTAL_QUESTIONS = 10;
const QUESTION_TIME_LIMIT = 15;
const TIMER_TICK_MS = 100;
const REVEAL_DELAY_MS = 500;

const triviaPanel = document.getElementById('trivia-panel');

let questionNumber = 0;
let questionsAnswered = 0;
let correctCount = 0;
let timerInterval = null;
let questionLocked = false;
let gameInProgress = false;

export function isGameInProgress() {
  return gameInProgress;
}

export function getQuestionsAnswered() {
  return questionsAnswered;
}

export function clearGameTimer() {
  clearInterval(timerInterval);
}

export function endGame() {
  gameInProgress = false;
}

function shuffle(array) {
  return array
    .map(item => ({ item, sort: Math.random() }))
    .sort((a, b) => a.sort - b.sort)
    .map(({ item }) => item);
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function startGame() {
  questionNumber = 0;
  questionsAnswered = 0;
  correctCount = 0;
  gameInProgress = true;
  showScreen('trivia');
  triviaPanel.innerHTML = '<p class="trivia-loading">Loading question…</p>';
  askNextQuestion();
}

function askNextQuestion() {
  questionNumber += 1;
  loadQuestion();
}

// No loading flash here on purpose - the previous question's feedback
// stays fully visible until the new question is ready to swap in.
async function loadQuestion() {
  const endpoint = questionEndpoints[Math.floor(Math.random() * questionEndpoints.length)];

  try {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }
    const data = await response.json();
    if (data.error) {
      triviaPanel.innerHTML = `<p class="trivia-loading">${data.error}</p>`;
      return;
    }
    renderQuestion(data);
  } catch (err) {
    triviaPanel.innerHTML =
      `<p class="trivia-loading">Couldn't reach the backend: ${err.message}</p>`;
  }
}

function renderQuestion(data) {
  const dotColor = questionTypeColors[data.question_type] || '#9C9284';
  const choices = shuffle(data.choices);

  const badgeRow = `
    <div class="question-type-row">
      <div class="question-type-left">
        <span class="question-type-dot" style="background:${dotColor}"></span>
        <span class="question-type-label">${data.question_type}</span>
      </div>
      <span class="progress-label">Question ${questionNumber} of ${TOTAL_QUESTIONS}</span>
    </div>
    <div class="timer-row">
      <div class="timer-track"><div class="timer-fill" id="timer-fill"></div></div>
      <span class="timer-value" id="timer-value">${QUESTION_TIME_LIMIT}</span>
    </div>
  `;

  if (data.path) {
    triviaPanel.innerHTML = `
      ${badgeRow}
      <div class="path-layout">
        <div class="path-list">
          ${data.path.map((stop, i) => `
            <div class="path-row ${i === data.hidden_index ? 'path-row-hidden' : ''}">
              <span class="path-team">${stop.team}</span>
              <span class="path-season">${
                stop.start_season === stop.end_season
                  ? stop.start_season
                  : `${stop.start_season} to ${stop.end_season}`
              }</span>
            </div>
          `).join('')}
        </div>
        <div class="path-side">
          <p class="question-text">${data.question}</p>
          <div class="choices-grid" id="choices-grid"></div>
          <p class="trivia-feedback" id="trivia-feedback"></p>
        </div>
      </div>
    `;
  } else if (data.staff) {
    triviaPanel.innerHTML = `
      ${badgeRow}
      <div class="path-layout">
        <div class="path-list">
          ${data.staff.map(coach => `
            <div class="path-row">
              <span class="path-team">${coach.coach_name}</span>
              <span class="path-season">${coach.coach_type}</span>
            </div>
          `).join('')}
        </div>
        <div class="path-side">
          <p class="question-text">${data.question}</p>
          <div class="choices-grid" id="choices-grid"></div>
          <p class="trivia-feedback" id="trivia-feedback"></p>
        </div>
      </div>
    `;
  } else if (data.resume) {
    triviaPanel.innerHTML = `
      ${badgeRow}
      <div class="path-layout">
        <div class="path-list resume-wide">
          ${data.resume.map(item => `
            <div class="path-row">
              <span class="resume-text">${item}</span>
            </div>
          `).join('')}
        </div>
        <div class="path-side">
          <p class="question-text">${data.question}</p>
          <div class="choices-grid" id="choices-grid"></div>
          <p class="trivia-feedback" id="trivia-feedback"></p>
        </div>
      </div>
    `;
  } else if (data.stats) {
    const hideStat = (key) => data.hidden_stat === key;
    const statValue = data.stats;

    const statCells = [
      { key: 'ppg', label: 'PPG', value: statValue.ppg },
      { key: 'rpg', label: 'RPG', value: statValue.rpg },
      { key: 'apg', label: 'APG', value: statValue.apg },
      { key: 'spg', label: 'SPG', value: statValue.spg },
      { key: 'bpg', label: 'BPG', value: statValue.bpg },
    ].filter(cell => cell.value !== null && cell.value !== undefined);

    triviaPanel.innerHTML = `
      ${badgeRow}
      <div class="stat-grid" style="grid-template-columns: repeat(${statCells.length}, 1fr);">
        ${statCells.map(cell => `
          <div class="stat-cell">
            <div class="stat-value">${hideStat(cell.key) ? '?' : cell.value}</div>
            <div class="stat-label">${cell.label}</div>
          </div>
        `).join('')}
      </div>
      <p class="question-text">${data.question}</p>
      <div class="choices-grid" id="choices-grid"></div>
      <p class="trivia-feedback" id="trivia-feedback"></p>
    `;
  } else {
    triviaPanel.innerHTML = `
      ${badgeRow}
      <p class="question-text">${data.question}</p>
      <div class="choices-grid" id="choices-grid"></div>
      <p class="trivia-feedback" id="trivia-feedback"></p>
    `;
  }

  const choicesGrid = document.getElementById('choices-grid');

  choices.forEach(choice => {
    const btn = document.createElement('button');
    btn.className = 'choice-btn';
    btn.textContent = choice;
    btn.addEventListener('click', () => submitGuess(data.question_id, choice));
    choicesGrid.appendChild(btn);
  });

  startTimer(data.question_id);
}

function startTimer(questionId) {
  questionLocked = false;
  clearInterval(timerInterval);

  const startTime = Date.now();
  const fillEl = document.getElementById('timer-fill');
  const valueEl = document.getElementById('timer-value');

  timerInterval = setInterval(() => {
    const elapsed = (Date.now() - startTime) / 1000;
    const remaining = Math.max(0, QUESTION_TIME_LIMIT - elapsed);

    fillEl.style.width = `${(remaining / QUESTION_TIME_LIMIT) * 100}%`;
    valueEl.textContent = Math.ceil(remaining);
    fillEl.classList.toggle('urgent', remaining <= 5);

    if (remaining <= 0) {
      clearInterval(timerInterval);
      if (!questionLocked) {
        submitGuess(questionId, '', true);
      }
    }
  }, TIMER_TICK_MS);
}

function playRevealAnimation(overlay) {
  overlay.classList.add('active');
  const ball = overlay.querySelector('.reveal-ball');
  // Restart the CSS animation each time by forcing a reflow
  ball.style.animation = 'none';
  void ball.offsetWidth;
  ball.style.animation = '';
}

async function submitGuess(questionId, guess, timedOut = false) {
  if (questionLocked) return;
  questionLocked = true;
  clearInterval(timerInterval);

  const buttons = document.querySelectorAll('.choice-btn');
  buttons.forEach(btn => { btn.disabled = true; });

  const overlay = document.getElementById('answer-reveal-overlay');
  playRevealAnimation(overlay);

  try {
    const [response] = await Promise.all([
      fetch(`${API_BASE}/trivia/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: questionId, guess }),
      }),
      wait(REVEAL_DELAY_MS),
    ]);

    overlay.classList.remove('active');

    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    const result = await response.json();

    if (result.error) {
      document.getElementById('trivia-feedback').textContent = result.error;
      return;
    }

    if (result.correct) correctCount += 1;
    questionsAnswered += 1;

    buttons.forEach(btn => {
      if (btn.textContent === result.answer) {
        btn.classList.add('correct');
      } else if (btn.textContent === guess) {
        btn.classList.add('incorrect');
      }
    });

    const feedback = document.getElementById('trivia-feedback');
    feedback.textContent = result.correct
      ? 'Correct!'
      : timedOut
        ? `Time's up — it was ${result.answer}.`
        : `Not quite — it was ${result.answer}.`;
    feedback.classList.add(result.correct ? 'correct' : 'incorrect');

    const isLastQuestion = questionNumber >= TOTAL_QUESTIONS;

    const advanceBtn = document.createElement('button');
    advanceBtn.className = 'next-btn';
    advanceBtn.textContent = isLastQuestion ? 'See Results' : 'Next Question';
    advanceBtn.addEventListener('click', isLastQuestion ? showResults : askNextQuestion);
    triviaPanel.appendChild(advanceBtn);

  } catch (err) {
    overlay.classList.remove('active');
    document.getElementById('trivia-feedback').textContent =
      `Couldn't reach the backend: ${err.message}`;
  }
}

function showResults() {
  gameInProgress = false;

  triviaPanel.innerHTML = `
    <h2 class="screen-heading">Results</h2>
    <p class="results-score">${correctCount} / ${TOTAL_QUESTIONS}</p>
    <p class="trivia-desc-static">You got ${correctCount} out of ${TOTAL_QUESTIONS} correct.</p>
    <button class="next-btn" id="play-again-btn">Play Again</button>
  `;

  document.getElementById('play-again-btn').addEventListener('click', startGame);

  recordGameResult();
}

export async function recordGameResult(totalQuestions = TOTAL_QUESTIONS) {
  const token = getToken();
  if (!token) return;

  try {
    await fetch(`${API_BASE}/games/record`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        score: correctCount,
        total_questions: totalQuestions,
        game_mode: 'nba_trivia',
      }),
    });
  } catch (err) {
    console.error('Could not record game result:', err);
  }
}