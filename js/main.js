/* ============================================
   GHOSTSHIELD AI — MAIN JAVASCRIPT
   Animations, Charts, Interactions
   ============================================ */

'use strict';

/* ──────────────────────────────────────────
   PARTICLE BACKGROUND SYSTEM
   ────────────────────────────────────────── */
const ParticleSystem = (() => {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  let width, height, animId;

  const colors = ['rgba(139,92,246,', 'rgba(236,72,153,', 'rgba(6,182,212,', 'rgba(255,255,255,'];

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }

  function createParticle() {
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.5 + 0.5,
      color: colors[Math.floor(Math.random() * colors.length)],
      opacity: Math.random() * 0.5 + 0.1,
      life: Math.random() * 200 + 100,
      age: 0
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: 120 }, createParticle);
    window.addEventListener('resize', resize);
    animate();
  }

  function drawConnections() {
    const maxDist = 120;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist) {
          const alpha = (1 - dist / maxDist) * 0.12;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(139,92,246,${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);
    drawConnections();

    particles.forEach((p, idx) => {
      p.x += p.vx;
      p.y += p.vy;
      p.age++;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      if (p.age > p.life) particles[idx] = createParticle();

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color + p.opacity + ')';
      ctx.fill();
    });

    animId = requestAnimationFrame(animate);
  }

  init();
})();

/* ──────────────────────────────────────────
   NAVBAR SCROLL BEHAVIOR
   ────────────────────────────────────────── */
const NavbarController = (() => {
  const navbar = document.getElementById('navbar');
  const toggle = document.getElementById('nav-toggle');
  const links = document.getElementById('nav-links');

  if (!navbar) return;

  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });

  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const isOpen = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', isOpen);
    });

    links.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        links.classList.remove('open');
        toggle.setAttribute('aria-expanded', false);
      });
    });
  }

  // Active link on scroll
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navLinks.forEach(l => {
          l.classList.toggle('active-link', l.getAttribute('href') === `#${id}`);
        });
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(s => observer.observe(s));
})();

/* ──────────────────────────────────────────
   SCROLL REVEAL ANIMATIONS
   ────────────────────────────────────────── */
const ScrollReveal = (() => {
  const elements = document.querySelectorAll('.reveal');
  if (!elements.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  elements.forEach(el => observer.observe(el));
})();

/* ──────────────────────────────────────────
   COUNTER ANIMATIONS
   ────────────────────────────────────────── */
const CounterAnimation = (() => {
  const counters = document.querySelectorAll('.counter, .stat-number');
  if (!counters.length) return;

  function animateCounter(el) {
    const target = parseFloat(el.dataset.target);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 2000;
    const isDecimal = target % 1 !== 0;
    const start = performance.now();

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4);
      const current = target * eased;

      el.textContent = prefix + (isDecimal ? current.toFixed(1) : Math.floor(current)) + suffix;

      if (progress < 1) requestAnimationFrame(update);
      else el.textContent = prefix + target + suffix;
    }

    requestAnimationFrame(update);
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(c => observer.observe(c));
})();

/* ──────────────────────────────────────────
   HEATMAP GENERATION
   ────────────────────────────────────────── */
const HeatmapGenerator = (() => {
  const grid = document.getElementById('heatmap-grid');
  if (!grid) return;

  const types = ['h-0', 'h-1', 'h-2', 'h-3', 'h-absent', 'h-anomaly'];
  const weights = [0.05, 0.2, 0.35, 0.2, 0.1, 0.1];

  function weightedRandom() {
    const r = Math.random();
    let cumulative = 0;
    for (let i = 0; i < weights.length; i++) {
      cumulative += weights[i];
      if (r < cumulative) return types[i];
    }
    return types[2];
  }

  for (let i = 0; i < 35; i++) {
    const cell = document.createElement('div');
    cell.className = `heatmap-cell ${weightedRandom()}`;
    cell.title = `Day ${i + 1}`;
    grid.appendChild(cell);
  }
})();

/* ──────────────────────────────────────────
   HERO CHART (Mini Anomaly Trend)
   ────────────────────────────────────────── */
const HeroChart = (() => {
  const canvas = document.getElementById('heroChart');
  if (!canvas) return;

  const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const data = [12, 19, 14, 28, 22, 35, 31];

  new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data,
        borderColor: '#8b5cf6',
        borderWidth: 2,
        backgroundColor: (ctx) => {
          const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 90);
          gradient.addColorStop(0, 'rgba(139,92,246,0.3)');
          gradient.addColorStop(1, 'rgba(139,92,246,0)');
          return gradient;
        },
        pointRadius: 3,
        pointBackgroundColor: '#8b5cf6',
        pointBorderColor: '#fff',
        pointBorderWidth: 1,
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, tooltip: {
        backgroundColor: 'rgba(13,18,38,0.9)',
        borderColor: 'rgba(139,92,246,0.3)',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        padding: 10
      }},
      scales: {
        x: { grid: { display: false }, ticks: { color: '#475569', font: { size: 9 } } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#475569', font: { size: 9 } } }
      }
    }
  });
})();

/* ──────────────────────────────────────────
   FRAUD TREND CHART (Dashboard)
   ────────────────────────────────────────── */
const FraudTrendChart = (() => {
  const canvas = document.getElementById('fraudTrendChart');
  if (!canvas) return;

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const detected = [42, 58, 51, 73, 88, 95, 79, 112, 98, 134, 118, 142];
  const resolved = [38, 50, 44, 65, 79, 87, 71, 98, 89, 119, 105, 130];

  const ctx = canvas.getContext('2d');
  const gradPurple = ctx.createLinearGradient(0, 0, 0, 200);
  gradPurple.addColorStop(0, 'rgba(139,92,246,0.35)');
  gradPurple.addColorStop(1, 'rgba(139,92,246,0)');

  const gradCyan = ctx.createLinearGradient(0, 0, 0, 200);
  gradCyan.addColorStop(0, 'rgba(6,182,212,0.2)');
  gradCyan.addColorStop(1, 'rgba(6,182,212,0)');

  new Chart(canvas, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Fraud Detected',
          data: detected,
          borderColor: '#8b5cf6',
          backgroundColor: gradPurple,
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#8b5cf6',
          pointBorderColor: '#0d1226',
          pointBorderWidth: 2,
          tension: 0.4,
          fill: true
        },
        {
          label: 'Cases Resolved',
          data: resolved,
          borderColor: '#06b6d4',
          backgroundColor: gradCyan,
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#06b6d4',
          pointBorderColor: '#0d1226',
          pointBorderWidth: 2,
          tension: 0.4,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 12, padding: 16 }
        },
        tooltip: {
          backgroundColor: 'rgba(13,18,38,0.95)',
          borderColor: 'rgba(139,92,246,0.3)',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          padding: 12,
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y} cases`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#475569', font: { size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#475569', font: { size: 10 } }
        }
      }
    }
  });
})();

/* ──────────────────────────────────────────
   RISK DONUT CHART (Dashboard)
   ────────────────────────────────────────── */
const RiskDonutChart = (() => {
  const canvas = document.getElementById('riskDonutChart');
  if (!canvas) return;

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['High Risk', 'Medium Risk', 'Low Risk'],
      datasets: [{
        data: [15, 28, 57],
        backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
        borderColor: ['rgba(239,68,68,0.3)', 'rgba(245,158,11,0.3)', 'rgba(16,185,129,0.3)'],
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      cutout: '70%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(13,18,38,0.95)',
          borderColor: 'rgba(139,92,246,0.3)',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          padding: 12,
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed}%`
          }
        }
      }
    }
  });
})();

/* ──────────────────────────────────────────
   DASHBOARD TAB SWITCHER
   ────────────────────────────────────────── */
const DashboardTabs = (() => {
  const tabs = document.querySelectorAll('.dash-tab');
  if (!tabs.length) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
    });
  });
})();

/* ──────────────────────────────────────────
   CONTACT FORM HANDLER
   ────────────────────────────────────────── */
const ContactForm = (() => {
  const form = document.getElementById('contact-form');
  const success = document.getElementById('form-success');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const btn = form.querySelector('button[type="submit"]');
    const original = btn.innerHTML;

    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    btn.disabled = true;

    setTimeout(() => {
      btn.innerHTML = original;
      btn.disabled = false;
      form.reset();
      success.hidden = false;
      success.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

      setTimeout(() => { success.hidden = true; }, 6000);
    }, 1800);
  });
})();

/* ──────────────────────────────────────────
   NEWSLETTER FORM HANDLER
   ────────────────────────────────────────── */
const NewsletterForm = (() => {
  const form = document.getElementById('newsletter-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = form.querySelector('button');
    btn.innerHTML = '<i class="fas fa-check"></i>';
    btn.style.background = '#10b981';
    form.querySelector('input').value = '';
    setTimeout(() => {
      btn.innerHTML = '<i class="fas fa-arrow-right"></i>';
      btn.style.background = '';
    }, 3000);
  });
})();

/* ──────────────────────────────────────────
   SMOOTH ANCHOR SCROLL
   ────────────────────────────────────────── */
const SmoothScroll = (() => {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
})();

/* ──────────────────────────────────────────
   DASHBOARD MOCKUP LIVE ANIMATION
   ────────────────────────────────────────── */
const LiveDashAnimation = (() => {
  // Randomly flash alert items to simulate live updates
  const alertItems = document.querySelectorAll('.alert-item');
  if (!alertItems.length) return;

  setInterval(() => {
    const idx = Math.floor(Math.random() * alertItems.length);
    alertItems[idx].style.background = 'rgba(139,92,246,0.1)';
    setTimeout(() => { alertItems[idx].style.background = ''; }, 600);
  }, 3200);

  // Animate risk bar widths on scroll
  const riskBars = document.querySelectorAll('.risk-bar');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        riskBars.forEach(bar => {
          const w = bar.style.width;
          bar.style.width = '0';
          requestAnimationFrame(() => {
            setTimeout(() => { bar.style.width = w; }, 100);
          });
        });
        observer.disconnect();
      }
    });
  }, { threshold: 0.3 });

  const table = document.querySelector('.dash-table-section');
  if (table) observer.observe(table);
})();

/* ──────────────────────────────────────────
   FEATURE CARD MAGNETIC EFFECT
   ────────────────────────────────────────── */
const CardMagneticEffect = (() => {
  const cards = document.querySelectorAll('.feature-card, .impact-card, .pricing-card');

  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = (e.clientX - cx) / rect.width;
      const dy = (e.clientY - cy) / rect.height;
      card.style.transform = `translateY(-6px) rotateX(${-dy * 4}deg) rotateY(${dx * 4}deg)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
})();

/* ──────────────────────────────────────────
   PRICING CARD HOVER GLOW CURSOR
   ────────────────────────────────────────── */
const CardGlowEffect = (() => {
  const cards = document.querySelectorAll('.feature-card, .security-card, .testimonial-card');

  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      card.style.setProperty('--mouse-x', `${x}%`);
      card.style.setProperty('--mouse-y', `${y}%`);
    });
  });
})();

/* ──────────────────────────────────────────
   TYPEWRITER EFFECT FOR HERO BADGE
   ────────────────────────────────────────── */
const TypewriterEffect = (() => {
  const badge = document.querySelector('.hero-badge span:last-child');
  if (!badge) return;

  const texts = [
    'Live AI Fraud Detection — Government-Certified Platform',
    'Protecting 500K+ Employee Records Nationwide',
    'Biometric Verification in Real-Time',
    '98.7% Accuracy — Trusted by 120+ Agencies'
  ];

  let textIdx = 0;
  let charIdx = 0;
  let deleting = false;
  let paused = false;

  function type() {
    if (paused) return;
    const current = texts[textIdx];

    if (!deleting) {
      badge.textContent = current.slice(0, charIdx + 1);
      charIdx++;
      if (charIdx === current.length) {
        paused = true;
        setTimeout(() => { paused = false; deleting = true; }, 3000);
      }
    } else {
      badge.textContent = current.slice(0, charIdx - 1);
      charIdx--;
      if (charIdx === 0) {
        deleting = false;
        textIdx = (textIdx + 1) % texts.length;
      }
    }
  }

  setInterval(type, 60);
})();

/* ──────────────────────────────────────────
   DASHBOARD NAV ITEM INTERACTIONS
   ────────────────────────────────────────── */
const DashNavItems = (() => {
  const items = document.querySelectorAll('.dash-nav-item');
  items.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      items.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
    });
  });
})();

/* ──────────────────────────────────────────
   CHART PERIOD TOGGLE (Pill Buttons)
   ────────────────────────────────────────── */
const ChartPillToggle = (() => {
  const pillGroups = document.querySelectorAll('.panel-controls');
  pillGroups.forEach(group => {
    group.querySelectorAll('.pill').forEach(pill => {
      pill.addEventListener('click', () => {
        group.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
      });
    });
  });
})();

/* ──────────────────────────────────────────
   PAGE LOAD ANIMATION
   ────────────────────────────────────────── */
const PageLoad = (() => {
  document.body.style.opacity = '0';
  document.body.style.transition = 'opacity 0.5s ease';

  window.addEventListener('load', () => {
    document.body.style.opacity = '1';
  });

  // Fallback
  setTimeout(() => { document.body.style.opacity = '1'; }, 800);
})();

/* ──────────────────────────────────────────
   DASHBOARD ALERT COUNTER UPDATE
   ────────────────────────────────────────── */
const AlertCounter = (() => {
  const badge = document.querySelector('.notif-badge');
  if (!badge) return;

  let count = parseInt(badge.textContent);
  setInterval(() => {
    if (Math.random() > 0.7) {
      count = Math.min(count + 1, 99);
      badge.textContent = count;
      badge.style.animation = 'none';
      badge.offsetHeight; // reflow
      badge.style.animation = 'pulse 0.4s ease';
    }
  }, 8000);
})();

/* ──────────────────────────────────────────
   UTILITY: Debounce
   ────────────────────────────────────────── */
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/* ──────────────────────────────────────────
   RESIZE HANDLER
   ────────────────────────────────────────── */
window.addEventListener('resize', debounce(() => {
  // Charts auto-resize via Chart.js responsive mode
}, 200));

console.log('%cGhostShield AI ⚡ Initialized', 'color: #8b5cf6; font-weight: bold; font-size: 14px;');
console.log('%cProtecting Government Payrolls with AI Intelligence', 'color: #94a3b8; font-size: 12px;');
