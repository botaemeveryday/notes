/*
 * Общий скрипт сайта: липкая шапка, счётчик звёзд, копирование кода,
 * кастомное контекстное меню.
 *
 * Раньше это были: main.js (стор тёмной темы — удалён, темой рулит ОС),
 * grid.js + masonry + imagesLoaded (удалены, сетки на CSS grid),
 * code-copy.js и два инлайновых <script> в партиалах.
 */
(function () {
  'use strict';

  var onReady = function (fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn, { once: true });
    } else {
      fn();
    }
  };

  /* ---------------------------------------------------------------- шапка */
  function initStickyNav() {
    var nav = document.getElementById('site-nav');
    if (!nav || !nav.dataset.stickyClass) return;

    var classes = nav.dataset.stickyClass.split(/\s+/).filter(Boolean);
    var sticky = false;
    var ticking = false;

    var apply = function () {
      var next = window.scrollY > 30;
      if (next !== sticky) {
        sticky = next;
        classes.forEach(function (c) { nav.classList.toggle(c, sticky); });
      }
      ticking = false;
    };

    window.addEventListener('scroll', function () {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(apply);
      }
    }, { passive: true });

    apply();
  }

  /* --------------------------------------------------- счётчик звёзд GitHub */
  function initStarCount() {
    var el = document.getElementById('nav-star-count');
    if (!el || !el.dataset.repo) return;

    var CACHE_KEY = 'gh-stars:' + el.dataset.repo;
    var TTL = 6 * 60 * 60 * 1000; // 6 часов

    var render = function (n) {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(function () {
        el.textContent = n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
        el.style.opacity = '1';
      }, 200);
    };

    // Из кеша — мгновенно и без сетевого запроса на каждой странице.
    try {
      var cached = JSON.parse(sessionStorage.getItem(CACHE_KEY) || 'null');
      if (cached && Date.now() - cached.t < TTL) {
        el.textContent = cached.n >= 1000 ? (cached.n / 1000).toFixed(1) + 'k' : String(cached.n);
        return;
      }
    } catch (e) { /* приватный режим — просто идём в сеть */ }

    fetch('https://api.github.com/repos/' + el.dataset.repo)
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        if (typeof data.stargazers_count !== 'number') return;
        try {
          sessionStorage.setItem(CACHE_KEY, JSON.stringify({ n: data.stargazers_count, t: Date.now() }));
        } catch (e) { /* ignore */ }
        render(data.stargazers_count);
      })
      .catch(function () { el.textContent = '★'; });
  }

  /* ------------------------------------------------------ копирование кода */
  var ICON_COPY =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
  var ICON_CHECK =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>';

  function initCodeCopy() {
    var blocks = document.querySelectorAll('.highlight');
    if (!blocks.length) return;

    blocks.forEach(function (block) {
      var code = block.querySelector('code');
      if (!code) return;

      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-code-btn';
      button.setAttribute('aria-label', 'Копировать код');
      button.setAttribute('title', 'Копировать');
      button.innerHTML = ICON_COPY;
      block.appendChild(button);

      var timer = null;
      button.addEventListener('click', function () {
        copyText(code.innerText).then(function (ok) {
          if (!ok) return;
          clearTimeout(timer);
          button.innerHTML = ICON_CHECK;
          button.classList.add('is-copied');
          timer = setTimeout(function () {
            button.innerHTML = ICON_COPY;
            button.classList.remove('is-copied');
          }, 2000);
        });
      });
    });
  }

  /* Клипборд с фолбэком: navigator.clipboard недоступен по http:// */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(function () { return true; }, fallback);
    }
    return Promise.resolve(fallback());

    function fallback() {
      try {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:-9999px;opacity:0';
        document.body.appendChild(ta);
        ta.select();
        var ok = document.execCommand('copy');
        document.body.removeChild(ta);
        return ok;
      } catch (e) {
        return false;
      }
    }
  }
  window.cnCopyText = copyText;

  /* ------------------------------------------------- контекстное меню */
  function initContextMenu() {
    var menu = document.getElementById('custom-context-menu');
    if (!menu) return;

    var copyTextBtn = document.getElementById('ctx-copy-text');
    var divider = document.getElementById('ctx-divider');
    var pendingText = '';

    function hide() {
      menu.classList.add('opacity-0');
      setTimeout(function () { menu.classList.add('hidden'); }, 150);
    }

    document.addEventListener('contextmenu', function (e) {
      if (e.shiftKey) return;
      e.preventDefault();

      pendingText = String(window.getSelection()).trim();
      var hasSelection = pendingText.length > 0;
      copyTextBtn.style.display = hasSelection ? 'flex' : 'none';
      divider.style.display = hasSelection ? 'block' : 'none';

      menu.classList.remove('hidden');

      var x = Math.min(e.clientX, window.innerWidth - menu.offsetWidth - 10);
      var y = Math.min(e.clientY, window.innerHeight - menu.offsetHeight - 10);
      menu.style.left = Math.max(10, x) + 'px';
      menu.style.top = Math.max(10, y) + 'px';

      requestAnimationFrame(function () { menu.classList.remove('opacity-0'); });
    });

    menu.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-ctx]');
      if (!btn) return;

      switch (btn.dataset.ctx) {
        case 'copy-text': copyText(pendingText); break;
        case 'copy-url':  copyText(window.location.href); break;
        case 'share':
          if (navigator.share) {
            navigator.share({ title: document.title, url: window.location.href }).catch(function () {});
          } else {
            copyText(window.location.href);
          }
          break;
        case 'top': window.scrollTo({ top: 0, behavior: 'smooth' }); break;
      }
      hide();
    });

    document.addEventListener('click', hide);
    window.addEventListener('scroll', hide, { passive: true });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') hide();
    });
  }

  onReady(function () {
    initStickyNav();
    initStarCount();
    initCodeCopy();
    initContextMenu();
  });
})();
