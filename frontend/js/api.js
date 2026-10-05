/**
 * PhytoSentinel API Module
 * Gère toutes les communications avec le backend
 */

const API = {
  // Configuration
  config: {
    baseUrl: '/api/v1',
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000
  },

  /**
   * Effectue une requête HTTP
   */
  async request(endpoint, options = {}) {
    const url = `${this.config.baseUrl}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      timeout: this.config.timeout
    };

    const mergedOptions = { ...defaultOptions, ...options };

    try {
      const response = await this.fetchWithTimeout(url, mergedOptions);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  },

  /**
   * Fetch avec timeout
   */
  async fetchWithTimeout(url, options) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), options.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      return response;
    } finally {
      clearTimeout(timeout);
    }
  },

  /**
   * Gère la réponse HTTP
   */
  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(response.status, error.message || 'Erreur serveur', error);
    }
    return response.json();
  },

  /**
   * Gère les erreurs
   */
  handleError(error) {
    if (error instanceof APIError) {
      throw error;
    }
    if (error.name === 'AbortError') {
      throw new APIError(408, 'Délai d\'attente dépassé', {});
    }
    throw new APIError(0, 'Erreur de connexion', { original: error.message });
  },

  // ==========================================
  // ENDPOINTS D'ANALYSE
  // ==========================================

  /**
   * Envoie une image pour analyse IA
   * @param {File} file - Image à analyser
   * @param {Object} metadata - Métadonnées (localisation, culture, etc.)
   */
  async analyzeImage(file, metadata = {}) {
    const formData = new FormData();
    formData.append('image', file);

    // Ajouter les métadonnées
    if (metadata.location) formData.append('location', metadata.location);
    if (metadata.culture) formData.append('culture', metadata.culture);
    if (metadata.commune) formData.append('commune', metadata.commune);
    if (metadata.agentId) formData.append('agent_id', metadata.agentId);

    const response = await fetch(`${this.config.baseUrl}/predict`, {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(response.status, error.message || 'Erreur d\'analyse', error);
    }

    return response.json();
  },

  /**
   * Récupère l'historique des analyses
   * @param {Object} filters - Filtres optionnels
   */
  async getAnalysisHistory(filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    return this.request(`/analyses?${queryParams}`);
  },

  /**
   * Récupère les détails d'une analyse
   * @param {string} analysisId - ID de l'analyse
   */
  async getAnalysis(analysisId) {
    return this.request(`/analyses/${analysisId}`);
  },

  // ==========================================
  // ENDPOINTS CLIMATIQUES
  // ==========================================

  /**
   * Récupère les conditions climatiques actuelles
   */
  async getWeather() {
    return this.request('/weather/current');
  },

  /**
   * Récupère les prévisions de risque
   */
  async getRiskForecast() {
    return this.request('/weather/forecast');
  },

  // ==========================================
  // ENDPOINTS ALERTES
  // ==========================================

  /**
   * Récupère les alertes actives
   */
  async getAlerts() {
    return this.request('/alerts');
  },

  /**
   * Crée une nouvelle alerte
   * @param {Object} alertData - Données de l'alerte
   */
  async createAlert(alertData) {
    return this.request('/alerts', {
      method: 'POST',
      body: JSON.stringify(alertData)
    });
  },

  /**
   * Marque une alerte comme lue
   * @param {string} alertId - ID de l'alerte
   */
  async markAlertRead(alertId) {
    return this.request(`/alerts/${alertId}/read`, {
      method: 'PUT'
    });
  },

  // ==========================================
  // ENDPOINTS CARTOGRAPHIE
  // ==========================================

  /**
   * Récupère les données de carte
   */
  async getMapData() {
    return this.request('/map/data');
  },

  /**
   * Récupère les statistiques par commune
   */
  async getCommuneStats() {
    return this.request('/map/communes');
  },

  // ==========================================
  // ENDPOINTS EXPLOITATIONS & AGRICULTEURS
  // ==========================================

  /**
   * Liste des exploitations
   */
  async getExploitations(filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    return this.request(`/exploitations?${queryParams}`);
  },

  /**
   * Crée une exploitation
   */
  async createExploitation(data) {
    return this.request('/exploitations', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  /**
   * Met à jour une exploitation
   */
  async updateExploitation(id, data) {
    return this.request(`/exploitations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  /**
   * Supprime une exploitation
   */
  async deleteExploitation(id) {
    return this.request(`/exploitations/${id}`, {
      method: 'DELETE'
    });
  },

  /**
   * Liste des agriculteurs
   */
  async getAgriculteurs(filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    return this.request(`/agriculteurs?${queryParams}`);
  },

  /**
   * Crée un agriculteur
   */
  async createAgriculteur(data) {
    return this.request('/agriculteurs', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  // ==========================================
  // ENDPOINTS STATISTIQUES
  // ==========================================

  /**
   * Statistiques générales
   */
  async getStats() {
    return this.request('/stats');
  },

  /**
   * Évolution mensuelle
   */
  async getMonthlyEvolution() {
    return this.request('/stats/monthly');
  },

  /**
   * Statistiques par culture
   */
  async getCultureStats() {
    return this.request('/stats/cultures');
  },

  /**
   * Prévisions IA
   */
  async getPredictions() {
    return this.request('/ai/predictions');
  },

  // ==========================================
  // ENDPOINTS AUTHENTIFICATION
  // ==========================================

  /**
   * Connexion
   */
  async login(credentials) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  },

  /**
   * Déconnexion
   */
  async logout() {
    return this.request('/auth/logout', {
      method: 'POST'
    });
  },

  /**
   * Vérifie la session
   */
  async checkSession() {
    return this.request('/auth/session');
  },

  // ==========================================
  // ENDPOINTS SIGNALEMENT
  // ==========================================

  /**
   * Envoie un signalement
   */
  async submitReport(data) {
    return this.request('/reports', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  /**
   * Génère un PDF de rapport
   * @param {string} analysisId - ID de l'analyse
   */
  async generatePDF(analysisId) {
    const response = await fetch(`${this.config.baseUrl}/analyses/${analysisId}/pdf`, {
      method: 'GET',
      headers: {
        'Accept': 'application/pdf'
      }
    });

    if (!response.ok) {
      throw new APIError(response.status, 'Erreur génération PDF');
    }

    return response.blob();
  },

  // ==========================================
  // ENDPOINTS TICKETS
  // ==========================================

  /**
   * Liste des tickets
   */
  async getTickets(filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    return this.request(`/tickets?${queryParams}`);
  },

  /**
   * Crée un ticket
   */
  async createTicket(data) {
    return this.request('/tickets', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  /**
   * Met à jour un ticket
   */
  async updateTicket(id, data) {
    return this.request(`/tickets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
};

/**
 * Classe d'erreur API
 */
class APIError extends Error {
  constructor(status, message, details = {}) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }

  toString() {
    return `APIError [${this.status}]: ${this.message}`;
  }
}

// Export pour usage comme module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { API, APIError };
}
