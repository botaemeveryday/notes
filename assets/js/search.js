/*
 * Поиск по конспектам (только главная).
 *
 * Главное изменение: index.json больше НЕ качается при загрузке страницы.
 * Он подгружается лениво — при первом фокусе/наборе или если в URL есть ?q=.
 * Для большинства посетителей это минус весь вес индекса на первом экране.
 */
(function () {
  'use strict';

  var input, resultsBar, countEl, normalView, searchView, grid, noResults, template;
  var index = null;
  var loading = null;
  var timer = null;
  var highlightClass = 'bg-primary/20 text-primary font-bold rounded px-1';

  function loadIndex() {
    if (loading) return loading;
    loading = fetch(input.dataset.index)
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        index = data;
        // Предрасчёт строки для поиска — иначе конкатенация на каждое нажатие.
        index.forEach(function (item) {
          item._haystack = [
            item.title || '',
            item.content || '',
            Array.isArray(item.tags) ? item.tags.join(' ') : ''
          ].join(' ').toLowerCase();
        });
        return index;
      })
      .catch(function (err) {
        loading = null;
        resultsBar.classList.remove('hidden');
        resultsBar.innerHTML = '<span class="text-error font-medium">Не удалось загрузить поисковый индекс.</span>';
        throw err;
      });
    return loading;
  }

  function escapeRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function highlight(html, term) {
    if (!term || !html) return html;
    var regex = new RegExp('(' + escapeRegExp(term) + ')', 'gi');
    var root = document.createElement('div');
    root.innerHTML = html;

    var skip = { SCRIPT: 1, STYLE: 1, CODE: 1, PRE: 1, SVG: 1 };
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (skip[node.parentNode.nodeName]) return NodeFilter.FILTER_REJECT;
        return regex.test(node.textContent) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });

    var targets = [];
    while (walker.nextNode()) targets.push(walker.currentNode);

    targets.forEach(function (node) {
      var fragment = document.createDocumentFragment();
      node.textContent.split(regex).forEach(function (part) {
        if (!part) return;
        if (part.toLowerCase() === term.toLowerCase()) {
          var span = document.createElement('span');
          span.className = highlightClass;
          span.textContent = part;
          fragment.appendChild(span);
        } else {
          fragment.appendChild(document.createTextNode(part));
        }
      });
      node.parentNode.replaceChild(fragment, node);
    });

    return root.innerHTML;
  }

  function fallbackCard(item) {
    var text = (item.content || '').replace(/<[^>]*>?/g, '').slice(0, 120);
    return '<a href="' + item.id + '" class="group flex flex-col h-full bg-base-100 border border-base-300 rounded-2xl overflow-hidden no-underline text-base-content hover:bg-base-200/50 hover:border-primary/50 hover:-translate-y-1 hover:shadow-xl transition-all duration-300">' +
      '<div class="h-1.5 w-full bg-gradient-to-r from-primary/40 to-secondary/40"></div>' +
      '<div class="p-5 flex-1 flex flex-col">' +
      '<h3 class="text-lg font-bold leading-snug mb-2 group-hover:text-primary transition-colors line-clamp-2">' + (item.title || 'Документ') + '</h3>' +
      '<p class="text-sm text-base-content/60 leading-relaxed line-clamp-3 mb-4">' + text + '…</p>' +
      '</div></a>';
  }

  function render(term) {
    normalView.style.display = 'none';

    var fragment = document.createDocumentFragment();
    var found = 0;

    index.forEach(function (item) {
      if (item._haystack.indexOf(term) === -1) return;
      var node = template.content.cloneNode(true);
      node.querySelector('.card-content').innerHTML = highlight(item.html || fallbackCard(item), term);
      fragment.appendChild(node);
      found++;
    });

    grid.replaceChildren(fragment);

    if (window.cnApplySubjectCards) window.cnApplySubjectCards(grid);

    countEl.textContent = found;
    resultsBar.classList.toggle('hidden', found === 0);
    noResults.classList.toggle('hidden', found > 0);
    searchView.classList.toggle('hidden', found === 0);

    syncUrl(term);
  }

  function search(query) {
    var term = query.toLowerCase().trim();
    if (!term) return clear();
    loadIndex().then(function () { render(term); }).catch(function () {});
  }

  function clear() {
    input.value = '';
    resultsBar.classList.add('hidden');
    noResults.classList.add('hidden');
    searchView.classList.add('hidden');
    grid.replaceChildren();
    normalView.style.display = '';
    syncUrl('');
    input.focus();
  }
  window.clearSearch = clear;

  function syncUrl(term) {
    if (!history.replaceState) return;
    var url = new URL(window.location.href);
    if (term) url.searchParams.set('q', term); else url.searchParams.delete('q');
    history.replaceState(null, '', url);
  }

  function init() {
    input = document.getElementById('global-search');
    if (!input) return;

    resultsBar = document.getElementById('search-results');
    countEl = document.getElementById('result-count');
    normalView = document.getElementById('normal-view');
    searchView = document.getElementById('search-view');
    grid = document.getElementById('search-grid');
    noResults = document.getElementById('no-results');
    template = document.getElementById('search-item-template');
    highlightClass = input.dataset.highlightClass || highlightClass;

    // Индекс начинаем тянуть заранее, но только когда человек явно
    // собрался искать — по фокусу или наведению на поле.
    ['focus', 'pointerenter'].forEach(function (evt) {
      input.addEventListener(evt, function () { loadIndex().catch(function () {}); }, { once: true });
    });

    input.addEventListener('input', function () {
      clearTimeout(timer);
      var value = this.value;
      timer = setTimeout(function () { search(value); }, 200);
    });

    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        input.focus();
        input.select();
      } else if (e.key === 'Escape' && input.value) {
        clear();
      }
    });

    // Подсказка ⌘K / Ctrl+K
    if (!/Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent)) {
      var kbd = document.querySelector('[data-kbd-mod]');
      if (kbd) kbd.textContent = 'Ctrl';
    }

    var q = new URLSearchParams(window.location.search).get('q');
    if (q) {
      input.value = q;
      search(q);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();