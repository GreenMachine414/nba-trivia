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

backBtn.addEventListener('click', async (e) => {
  clearGameTimer();   // 1. stop the countdown - doesn't touch gameInProgress at all

  if (screens.trivia.classList.contains('active') && isGameInProgress() && getQuestionsAnswered() > 0) {
    // 2. check gameInProgress WHILE it's still accurately true, and record if warranted
    await recordGameResult(getQuestionsAnswered());
  }

  endGame();   // 3. NOW it's safe to set gameInProgress = false, since nothing needs to read it anymore

  const target = e.currentTarget.dataset.target;
  if (target) showScreen(target);
});

updateAccountLink();
showScreen('home');