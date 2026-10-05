/**
 * auth.js — PhytoSentinel
 * Module d'authentification centralisé
 *
 * - Stockage : localStorage (token + user)
 * - Backend  : /api/auth/login | /api/auth/verify
 * - Rôles    : admin → admin.html | farmer/expert/technician → agriculteur.html
 */

const API_BASE = "http://localhost:5000";

const STORAGE_TOKEN = "phyto_token";
const STORAGE_USER = "phyto_user";

const ROLE_REDIRECTS = {
  admin: "admin.html",
  farmer: "agriculteur.html",
  expert: "agriculteur.html",
  technician: "agriculteur.html",
};

// ── Lecture du stockage ────────────────────────────────────────────────────────

function getToken() {
  return localStorage.getItem(STORAGE_TOKEN) || null;
}

function getUser() {
  try {
    const raw = localStorage.getItem(STORAGE_USER);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function isAuthenticated() {
  return !!getToken();
}

// ── Écriture / suppression ────────────────────────────────────────────────────

function saveSession(token, user) {
  localStorage.setItem(STORAGE_TOKEN, token);
  localStorage.setItem(STORAGE_USER, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(STORAGE_TOKEN);
  localStorage.removeItem(STORAGE_USER);
}

// ── Déconnexion ───────────────────────────────────────────────────────────────

function logout() {
  clearSession();
  window.location.href = "login.html";
}

// ── Redirection après connexion ───────────────────────────────────────────────

function redirectByRole(user) {
  const page = ROLE_REDIRECTS[user.role] || "agriculteur.html";
  window.location.replace(page);
}

// ── Vérification serveur (silencieuse) ────────────────────────────────────────

async function verifyTokenOnServer() {
  const token = getToken();
  if (!token) return false;
  try {
    const res = await fetch(`${API_BASE}/api/auth/verify`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) return true;
    clearSession();
    return false;
  } catch {
    // Serveur injoignable → on laisse continuer (mode offline/dev)
    return true;
  }
}

// ── Protection automatique des pages ─────────────────────────────────────────
// Toute page qui inclut ce script (sauf login.html) est protégée.

const _onLoginPage = window.location.pathname.endsWith("login.html");

if (!_onLoginPage) {
  if (!isAuthenticated()) {
    window.location.replace("login.html");
  } else {
    // Vérification asynchrone en arrière-plan (invalide les tokens expirés)
    verifyTokenOnServer().catch(() => {
      /* silencieux */
    });
  }
}

// ── Injection du nom/rôle dans l'interface ───────────────────────────────────

function injectUserInfo(
  nameSelector = "#sidebarUserName",
  roleSelector = null,
) {
  const user = getUser();
  if (!user) return;

  const nameEl = document.querySelector(nameSelector);
  if (nameEl) nameEl.textContent = user.full_name || user.username;

  if (roleSelector) {
    const roleEl = document.querySelector(roleSelector);
    const labels = {
      admin: "Administrateur",
      expert: "Expert",
      technician: "Technicien",
      farmer: "Agriculteur",
    };
    if (roleEl) roleEl.textContent = labels[user.role] || user.role;
  }
}
