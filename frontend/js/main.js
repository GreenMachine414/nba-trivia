import { showScreen, backBtn, screens } from './screens.js';
import { updateAccountLink } from './session.js';
import { renderAccountScreen } from './auth.js';
import { initLeaderboardTabs } from './leaderboard.js';
import { startGame, isGameInProgress, getQuestionsAnswered, stopTimer, recordGameResult } from './trivia.js';

initLeaderboardTabs();

document.getElementById('play-btn').addEventListener('click', () => showScreen('options'));
document.getElementById('nba-trivia-card').addEventListener('click', startGame);

document.getElementById('account-link').addEventListener('click', () => {
  showScreen('account');
  renderAccountScreen();
});

backBtn.addEventListener('click', (e) => {
  stopTimer();
  console.log('Back clicked - gameInProgress:', isGameInProgress(), 'questionsAnswered:', getQuestionsAnswered());

  if (screens.trivia.classList.contains('active') && isGameInProgress() && getQuestionsAnswered() > 0) {
    recordGameResult(getQuestionsAnswered());
  }

  const target = e.currentTarget.dataset.target;
  if (target) showScreen(target);
});

updateAccountLink();
showScreen('home');