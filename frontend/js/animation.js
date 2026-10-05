/**
 * PhytoSentinel Animation Module
 * Gère toutes les animations et effets visuels
 */

const Animation = {
  // ==========================================
  // INITIALISATION
  // ==========================================

  init() {
    this.initRevealAnimations();
    this.initCounterAnimations();
    this.initHoverEffects();
    this.initTicker();
    this.initMapDots();
    this.initForecastChart();
    this.initDashboardCharts();
    this.initAlerts();
    this.initMapData();
    this.initActivityTimeline();
    this.initContactInfo();
    this.initCultureBreakdown();
    this.initDiseaseBreakdown();
    this.initInspectionStats();
    this.initAIpredictions();
    this.initMonthlyChart();
    this.initToast();
  },

  // ==========================================
  // REVEAL ON SCROLL
  // ==========================================

  initRevealAnimations() {
    const rvEls = document.querySelectorAll('.rv');
    const rvObs = new IntersectionObserver((entries) => {
      entries.forEach((e, i) => {
        if (e.isIntersecting) {
          setTimeout(() => e.target.classList.add('on'), i * 80);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    rvEls.forEach(el => rvObs.observe(el));
  },

  // ==========================================
  // COUNTER ANIMATIONS
  // ==========================================

  initCounterAnimations() {
    const counters = document.querySelectorAll('[data-count]');

    function animCount(el) {
      const target = parseInt(el.getAttribute('data-count'));
      const dur = 1800;
      const t0 = performance.now();

      const tick = (now) => {
        const p = Math.min((now - t0) / dur, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        const value = Math.floor(ease * target);
        el.textContent = el.textContent.includes('%') ? `${value}%` : value;
        if (p < 1) {
          requestAnimationFrame(tick);
        } else {
          el.textContent = el.textContent.includes('%') ? `${target}%` : target;
        }
      };

      requestAnimationFrame(tick);
    }

    const cntObs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          animCount(e.target);
          cntObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.5 });

    counters.forEach(el => cntObs.observe(el));
  },

  // ==========================================
  // HOVER EFFECTS
  // ==========================================

  initHoverEffects() {
    // Card hover effects
    document.querySelectorAll('.card, .stat, .glass, .glass-lime').forEach(el => {
      el.addEventListener('mouseenter', () => {
        el.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
      });
    });

    // Button ripple effect
    document.querySelectorAll('.btn, .btn-o').forEach(btn => {
      btn.addEventListener('click', function(e) {
        const rect = this.getBoundingClientRect();
        const ripple = document.createElement('span');
        ripple.style.cssText = `
          position: absolute;
          background: rgba(255,255,255,0.3);
          border-radius: 50%;
          transform: scale(0);
          animation: ripple 0.6s linear;
          pointer-events: none;
        `;
        const size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size/2) + 'px';
        this.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
      });
    });

    // Form input focus effects
    document.querySelectorAll('input, textarea, select').forEach(input => {
      input.addEventListener('focus', () => {
        input.style.borderColor = 'rgba(74,222,128,.5)';
        input.style.boxShadow = '0 0 0 3px rgba(74,222,128,.1)';
      });
      input.addEventListener('blur', () => {
        input.style.borderColor = 'rgba(74,222,128,.18)';
        input.style.boxShadow = 'none';
      });
    });
  },

  // ==========================================
  // TICKER ANIMATION
  // ==========================================

  initTicker() {
    const ticker = document.getElementById('ticker');
    if (ticker) {
      ticker.innerHTML += ticker.innerHTML;
    }
  },

  // ==========================================
  // MAP DATA & DOTS
  // ==========================================

  initMapDots() {
    const mapDots = document.getElementById('mapDots');
    if (!mapDots) return;

    const communes = [
      { name: 'Guelma-Centre', cases: 94, disease: 'Mildiou tomate', type: 'r', top: '42%', left: '44%', size: 20 },
      { name: 'Belkheir', cases: 58, disease: 'Mildiou', type: 'r', top: '36%', left: '55%', size: 16 },
      { name: 'Bouchegouf', cases: 52, disease: 'Mildiou', type: 'r', top: '20%', left: '50%', size: 14 },
      { name: 'Bouhamdane', cases: 41, disease: 'Rouille brune', type: 'a', top: '48%', left: '36%', size: 15 },
      { name: 'Oued Zenati', cases: 37, disease: 'Rouille brune', type: 'a', top: '30%', left: '60%', size: 15 },
      { name: 'Hammam Debagh', cases: 28, disease: 'Oïdium vigne', type: 'a', top: '24%', left: '68%', size: 13 },
      { name: 'Héliopolis', cases: 22, disease: 'Fusariose', type: 'a', top: '55%', left: '27%', size: 13 },
      { name: 'Bouati Mahmoud', cases: 11, disease: 'Oïdium léger', type: 'g', top: '62%', left: '48%', size: 12 },
      { name: 'El Fedjoudj', cases: 9, disease: 'Fusariose contrôlée', type: 'g', top: '35%', left: '32%', size: 12 },
      { name: 'Medjez Amar', cases: 6, disease: 'Faible pression', type: 'g', top: '66%', left: '60%', size: 11 }
    ];

    mapDots.innerHTML = communes.map(c => `
      <div class="dot ${c.type}" style="width:${c.size}px;height:${c.size}px;top:${c.top};left:${c.left};">
        <div class="tip">
          ${c.name}<br>
          <span style="color:var(--${c.type === 'r' ? 'red' : c.type === 'a' ? 'amber' : 'green'});font-weight:700;">
            ${c.disease} — ${c.cases} cas
          </span>
        </div>
      </div>
    `).join('');

    // Map filter buttons
    document.querySelectorAll('.map-filter').forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;
        document.querySelectorAll('.map-filter').forEach(b => {
          b.classList.remove('active');
          b.style.background = 'rgba(255,255,255,.05)';
          b.style.color = 'var(--t3)';
        });
        btn.classList.add('active');
        btn.style.background = 'rgba(74,222,128,.1)';

        document.querySelectorAll('.dot').forEach(d => {
          const isMatch = filter === 'all' || d.classList.contains(filter);
          d.style.opacity = isMatch ? '1' : '0.15';
          d.style.transform = isMatch ? '' : 'scale(0.7)';
        });
      });
    });
  },

  // ==========================================
  // FORECAST CHART
  // ==========================================

  initForecastChart() {
    const forecastChart = document.getElementById('forecastChart');
    if (!forecastChart) return;

    const forecast = [
      { day: 'Dim', level: 30, risk: 'low' },
      { day: 'Lun', level: 55, risk: 'medium' },
      { day: 'Mar', level: 90, risk: 'high' },
      { day: 'Mer', level: 80, risk: 'high' },
      { day: 'Jeu', level: 58, risk: 'medium' },
      { day: 'Ven', level: 28, risk: 'low' },
      { day: 'Sam', level: 22, risk: 'low' }
    ];

    forecastChart.innerHTML = forecast.map(f => {
      const color = f.risk === 'high' ? 'var(--red)' : f.risk === 'medium' ? 'var(--amber)' : 'var(--green)';
      const gradient = f.risk === 'high'
        ? 'linear-gradient(180deg,var(--red),#7f1d1d)'
        : f.risk === 'medium'
        ? 'linear-gradient(180deg,var(--amber),#92400e)'
        : 'linear-gradient(180deg,var(--green),var(--green-dk))';
      const textColor = f.risk === 'high' ? 'var(--red)' : 'var(--t3)';
      return `
        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;height:100%;justify-content:flex-end;">
          <div class="forecast-bar" style="width:100%;background:${gradient};border-radius:3px 3px 0 0;height:${f.level}%;"></div>
          <div style="font-size:9.5px;color:${textColor};${f.risk === 'high' ? 'font-weight:700;' : ''}">${f.day}</div>
        </div>
      `;
    }).join('');
  },

  // ==========================================
  // DASHBOARD CHARTS
  // ==========================================

  initDashboardCharts() {
    this.initMonthlyChart();
    this.initCultureBreakdown();
    this.initDiseaseBreakdown();
    this.initInspectionStats();
    this.initAIpredictions();
    this.initActivityTimeline();
  },

  initMonthlyChart() {
    const monthlyChart = document.getElementById('monthlyChart');
    if (!monthlyChart) return;

    const months = [
      { name: 'Oct', current: 48, previous: 42 },
      { name: 'Nov', current: 36, previous: 38 },
      { name: 'Déc', current: 28, previous: 32 },
      { name: 'Jan', current: 55, previous: 48 },
      { name: 'Fév', current: 66, previous: 58 },
      { name: 'Mar', current: 74, previous: 65 }
    ];

    monthlyChart.innerHTML = months.map((m, i) => {
      const isCurrent = i === months.length - 1;
      return `
        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:5px;height:100%;justify-content:flex-end;position:relative;">
          <div style="width:100%;background:rgba(74,222,128,.18);border-radius:3px 3px 0 0;height:${m.previous}%;"></div>
          ${isCurrent ? `
            <div style="width:100%;background:linear-gradient(180deg,var(--lime),var(--green));border-radius:3px 3px 0 0;height:${m.current}%;position:absolute;bottom:20px;opacity:.85;"></div>
          ` : ''}
          <div style="font-size:9.5px;color:${isCurrent ? 'var(--lime)' : 'var(--t3)'};${isCurrent ? 'font-weight:700;position:relative;z-index:1;' : ''}">${m.name}</div>
        </div>
      `;
    }).join('');
  },

  initCultureBreakdown() {
    const container = document.getElementById('cultureBreakdown');
    if (!container) return;

    const cultures = [
      { icon: '🍅', name: 'Tomate', percent: 38, color: 'rgba(248,113,113,.12)' },
      { icon: '🌾', name: 'Blé / Céréales', percent: 27, color: 'rgba(251,191,36,.12)' },
      { icon: '🍇', name: 'Vigne', percent: 18, color: 'rgba(163,230,53,.12)' },
      { icon: '🌶️', name: 'Piment / Légumes', percent: 17, color: 'rgba(45,212,191,.12)' }
    ];

    container.innerHTML = cultures.map(c => `
      <div style="display:flex;align-items:center;gap:9px;">
        <div style="width:28px;height:28px;border-radius:8px;background:${c.color};display:flex;align-items:center;justify-content:center;font-size:14px;">${c.icon}</div>
        <div>
          <div style="font-size:12.5px;color:var(--t1);font-weight:600;">${c.name}</div>
          <div style="font-size:11px;color:var(--t3);">${c.percent}% des cas</div>
        </div>
      </div>
    `).join('');
  },

  initDiseaseBreakdown() {
    const container = document.getElementById('diseaseBreakdown');
    if (!container) return;

    const diseases = [
      { name: 'Mildiou de la tomate', percent: 38, color: 'var(--red)' },
      { name: 'Rouille brune du blé', percent: 27, color: 'var(--amber)' },
      { name: 'Oïdium de la vigne', percent: 18, color: 'var(--lime)' },
      { name: 'Fusariose', percent: 11, color: 'var(--teal)' },
      { name: 'Autres', percent: 6, color: 'rgba(74,222,128,.4)' }
    ];

    container.innerHTML = diseases.map(d => `
      <div>
        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
          <span style="font-size:12.5px;color:var(--t1);">${d.name}</span>
          <span style="font-size:12.5px;font-weight:700;color:${d.color};">${d.percent}%</span>
        </div>
        <div class="bar"><div class="fill" style="width:${d.percent}%;background:${d.color};"></div></div>
      </div>
    `).join('');
  },

  initInspectionStats() {
    const container = document.getElementById('inspectionStats');
    if (!container) return;

    const stats = [
      { label: 'Exploitations inspectées', value: 246, color: 'var(--green)' },
      { label: 'Prélèvements envoyés au labo', value: 83, color: 'var(--teal)' },
      { label: 'PV d\'infraction établis', value: 12, color: 'var(--amber)' }
    ];

    container.innerHTML = stats.map(s => `
      <div style="display:flex;justify-content:space-between;align-items:center;background:rgba(74,222,128,.06);border-radius:9px;padding:9px 12px;">
        <span style="font-size:12px;color:var(--t3);">${s.label}</span>
        <span style="font-size:14px;font-weight:700;color:${s.color};">${s.value}</span>
      </div>
    `).join('');
  },

  initAIpredictions() {
    const container = document.getElementById('aiPredictions');
    if (!container) return;

    const predictions = [
      { disease: 'Mildiou de la tomate', probability: 89, status: 'Fort', direction: '↑', color: 'var(--red)', bg: 'rgba(248,113,113,.08)', border: 'rgba(248,113,113,.2)' },
      { disease: 'Rouille brune du blé', probability: 63, status: 'Stable', direction: '→', color: 'var(--amber)', bg: 'rgba(251,191,36,.08)', border: 'rgba(251,191,36,.2)' },
      { disease: 'Oïdium de la vigne', probability: 71, status: 'Faible', direction: '↓', color: 'var(--green)', bg: 'rgba(74,222,128,.06)', border: 'rgba(74,222,128,.15)' },
      { disease: 'Fusariose (piment)', probability: 100, status: 'Contrôlé', direction: '✓', color: 'var(--teal)', bg: 'rgba(45,212,191,.06)', border: 'rgba(45,212,191,.15)' }
    ];

    container.innerHTML = predictions.map(p => `
      <div style="background:${p.bg};border:1px solid ${p.border};border-radius:13px;padding:14px;display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:13.5px;font-weight:700;color:var(--t1);">${p.disease}</div>
          <div style="font-size:11.5px;color:${p.color};margin-top:2px;">${p.status === 'Contrôlé' ? 'Foyer contrôlé — surveillance maintenue' : `Probabilité d'extension : ${p.probability}%`}</div>
        </div>
        <div style="font-size:20px;font-weight:800;color:${p.color};">${p.direction} ${p.status}</div>
      </div>
    `).join('');
  },

  initActivityTimeline() {
    const container = document.getElementById('activityTimeline');
    if (!container) return;

    const activities = [
      { title: 'Nouveau diagnostic — Guelma-Centre', desc: 'Mildiou grave détecté sur 3 ha de tomate — Périmètre Bouhamdane', time: 'Il y a 18 min', agent: 'Inspecteur Benali', color: 'var(--green)' },
      { title: 'Alerte transmise — 2 communes', desc: 'Notification envoyée aux fellahs de Belkheir et Bouchegouf', time: 'Il y a 42 min', agent: 'Système automatique', color: 'var(--amber)' },
      { title: 'Prélèvement envoyé au laboratoire', desc: '3 échantillons de piment — El Fedjoudj — Lab. INPV Annaba', time: 'Il y a 2h', agent: 'Inspectrice Chaabi', color: 'var(--teal)' },
      { title: 'Rapport hebdomadaire généré', desc: 'Synthèse phytosanitaire semaine 12 transmise à la Direction', time: 'Il y a 5h', agent: 'Chef de service', color: 'var(--lime)' },
      { title: 'Modèle IA mis à jour — v3.2', desc: 'Précision améliorée de 96.8% à 97.4% — intégration données 2025', time: 'Il y a 8h', agent: 'Système', color: 'var(--green)' }
    ];

    container.innerHTML = activities.map((a, i) => `
      <div style="padding-bottom:${i < activities.length - 1 ? '18px' : '0'};position:relative;">
        <div class="tl-dot" style="position:absolute;left:-26px;top:3px;background:${a.color};box-shadow:0 0 10px ${a.color.replace(')', ',.5)')}"></div>
        <div style="font-size:13px;font-weight:700;color:var(--t1);margin-bottom:3px;">${a.title}</div>
        <div style="font-size:12px;color:var(--t3);">${a.desc}</div>
        <div style="font-size:10.5px;color:var(--tm);margin-top:3px;">${a.time} · ${a.agent}</div>
      </div>
    `).join('');
  },

  // ==========================================
  // ALERTS
  // ==========================================

  initAlerts() {
    const container = document.getElementById('alertsContainer');
    if (!container) return;

    const alerts = [
      {
        type: 'critical',
        badge: '🚨 ALERTE CRITIQUE',
        title: 'Mildiou de la tomate — Guelma & Belkheir',
        desc: 'Conditions climatiques optimales pour <em>Phytophthora infestans</em> — humidité 78%, température 26°C maintenue depuis 48h. Probabilité d\'épidémie : <strong style="color:var(--red);">89%</strong>.',
        communes: ['Guelma-Centre', 'Belkheir', 'Bouhamdane'],
        status: 'Action immédiate',
        time: 'Il y a 2h',
        color: 'var(--red)',
        bg: 'rgba(248,113,113,.05)',
        border: 'rgba(248,113,113,.28)'
      },
      {
        type: 'warning',
        badge: '⚠ AVERTISSEMENT',
        title: 'Rouille brune du blé — Oued Zenati',
        desc: 'Probabilité d\'extension de <em>Puccinia triticina</em> à 63% sur la semaine à venir. Température nocturne favorable. Inspection des parcelles céréalières recommandée.',
        communes: ['Oued Zenati', 'Hammam Debagh'],
        status: 'Surveillance renforcée',
        time: 'Il y a 6h',
        color: 'var(--amber)',
        bg: 'rgba(251,191,36,.05)',
        border: 'rgba(251,191,36,.25)'
      },
      {
        type: 'info',
        badge: 'ℹ INFORMATION',
        title: 'Oïdium de la vigne — Périmètre Bouati Mahmoud',
        desc: 'Conditions légèrement propices à <em>Erysiphe necator</em>. Traitement préventif au soufre conseillé avant la période critique du débourrement.',
        communes: ['Bouati Mahmoud'],
        status: 'Traitement préventif',
        time: 'Il y a 14h',
        color: 'var(--green)',
        bg: 'rgba(74,222,128,.04)',
        border: 'rgba(74,222,128,.18)'
      },
      {
        type: 'follow',
        badge: '📋 SUIVI',
        title: 'Fusariose du piment — El Fedjoudj',
        desc: 'Foyer confirmé dans 2 serres. Situation sous contrôle. Produit appliqué : Thiophanate-méthyl 70%. Réévaluation prévue dans 10 jours.',
        communes: ['El Fedjoudj'],
        status: 'Situation stable',
        time: 'Il y a 22h',
        color: 'var(--teal)',
        bg: 'rgba(45,212,191,.04)',
        border: 'rgba(45,212,191,.18)'
      }
    ];

    const badgeClass = {
      critical: 'b-r',
      warning: 'b-a',
      info: 'b-g',
      follow: 'b-t'
    };

    container.innerHTML = alerts.map(a => `
      <div class="alert-card" style="background:${a.bg};border:1px solid ${a.border};">
        <div class="side" style="background:${a.color};"></div>
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
          <div>
            <div class="badge ${badgeClass[a.type]}" style="margin-bottom:7px;">${a.badge}</div>
            <div style="font-size:16px;font-weight:700;color:var(--t1);">${a.title}</div>
          </div>
          <div style="font-size:11.5px;color:${a.color};font-weight:600;white-space:nowrap;margin-right:8px;">${a.time}</div>
        </div>
        <div style="font-size:13px;color:var(--t3);line-height:1.75;margin-bottom:12px;">${a.desc}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          ${a.communes.map(c => `<div class="badge ${badgeClass[a.type]}">📍 ${c}</div>`).join('')}
          <div class="badge ${badgeClass[a.type]}">⏱ ${a.status}</div>
        </div>
      </div>
    `).join('');
  },

  // ==========================================
  // MAP DATA (COMMUNE RANKING)
  // ==========================================

  initMapData() {
    const ranking = document.getElementById('communeRanking');
    if (!ranking) return;

    const communes = [
      { name: 'Guelma-Centre', cases: 94, disease: 'Mildiou de la tomate', color: 'var(--red)', bg: 'rgba(248,113,113,.06)', border: 'rgba(248,113,113,.2)', badgeClass: 'b-r' },
      { name: 'Belkheir', cases: 58, disease: 'Mildiou de la tomate', color: 'var(--red)', bg: 'rgba(248,113,113,.06)', border: 'rgba(248,113,113,.2)', badgeClass: 'b-r' },
      { name: 'Bouchegouf', cases: 52, disease: 'Mildiou', color: 'var(--red)', bg: 'rgba(248,113,113,.06)', border: 'rgba(248,113,113,.2)', badgeClass: 'b-r' },
      { name: 'Bouhamdane', cases: 41, disease: 'Rouille brune du blé', color: 'var(--amber)', bg: 'rgba(251,191,36,.06)', border: 'rgba(251,191,36,.2)', badgeClass: 'b-a' },
      { name: 'Oued Zenati', cases: 37, disease: 'Rouille brune du blé', color: 'var(--amber)', bg: 'rgba(251,191,36,.06)', border: 'rgba(251,191,36,.2)', badgeClass: 'b-a' },
      { name: 'Bouati Mahmoud', cases: 11, disease: 'Oïdium vigne — faible', color: 'var(--green)', bg: 'rgba(74,222,128,.05)', border: 'rgba(74,222,128,.14)', badgeClass: 'b-g' }
    ];

    ranking.innerHTML = communes.map(c => `
      <div style="background:${c.bg};border:1px solid ${c.border};border-radius:13px;padding:14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;">
          <div style="font-size:13.5px;font-weight:700;color:var(--t1);">${c.name}</div>
          <div class="badge ${c.badgeClass}">${c.cases}</div>
        </div>
        <div class="bar"><div class="fill" style="width:${c.cases}%;background:linear-gradient(90deg,${c.color},${c.color === 'var(--red)' ? '#ef4444' : c.color === 'var(--amber)' ? '#f59e0b' : '#22c55e'});"></div></div>
        <div style="font-size:11px;color:var(--t3);margin-top:5px;">${c.disease}</div>
      </div>
    `).join('');
  },

  // ==========================================
  // CONTACT INFO
  // ==========================================

  initContactInfo() {
    const container = document.getElementById('contactInfo');
    if (!container) return;

    const contacts = [
      { icon: '📞', label: 'TÉLÉPHONE', value: '037 20 XX XX' },
      { icon: '📧', label: 'E-MAIL', value: 'dsa.guelma@agriculture.gov.dz' },
      { icon: '📍', label: 'ADRESSE', value: 'Cité Administrative, Guelma 24000' },
      { icon: '🕐', label: 'HORAIRES', value: 'Dim–Jeu : 08h00–16h30' }
    ];

    container.innerHTML = contacts.map(c => `
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:36px;height:36px;background:rgba(74,222,128,.1);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">${c.icon}</div>
        <div>
          <div style="font-size:11px;color:var(--tm);letter-spacing:.5px;">${c.label}</div>
          <div style="font-size:14px;color:var(--t1);font-weight:600;">${c.value}</div>
        </div>
      </div>
    `).join('');
  },

  // ==========================================
  // TOAST NOTIFICATIONS
  // ==========================================

  initToast() {
    // Create toast container if it doesn't exist
    if (!document.querySelector('.toast-container')) {
      const toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container';
      toastContainer.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:1000;display:flex;flex-direction:column;gap:8px;';
      document.body.appendChild(toastContainer);
    }
  },

  showToast(message, type = 'success', duration = 4000) {
    const container = document.querySelector('.toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      padding: 16px 24px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 500;
      background: ${type === 'success' ? 'rgba(34,197,94,.9)' : type === 'error' ? 'rgba(248,113,113,.9)' : 'rgba(251,191,36,.9)'};
      color: ${type === 'warning' ? '#1a1a1a' : 'white'};
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      transform: translateX(120%);
      transition: transform .3s ease;
    `;

    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
    });

    // Auto remove
    setTimeout(() => {
      toast.style.transform = 'translateX(120%)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
};

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  Animation.init();
});
