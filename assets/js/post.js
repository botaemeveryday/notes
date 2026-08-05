/*
 * Подсветка активного пункта в оглавлении.
 *
 * Было: Alpine-компонент tocHighlighter() + слушатель scroll с debounce 300 мс,
 * который на каждый тик дёргал getBoundingClientRect() для всех заголовков.
 * Стало: IntersectionObserver — ноль работы при прокрутке и мгновенный отклик.
 */
(function () {
  'use strict';

  function init() {
    var toc = document.getElementById('TableOfContents');
    if (!toc) return;

    var wrapper = toc.closest('[data-toc]');
    if (!wrapper || getComputedStyle(wrapper).display === 'none') return;

    var activeClasses = (wrapper.dataset.activeClass || '').split(/\s+/).filter(Boolean);

    var links = Array.prototype.slice.call(toc.querySelectorAll('a[href^="#"]'));
    var pairs = [];

    links.forEach(function (link) {
      var id = decodeURIComponent(link.getAttribute('href').slice(1));
      var heading = id && document.getElementById(id);
      if (heading) pairs.push({ link: link, heading: heading });
    });
    if (!pairs.length) return;

    var current = null;
    function setActive(index) {
      if (index === current || !pairs[index]) return;
      if (current !== null) {
        activeClasses.forEach(function (c) { pairs[current].link.classList.remove(c); });
      }
      activeClasses.forEach(function (c) { pairs[index].link.classList.add(c); });
      current = index;
    }

    var visible = new Set();

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var i = pairs.findIndex(function (p) { return p.heading === entry.target; });
        if (i < 0) return;
        if (entry.isIntersecting) visible.add(i); else visible.delete(i);
      });

      if (visible.size) {
        setActive(Math.min.apply(null, Array.from(visible)));
        return;
      }

      // Ни один заголовок не в «активной зоне» — берём последний, что уже проехали.
      var last = 0;
      for (var i = 0; i < pairs.length; i++) {
        if (pairs[i].heading.getBoundingClientRect().top < 100) last = i;
      }
      setActive(last);
    }, {
      // Активная зона: полоса от 100 px сверху до 30 % высоты экрана.
      rootMargin: '-100px 0px -70% 0px',
      threshold: 0
    });

    pairs.forEach(function (p) { observer.observe(p.heading); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
