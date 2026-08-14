(function () {
  'use strict';

  var onReady = function (fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn, { once: true });
    } else {
      fn();
    }
  };

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

  function initStarCount() {
    var el = document.getElementById('nav-star-count');
    if (!el || !el.dataset.repo) return;

    var CACHE_KEY = 'gh-stars:' + el.dataset.repo;
    var TTL = 6 * 60 * 60 * 1000;

    var render = function (n) {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(function () {
        el.textContent = n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
        el.style.opacity = '1';
      }, 200);
    };

    try {
      var cached = JSON.parse(sessionStorage.getItem(CACHE_KEY) || 'null');
      if (cached && Date.now() - cached.t < TTL) {
        el.textContent = cached.n >= 1000 ? (cached.n / 1000).toFixed(1) + 'k' : String(cached.n);
        return;
      }
    } catch (e) { }

    fetch('https://api.github.com/repos/' + el.dataset.repo)
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        if (typeof data.stargazers_count !== 'number') return;
        try {
          sessionStorage.setItem(CACHE_KEY, JSON.stringify({ n: data.stargazers_count, t: Date.now() }));
        } catch (e) { }
        render(data.stargazers_count);
      })
      .catch(function () { el.textContent = '★'; });
  }

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

(function () {
  'use strict';

  var GAP = 8;
  var DELAY = 120;
  var tip = null;
  var target = null;
  var showTimer = null;
  var hideTimer = null;

  function ensure() {
    if (tip) return tip;
    tip = document.createElement('div');
    tip.className = 'cn-tip';
    tip.setAttribute('role', 'tooltip');
    tip.id = 'cn-tip';
    document.body.appendChild(tip);
    return tip;
  }

  function place(el) {
    var box = el.getBoundingClientRect();
    var w = tip.offsetWidth;
    var h = tip.offsetHeight;
    var prefersTop = el.dataset.cnTipPos === 'top';

    var top = prefersTop ? box.top - h - GAP : box.bottom + GAP;
    if (!prefersTop && top + h > window.innerHeight - 4) top = box.top - h - GAP;
    if (top < 4) top = Math.min(box.bottom + GAP, window.innerHeight - h - 4);

    var left = box.left;
    if (left + w > window.innerWidth - 8) left = window.innerWidth - w - 8;
    if (left < 8) left = 8;

    tip.style.left = Math.round(left) + 'px';
    tip.style.top = Math.round(top) + 'px';
  }

  function show(el) {
    var text = el.getAttribute('data-cn-tip');
    if (!text) return;
    ensure();
    clearTimeout(hideTimer);
    target = el;
    tip.textContent = text;
    tip.style.visibility = 'hidden';
    tip.dataset.open = '0';
    requestAnimationFrame(function () {
      if (target !== el) return;
      tip.style.visibility = '';
      place(el);
      tip.dataset.open = '1';
      el.setAttribute('aria-describedby', 'cn-tip');
    });
  }

  function hide() {
    clearTimeout(showTimer);
    if (!tip || !target) return;
    target.removeAttribute('aria-describedby');
    target = null;
    tip.dataset.open = '0';
    hideTimer = setTimeout(function () {
      if (!target) tip.textContent = '';
    }, 200);
  }

  function pick(node) {
    return node && node.closest ? node.closest('[data-cn-tip]') : null;
  }

  function schedule(el) {
    clearTimeout(showTimer);
    if (!el || el === target) return;
    if (el.title) { el.dataset.cnTitle = el.title; el.removeAttribute('title'); }
    showTimer = setTimeout(function () { show(el); }, DELAY);
  }

  document.addEventListener('pointerover', function (e) {
    if (e.pointerType === 'touch') return;
    var el = pick(e.target);
    if (el) schedule(el); else hide();
  }, { passive: true });

  document.addEventListener('pointerdown', function (e) {
    var el = pick(e.target);
    if (!el) { hide(); return; }
    if (e.pointerType === 'touch') {
      show(el);
      clearTimeout(hideTimer);
      hideTimer = setTimeout(hide, 2600);
    }
  }, { passive: true });

  document.addEventListener('focusin', function (e) {
    var el = pick(e.target);
    if (el) schedule(el); else hide();
  });

  document.addEventListener('focusout', hide);
  window.addEventListener('scroll', hide, { passive: true });
  window.addEventListener('resize', hide, { passive: true });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') hide();
  });
})();

(function () {
  'use strict';

  var PREFIX = 'cn:teacher:';

  function remember(subject, variant) {
    if (!subject || !variant) return;
    try { localStorage.setItem(PREFIX + subject, variant); } catch (e) { }
  }

  function recall(subject) {
    try { return localStorage.getItem(PREFIX + subject); } catch (e) { return null; }
  }

  function trackCurrent() {
    var root = document.querySelector('[data-cn-course]');
    if (!root) return;
    remember(root.dataset.subject, root.dataset.variant);
  }

  function escapeAttr(value) {
    if (window.CSS && CSS.escape) return CSS.escape(value);
    return value.replace(/["\\]/g, '\\$&');
  }

  function applyToCards(scope) {
    var root = scope || document;
    root.querySelectorAll('[data-subject-card]').forEach(function (card) {
      var saved = recall(card.dataset.subject);
      if (!saved) return;

      var row = card.querySelector('[data-variant="' + escapeAttr(saved) + '"]');
      if (!row) return;

      var url = row.dataset.url || row.getAttribute('href');
      var link = card.querySelector('[data-subject-link]');
      if (link && url) link.setAttribute('href', url);

      card.querySelectorAll('[data-remembered]').forEach(function (el) {
        el.removeAttribute('data-remembered');
      });
      row.dataset.remembered = '1';
    });
  }

  window.cnApplySubjectCards = applyToCards;

  function initSheet() {
    var sheet = document.getElementById('cn-teacher-sheet');
    if (!sheet) return;

    document.addEventListener('click', function (e) {
      var opener = e.target.closest('[data-teacher-open]');
      if (opener) {
        e.preventDefault();
        if (typeof sheet.showModal === 'function') sheet.showModal();
        else sheet.setAttribute('open', '');
        return;
      }

      var item = e.target.closest('.cn-sheet__item');
      if (item && sheet.contains(item)) {
        remember(sheet.dataset.subject, item.dataset.variant);
      }
    });

    sheet.addEventListener('click', function (e) {
      if (e.target === sheet) sheet.close();
    });
  }

  function initCardRows() {
    document.addEventListener('click', function (e) {
      var row = e.target.closest('[data-subject-card] [data-variant]');
      if (!row) return;
      var card = row.closest('[data-subject-card]');
      if (card) remember(card.dataset.subject, row.dataset.variant);
    });
  }

  function init() {
    trackCurrent();
    applyToCards();
    initCardRows();
    initSheet();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
