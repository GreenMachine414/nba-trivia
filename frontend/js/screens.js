import { loadLeaderboard } from './leaderboard.js';

export const screens = {
  home: document.getElementById('screen-home'),
  options: document.getElementById('screen-options'),
  trivia: document.getElementById('screen-trivia'),
  account: document.getElementById('screen-account'),
};

const topbar = document.getElementById('topbar');
const backBtn = document.getElementById('back-btn');

const backTargets = {
  options: 'home',
  trivia: 'options',
  account: 'home',
};

export function showScreen(name) {
  Object.entries(screens).forEach(([key, el]) => {
    el.classList.toggle('active', key === name);
  });

  if (name === 'home') {
    topbar.classList.add('hidden');
  } else {
    topbar.classList.remove('hidden');
    backBtn.dataset.target = backTargets[name];
  }

  if (name === 'options') {
    loadLeaderboard();
  }
}

export { backBtn };