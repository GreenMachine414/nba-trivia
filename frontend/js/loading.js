const overlay = document.getElementById('loading-overlay');

export function showLoading() {
  overlay.classList.add('active');
}

export function hideLoading() {
  overlay.classList.remove('active');
}

export async function withLoading(action) {
  showLoading();
  try {
    return await action();
  } finally {
    hideLoading();
  }
}