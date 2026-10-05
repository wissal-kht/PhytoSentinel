/**
 * PhytoSentinel UI Module
 * Gère les interactions utilisateur et la logique UI
 */

const UI = {
  // State
  state: {
    currentImage: null,
    isAnalyzing: false,
    analysisResult: null
  },

  // ==========================================
  // INITIALISATION (Safety Check)
  // ==========================================

  init() {
    // Attendre que le DOM soit prêt
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.initAfterDOM());
    } else {
      this.initAfterDOM();
    }
  },

  initAfterDOM() {
    try {
      this.initNavigation();
      this.initFileUpload();
      this.initScanSimulation();
      this.initContactForm();
      this.initLoginButton();
      this.initSmoothScroll();
      this.initFooterLinks();
      console.log('[PhytoSentinel] UI Initialisé avec succès');
    } catch (error) {
      console.error('[PhytoSentinel] Erreur d\'initialisation:', error);
    }
  },

  // ==========================================
  // NAVIGATION (Safe DOM Access)
  // ==========================================

  initNavigation() {
    const nav = document.getElementById('nav');
    if (!nav) return;

    // Scroll effect
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 60);

      // Update active nav link (avec vérification)
      const sections = ['hero', 'detection', 'alerte', 'carte', 'dashboard', 'contact'];
      const scrollPos = window.scrollY + 200;

      sections.forEach(id => {
        const section = document.getElementById(id);
        const link = document.querySelector(`.nav-link[data-nav="${id}"]`);
        if (section && link) {
          const isActive = scrollPos >= section.offsetTop &&
                         scrollPos < section.offsetTop + section.offsetHeight;
          link.classList.toggle('active', isActive);
        }
      });
    });

    this.updateSystemStatus();
  },

  updateSystemStatus() {
    // Fonctionnalité optionnelle
    const statusEl = document.getElementById('systemStatus');
    if (!statusEl) return;
  },

  // ==========================================
  // SMOOTH SCROLL (Safe)
  // ==========================================

  initSmoothScroll() {
    document.querySelectorAll('a[href^="#"], .hero-cta').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = el.getAttribute('href')?.substring(1) || el.dataset.target;
        const target = document.getElementById(targetId);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  },

  // ==========================================
  // FILE UPLOAD (Safe)
  // ==========================================

  initFileUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resetBtn = document.getElementById('resetBtn');

    if (!dropZone || !fileInput) return;

    // Click to upload
    uploadBtn?.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    // File selected
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleFileSelect(e.target.files[0]);
      }
    });

    // Drag and drop
    dropZone.addEventListener('click', () => {
      if (!this.state.currentImage) {
        fileInput.click();
      }
    });

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      const files = e.dataTransfer.files;
      if (files.length > 0 && files[0].type.startsWith('image/')) {
        this.handleFileSelect(files[0]);
      }
    });

    // Analyze button
    analyzeBtn?.addEventListener('click', () => {
      this.performAnalysis();
    });

    // Reset button
    resetBtn?.addEventListener('click', () => {
      this.resetUpload();
    });
  },

  handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
      this.showToast?.('Veuillez sélectionner une image valide', 'error');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.showToast?.('L\'image est trop volumineuse (max 10MB)', 'error');
      return;
    }

    this.state.currentImage = file;

    const reader = new FileReader();
    reader.onload = (e) => {
      this.showPreview(e.target.result, file.name);
    };
    reader.readAsDataURL(file);
  },

  showPreview(imageData, fileName) {
    const up1 = document.getElementById('up1');
    const up2 = document.getElementById('up2');
    const up3 = document.getElementById('up3');
    const previewContainer = document.getElementById('previewContainer');

    if (!previewContainer) return;

    if (up1) up1.style.display = 'none';
    if (up2) up2.style.display = 'none';
    if (up3) up3.style.display = 'block';

    previewContainer.innerHTML = `
      <img src="${imageData}" alt="Preview" class="preview-image" style="max-width:100%;max-height:180px;border-radius:12px;margin-bottom:12px;">
      <div style="font-size:12px;color:var(--tm);">${fileName}</div>
    `;
  },

  resetUpload() {
    const up1 = document.getElementById('up1');
    const up2 = document.getElementById('up2');
    const up3 = document.getElementById('up3');
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');

    if (up1) up1.style.display = 'block';
    if (up2) up2.style.display = 'none';
    if (up3) up3.style.display = 'none';

    if (fileInput) fileInput.value = '';
    if (dropZone) dropZone.classList.remove('scanning');
    this.state.currentImage = null;
    this.state.analysisResult = null;
    this.resetResultPanel();
  },

  // ==========================================
  // SCAN SIMULATION
  // ==========================================

  initScanSimulation() {
    // Empty - handled by performAnalysis
  },

  async performAnalysis() {
    if (!this.state.currentImage || this.state.isAnalyzing) return;

    this.state.isAnalyzing = true;
    const dropZone = document.getElementById('dropZone');
    const up1 = document.getElementById('up1');
    const up2 = document.getElementById('up2');
    const up3 = document.getElementById('up3');
    const scanTxt = document.getElementById('scanTxt');

    if (up3) up3.style.display = 'none';
    if (up2) up2.style.display = 'block';
    if (dropZone) dropZone.classList.add('scanning');

    const steps = [
      'Chargement de l\'image…',
      'Extraction des caractéristiques…',
      'Comparaison avec la base de données…',
      'Calcul de l\'indice de confiance…',
      'Génération du rapport…'
    ];

    let i = 0;
    const interval = setInterval(() => {
      if (i < steps.length && scanTxt) {
        scanTxt.textContent = steps[i++];
      }
    }, 650);

    try {
      const result = await this.simulateAPICall();

      clearInterval(interval);
      if (scanTxt) scanTxt.textContent = 'Analyse terminée ✓';

      setTimeout(() => {
        if (dropZone) dropZone.classList.remove('scanning');
        if (up2) up2.style.display = 'none';
        if (up3) up3.style.display = 'block';
        this.state.isAnalyzing = false;
        this.displayResult(result);
        this.showToast?.('Analyse terminée avec succès', 'success');
      }, 800);

    } catch (error) {
      clearInterval(interval);
      if (dropZone) dropZone.classList.remove('scanning');
      if (up2) up2.style.display = 'none';
      if (up3) up3.style.display = 'block';
      this.state.isAnalyzing = false;
      this.showToast?.('Erreur lors de l\'analyse', 'error');
    }
  },

  async simulateAPICall() {
    await new Promise(resolve => setTimeout(resolve, 3500));

    const diseases = [
      {
        disease: 'Mildiou de la Tomate',
        pathogen: 'Phytophthora infestans',
        type: 'Oomycète',
        confidence: 0.92,
        severity: 82,
        infectionLevel: 68,
        progressionSpeed: 52,
        contaminationRisk: 34,
        badge: 'b-r',
        badgeText: 'Critique',
        treatment: [
          'Pulvériser Mancozèbe 80% WP — 2 kg/ha',
          'Améliorer la ventilation inter-rangs',
          'Notifier le service DSA Guelma'
        ]
      },
      {
        disease: 'Oïdium de la Vigne',
        pathogen: 'Erysiphe necator',
        type: 'Champignon ascomycète',
        confidence: 0.87,
        severity: 45,
        infectionLevel: 38,
        progressionSpeed: 42,
        contaminationRisk: 28,
        badge: 'b-a',
        badgeText: 'Modéré',
        treatment: [
          'Application de soufre mouillable — 6 kg/ha',
          'Éliminer les feuilles infectées',
          'Surveillance de la pression maladie'
        ]
      },
      {
        disease: 'Rouille Brune du Blé',
        pathogen: 'Puccinia triticina',
        type: 'Basidiomycète',
        confidence: 0.89,
        severity: 58,
        infectionLevel: 55,
        progressionSpeed: 48,
        contaminationRisk: 42,
        badge: 'b-a',
        badgeText: 'Modéré',
        treatment: [
          'Traitement fongicide — Triazole',
          'Rotation culturales recommandées'
        ]
      },
      {
        disease: 'Plante en Bonne Santé',
        pathogen: null,
        type: null,
        confidence: 0.95,
        severity: 10,
        infectionLevel: 5,
        progressionSpeed: 2,
        contaminationRisk: 3,
        badge: 'b-g',
        badgeText: 'Bonne santé',
        treatment: [
          'Maintenir les pratiques actuelles',
          'Surveillance régulière recommandée'
        ]
      }
    ];

    return diseases[Math.floor(Math.random() * diseases.length)];
  },

  displayResult(result) {
    this.state.analysisResult = result;

    const elements = {
      disease: document.getElementById('resultDisease'),
      pathogen: document.getElementById('resultPathogen'),
      badge: document.getElementById('resultBadge'),
      confidenceRing: document.getElementById('confidenceRing'),
      confidenceText: document.getElementById('confidenceText'),
      resultConfidence: document.getElementById('resultConfidence'),
      resultLocation: document.getElementById('resultLocation'),
      resultDate: document.getElementById('resultDate'),
      infectionLevel: document.getElementById('infectionLevel'),
      infectionBar: document.getElementById('infectionBar'),
      progressionSpeed: document.getElementById('progressionSpeed'),
      progressionBar: document.getElementById('progressionBar'),
      contaminationRisk: document.getElementById('contaminationRisk'),
      contaminationBar: document.getElementById('contaminationBar'),
      treatmentSection: document.getElementById('treatmentSection'),
      treatmentSteps: document.getElementById('treatmentSteps'),
      downloadPdf: document.getElementById('downloadPdf'),
      notifyDsa: document.getElementById('notifyDsa')
    };

    if (elements.disease) elements.disease.textContent = result.disease;
    if (elements.pathogen) elements.pathogen.textContent = result.pathogen ? `${result.pathogen} — ${result.type}` : 'Aucun pathogène';
    if (elements.badge) {
      elements.badge.className = `badge ${result.badge}`;
      elements.badge.textContent = result.badgeText;
    }

    const confidencePercent = Math.round(result.confidence * 100);
    const dashOffset = 226 - (226 * confidencePercent / 100);

    if (elements.confidenceRing) elements.confidenceRing.style.strokeDashoffset = dashOffset;
    if (elements.confidenceText) elements.confidenceText.textContent = `${confidencePercent}%`;
    if (elements.resultConfidence) elements.resultConfidence.textContent = `${confidencePercent}%`;

    const communes = ['Guelma-Centre', 'Belkheir', 'Bouhamdane', 'Oued Zenati', 'Bouchegouf'];
    const commune = communes[Math.floor(Math.random() * communes.length)];
    const now = new Date();
    if (elements.resultLocation) elements.resultLocation.textContent = commune;
    if (elements.resultDate) elements.resultDate.textContent = now.toLocaleDateString('fr-FR');

    setTimeout(() => {
      if (elements.infectionLevel) elements.infectionLevel.textContent = `${result.infectionLevel}%`;
      if (elements.infectionBar) elements.infectionBar.style.width = `${result.infectionLevel}%`;
      if (elements.progressionSpeed) elements.progressionSpeed.textContent = `${result.progressionSpeed}%`;
      if (elements.progressionBar) elements.progressionBar.style.width = `${result.progressionSpeed}%`;
      if (elements.contaminationRisk) elements.contaminationRisk.textContent = `${result.contaminationRisk}%`;
      if (elements.contaminationBar) elements.contaminationBar.style.width = `${result.contaminationRisk}%`;
    }, 300);

    if (elements.treatmentSection && elements.treatmentSteps) {
      elements.treatmentSection.style.display = 'block';
      elements.treatmentSteps.innerHTML = result.treatment.map((step, i) => `
        <div style="display:flex;align-items:flex-start;gap:11px;margin-bottom:8px;">
          <div style="width:22px;height:22px;border-radius:50%;background:rgba(74,222,128,.14);border:1px solid rgba(74,222,128,.3);display:flex;align-items:center;justify-content:center;font-size:10.5px;color:var(--green);font-weight:700;flex-shrink:0;">${i + 1}</div>
          <span style="font-size:12.5px;color:var(--t3);line-height:1.5;">${step}</span>
        </div>
      `).join('');
    }

    if (elements.downloadPdf) elements.downloadPdf.disabled = false;
    if (elements.notifyDsa) elements.notifyDsa.disabled = false;
  },

  resetResultPanel() {
    const ids = ['resultDisease', 'resultPathogen', 'resultBadge', 'confidenceRing', 'confidenceText',
                 'resultConfidence', 'resultLocation', 'resultDate', 'infectionLevel', 'infectionBar',
                 'progressionSpeed', 'progressionBar', 'contaminationRisk', 'contaminationBar',
                 'treatmentSection', 'downloadPdf', 'notifyDsa'];

    const setters = {
      resultDisease: 'En attente d\'analyse',
      resultPathogen: 'Téléversez une image pour commencer',
      resultBadge: 'En attente',
      confidenceText: '—',
      resultConfidence: '—',
      resultLocation: '—',
      resultDate: '—',
      infectionLevel: '—',
      progressionSpeed: '—',
      contaminationRisk: '—',
      infectionBar: 'width:0%',
      progressionBar: 'width:0%',
      contaminationBar: 'width:0%',
      treatmentSection: 'display:none'
    };

    ids.forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      if (id === 'resultBadge') {
        el.className = 'badge b-g';
      } else if (id === 'confidenceRing') {
        el.style.strokeDashoffset = '226';
      } else if (id === 'infectionBar' || id === 'progressionBar' || id === 'contaminationBar') {
        el.style.width = '0%';
      } else if (id === 'treatmentSection') {
        el.style.display = 'none';
      } else if (id === 'downloadPdf' || id === 'notifyDsa') {
        el.disabled = true;
      } else if (setters[id]) {
        el.textContent = setters[id];
      }
    });
  },

  // ==========================================
  // CONTACT FORM
  // ==========================================

  initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      this.showToast?.('Signalement envoyé avec succès', 'success');
      form.reset();
    });

    form.querySelectorAll('input, textarea, select').forEach(input => {
      input.addEventListener('focus', () => {
        input.style.borderColor = 'rgba(74,222,128,.5)';
      });
      input.addEventListener('blur', () => {
        input.style.borderColor = 'rgba(74,222,128,.18)';
      });
    });
  },

  // ==========================================
  // LOGIN BUTTON
  // ==========================================

  initLoginButton() {
    const loginBtn = document.getElementById('loginBtn');
    if (!loginBtn) return;

    loginBtn.addEventListener('click', () => {
      this.showToast?.('Redirection vers le portail DSA…', 'success');
      setTimeout(() => {
        this.showToast?.('Fonctionnalité en cours de développement', 'warning');
      }, 1000);
    });
  },

  // ==========================================
  // FOOTER LINKS
  // ==========================================

  initFooterLinks() {
    document.querySelectorAll('.footer-link').forEach(link => {
      link.addEventListener('mouseenter', () => {
        link.style.color = 'var(--green)';
      });
      link.addEventListener('mouseleave', () => {
        link.style.color = 'var(--t3)';
      });
    });
  },

  // ==========================================
  // TOAST (Fallback si Animation non chargé)
  // ==========================================

  showToast(message, type = 'success') {
    if (typeof Animation !== 'undefined' && Animation.showToast) {
      Animation.showToast(message, type);
      return;
    }

    // Fallback simple
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed; bottom: 24px; right: 24px; padding: 16px 24px;
      border-radius: 12px; font-size: 14px; font-weight: 500; z-index: 1000;
      background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#f59e0b'};
      color: ${type === 'warning' ? '#000' : '#fff'};
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
  }
};

// Initialize UI
UI.init();
