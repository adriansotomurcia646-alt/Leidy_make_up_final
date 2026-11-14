/* Carrusel con desvanecimiento: no introduce peticiones de red ni librerías. */
(() => {
  'use strict';
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  for (const gallery of document.querySelectorAll('[data-maison-carousel]')) {
    const slides = [...gallery.querySelectorAll('.maison-crossfade-image')];
    const dots = [...gallery.querySelectorAll('[data-maison-dot]')];
    if (slides.length < 2) continue;
    let current = 0;
    let timer = null;
    const interval = Math.max(3000, Math.min(12000, Number(gallery.dataset.interval) || 5800));

    function show(index) {
      const next = (index + slides.length) % slides.length;
      if (next === current) return;
      slides[current].classList.remove('is-visible');
      slides[current].setAttribute('aria-hidden', 'true');
      slides[next].classList.add('is-visible');
      slides[next].removeAttribute('aria-hidden');
      dots.forEach((dot, i) => {
        const active = i === next;
        dot.classList.toggle('is-active', active);
        dot.setAttribute('aria-pressed', String(active));
      });
      current = next;
    }

    function stop() {
      if (timer !== null) window.clearInterval(timer);
      timer = null;
    }
    function start() {
      stop();
      if (!reduceMotion.matches && !document.hidden)
        timer = window.setInterval(() => show(current + 1), interval);
    }
    dots.forEach((dot, index) => dot.addEventListener('click', () => {
      show(index);
      start();
    }));
    gallery.addEventListener('mouseenter', stop);
    gallery.addEventListener('mouseleave', start);
    gallery.addEventListener('focusin', stop);
    gallery.addEventListener('focusout', (event) => {
      if (!gallery.contains(event.relatedTarget)) start();
    });
    document.addEventListener('visibilitychange', start);
    if (typeof reduceMotion.addEventListener === 'function')
      reduceMotion.addEventListener('change', start);
    start();
  }
})();
