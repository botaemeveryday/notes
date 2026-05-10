function tocHighlighter() {
  return {
    headings: [],
    links: [],
    debouncedScroll: null,
    
    init() {
      const toc = document.querySelector('#TableOfContents');
      if (!toc || window.getComputedStyle(toc.parentElement).display === 'none') {
        return;
      }
      
      this.links = Array.from(toc.querySelectorAll('a'));
      this.headings = this.links
        .map((link) => {
          const href = link.getAttribute('href');
          return document.getElementById(href?.replace('#', ''));
        })
        .filter(Boolean);
        
      this.debouncedScroll = this.debounce(this.onScroll.bind(this), 300);
      this.debouncedScroll();
    },
    
    onScroll() {
      let closest = null;
      let minOffset = Infinity;
      
      this.headings.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        const offset = Math.abs(rect.top - 100);
        
        if (rect.top < window.innerHeight && offset < minOffset) {
          minOffset = offset;
          closest = index;
        }
      });
      
      if (closest !== null && this.links[closest]) {
        this.setActive(this.links[closest]);
      }
    },
    
    setActive(activeLink) {
      this.links.forEach((link) => link.classList.remove('menu-active', 'text-primary', 'font-bold'));
      activeLink.classList.add('menu-active', 'text-primary', 'font-bold');
    },
    
    debounce(fn, delay) {
      let timeout;
      return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), delay);
      };
    }
  };
}