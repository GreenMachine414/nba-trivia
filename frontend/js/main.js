import { showScreen, backBtn, screens } from './screens.js';
import { updateAccountLink } from './session.js';
import { renderAccountScreen } from './auth.js';
import { initLeaderboardTabs } from './leaderboard.js';
import { startGame, isGameInProgress, getQuestionsAnswered, clearGameTimer, endGame, recordGameResult } from './trivia.js';
import { withLoading } from './loading.js';

initLeaderboardTabs();

document.getElementById('play-btn').addEventListener('click', () => showScreen('options'));
document.getElementById('nba-trivia-card').addEventListener('click', startGame);

document.getElementById('account-link').addEventListener('click', () => {
  showScreen('account');
  renderAccountScreen();
});

backBtn.addEventListener('click', async (e) => {
  const target = e.currentTarget.dataset.target;

  await withLoading(async () => {
    clearGameTimer();

    if (screens.trivia.classList.contains('active') && isGameInProgress()) {
      await recordGameResult(getQuestionsAnswered());
    }

    endGame();

    if (target) showScreen(target);
  });
});

updateAccountLink();
showScreen('home');