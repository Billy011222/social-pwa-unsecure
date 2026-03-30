if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/static/js/serviceWorker.js')
      .then(function (reg) {
        console.log('[App] ServiceWorker registered. Scope:', reg.scope);
        reg.update();
      })
      .catch(function (err) {
        console.error('[App] ServiceWorker registration failed:', err);
      });
  });
}

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

function isSafeInternalPath(url) {
  if (typeof url !== 'string') return false;
  return url.startsWith('/') && !url.startsWith('//') && !url.includes('..');
}

window.addEventListener('DOMContentLoaded', function () {
  const params = new URLSearchParams(window.location.search);
  const msg = params.get('msg');
  const msgBox = document.getElementById('js-msg-box');

  if (msg && msgBox) {
    msgBox.textContent = msg;
    msgBox.style.display = 'block';
  }

  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.style.color = '#e94560';
      link.style.fontWeight = '700';
    }
  });
});

window.addEventListener('message', function (event) {
  if (event.origin !== window.location.origin) {
    return;
  }

  if (
    event.data &&
    typeof event.data === 'object' &&
    event.data.action === 'redirect' &&
    typeof event.data.url === 'string' &&
    isSafeInternalPath(event.data.url)
  ) {
if (event.data && event.data.action === 'redirect' && isSafeInternalPath(event.data.url)) {
  window.location.href = event.data.url;
}
  }

  if (
    event.data &&
    typeof event.data === 'object' &&
    event.data.action === 'setMsg'
  ) {
    const msgBox = document.getElementById('js-msg-box');
    if (msgBox && typeof event.data.content === 'string') {
      msgBox.textContent = event.data.content;
      msgBox.style.display = 'block';
    }
  }
});

let deferredPrompt;
window.addEventListener('beforeinstallprompt', function (e) {
  e.preventDefault();
  deferredPrompt = e;

  const installBtn = document.getElementById('install-btn');
  if (installBtn) {
    installBtn.style.display = 'inline-block';
    installBtn.addEventListener('click', function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function (choiceResult) {
        console.log('[App] Install choice:', choiceResult.outcome);
        deferredPrompt = null;
        installBtn.style.display = 'none';
      });
    }, { once: true });
  }
});

window.socialPwaSecurity = {
  getCsrfToken,
  isSafeInternalPath,
};
