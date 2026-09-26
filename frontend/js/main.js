import { showScreen, backBtn, screens } from './screens.js';
import { updateAccountLink } from './session.js';
import { renderAccountScreen } from './auth.js';
import { initLeaderboardTabs } from './leaderboard.js';
import { startGame, isGameInProgress, getQuestionsAnswered, clearGameTimer, endGame, recordGameResult } from './trivia.js';
import { startGuessPlayerGame, isGuessPlayerGameInProgress, endGuessPlayerGame, recordGuessPlayerResult } from './guessplayer.js';
import { withLoading } from './loading.js';

initLeaderboardTabs();

document.getElementById('play-btn').addEventListener('click', () => showScreen('options'));
document.getElementById('nba-trivia-card').addEventListener('click', startGame);
document.getElementById('guess-player-card').addEventListener('click', startGuessPlayerGame);

document.getElementById('account-link').addEventListener('click', () => {
  showScreen('account');
  renderAccountScreen();
});

backBtn.addEventListener('click', async (e) => {
  const target = e.currentTarget.dataset.target;

  await withLoading(async () => {
    if (screens.trivia.classList.contains('active') && isGameInProgress()) {
      clearGameTimer();
      await recordGameResult(getQuestionsAnswered());
      endGame();
    }

    if (screens['guess-player'].classList.contains('active') && isGuessPlayerGameInProgress()) {
      const roundsPlayed = Number(document.querySelector('.progress-label')?.textContent.match(/Round (\d+)/)?.[1] || 1);
      await recordGuessPlayerResult(false, roundsPlayed);
      endGuessPlayerGame();
    }

    if (target) showScreen(target);
  });
});

updateAccountLink();
showScreen('home');