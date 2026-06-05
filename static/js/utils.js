/* ─── NAV SCROLL EFFECT ──────────────────────────────────────── */
function initNav() {
  const nav = document.querySelector('.nav');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  });

  const hamburger = document.querySelector('.hamburger');
  const links     = document.querySelector('.nav-links');
  const cta       = document.querySelector('.nav-cta');
  if (hamburger) {
    hamburger.addEventListener('click', () => {
      links?.classList.toggle('open');
      cta?.classList.toggle('open');
      hamburger.classList.toggle('is-open');
      hamburger.setAttribute('aria-expanded', hamburger.classList.contains('is-open'));
    });
  }

  // Active link
  const path = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === location.pathname || href === '/' + path) {
      a.classList.add('active');
    }
  });
}

/* ─── TYPEWRITER FOR HERO DESTINATION ───────────────────────── */
function initTypewriter() {
  const el = document.getElementById('heroDestText');
  if (!el) return;

  const words = ['Adventure', 'Kyoto', 'Santorini', 'Patagonia', 'Bali', 'Journey'];
  let wordIdx = 0;
  let charIdx = 0;
  let deleting = false;
  let paused = false;

  // Inject blinking cursor
  const cursor = document.createElement('span');
  cursor.style.cssText = `
    display: inline-block;
    width: 3px;
    height: 0.85em;
    background: var(--terra);
    margin-left: 3px;
    vertical-align: middle;
    border-radius: 1px;
    animation: blink 0.9s step-end infinite;
  `;
  el.parentNode.insertBefore(cursor, el.nextSibling);

  function tick() {
    if (paused) return;
    const word = words[wordIdx];

    if (!deleting) {
      charIdx++;
      el.textContent = word.slice(0, charIdx);
      if (charIdx === word.length) {
        paused = true;
        setTimeout(() => { paused = false; deleting = true; tick(); }, 2200);
        return;
      }
      setTimeout(tick, 80 + Math.random() * 40);
    } else {
      charIdx--;
      el.textContent = word.slice(0, charIdx);
      if (charIdx === 0) {
        deleting = false;
        wordIdx = (wordIdx + 1) % words.length;
        setTimeout(tick, 380);
        return;
      }
      setTimeout(tick, 45);
    }
  }

  // Start after hero entrance delay
  setTimeout(tick, 1400);
}

/* ─── SCROLL REVEAL (directional + stagger) ─────────────────── */
function initReveal() {
  const els = document.querySelectorAll('[data-reveal]');
  if (!els.length) return;

  // Inject reveal CSS once
  if (!document.getElementById('reveal-styles')) {
    const style = document.createElement('style');
    style.id = 'reveal-styles';
    style.textContent = `
      [data-reveal] {
        opacity: 0;
        transform: translateY(32px);
        transition: opacity 0.65s ease, transform 0.65s cubic-bezier(0.22,1,0.36,1);
      }
      [data-reveal][data-dir="left"]  { transform: translateX(-36px); }
      [data-reveal][data-dir="right"] { transform: translateX(36px); }
      [data-reveal][data-dir="scale"] { transform: scale(0.93); }
      [data-reveal].revealed {
        opacity: 1 !important;
        transform: none !important;
      }
    `;
    document.head.appendChild(style);
  }

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const delay = e.target.dataset.delay || '0s';
      e.target.style.transitionDelay = delay;
      e.target.classList.add('revealed');
      io.unobserve(e.target);
    });
  }, { threshold: 0.12 });

  els.forEach(el => io.observe(el));
}

/* ─── STAT COUNTER ANIMATION ─────────────────────────────────── */
function initStatCounters() {
  const stats = document.querySelectorAll('.stat-num');
  if (!stats.length) return;

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const el = e.target;
      const raw = el.textContent.trim();           // e.g. "12k+", "4.9★", "50+"
      const suffix = raw.replace(/[\d.]/g, '');    // "+", "k+", "★", etc.
      const num    = parseFloat(raw);
      if (isNaN(num)) return;

      let start = null;
      const duration = 1200;
      const isDecimal = raw.includes('.');

      function step(ts) {
        if (!start) start = ts;
        const progress = Math.min((ts - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const current = num * eased;
        el.textContent = (isDecimal ? current.toFixed(1) : Math.floor(current)) + suffix;
        if (progress < 1) requestAnimationFrame(step);
        else el.textContent = raw; // snap to exact final value
      }
      requestAnimationFrame(step);
      io.unobserve(el);
    });
  }, { threshold: 0.5 });

  stats.forEach(s => io.observe(s));
}

/* ─── TOAST ──────────────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  const container = document.querySelector('.toast-container') || (() => {
    const d = document.createElement('div');
    d.className = 'toast-container';
    document.body.appendChild(d);
    return d;
  })();
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${type === 'success' ? '✓' : '✕'}</span><span class="toast-msg">${msg}</span>`;
  // Entrance
  t.style.cssText = 'opacity:0; transform:translateX(20px); transition: opacity 0.3s, transform 0.3s;';
  container.appendChild(t);
  requestAnimationFrame(() => { t.style.opacity = '1'; t.style.transform = 'translateX(0)'; });
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateX(20px)';
    setTimeout(() => t.remove(), 300);
  }, 3200);
}

/* ─── DEST TILES HOVER PARALLAX ─────────────────────────────── */
function initDestTileParallax() {
  document.querySelectorAll('.dest-tile').forEach(tile => {
    tile.addEventListener('mousemove', e => {
      const rect = tile.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width  - 0.5) * 12;
      const y = ((e.clientY - rect.top)  / rect.height - 0.5) * 12;
      tile.style.transform = `perspective(500px) rotateY(${x}deg) rotateX(${-y}deg) scale(1.04)`;
    });
    tile.addEventListener('mouseleave', () => {
      tile.style.transform = '';
    });
  });
}

/* ─── INIT ALL ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initReveal();
  initTypewriter();
  initStatCounters();
  initDestTileParallax();
});