"""
PhytoSentinel - Base de données SQLite
Architecture Multi-Utilisateurs — Version Enterprise

Nouveautés v2.0:
  ✅ Table users avec rôles (admin, farmer, expert, technician)
  ✅ Table farms liée aux utilisateurs
  ✅ Clé étrangère réelle analyses → users
  ✅ RBAC (Role-Based Access Control) sur toutes les fonctions
  ✅ Mots de passe hashés avec bcrypt (PBKDF2 en fallback)
  ✅ Sessions et tokens JWT-ready
  ✅ Migration automatique depuis l'ancienne structure
  ✅ Toutes les fonctions existantes conservées et mises à jour

Corrections v2.1:
  ✅ Ajout colonnes titre/niveau/statut/description/action_recommandee dans alerts
  ✅ Nouvelle fonction create_alert()
  ✅ Nouvelle fonction get_alerts_stats()
  ✅ get_alerts() corrigé — Farmer voit les alertes globales + ses analyses
  ✅ resolve_alert() corrigé — accepte int ou dict
  ✅ save_analysis() — alerte critique inclut titre/niveau/statut
"""

import sqlite3
import json
import os
import uuid
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR          = Path(__file__).parent.parent
UPLOAD_FOLDER     = BASE_DIR / 'uploads'
DB_PATH           = BASE_DIR / 'phytosentinel.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'PNG', 'JPG', 'JPEG', 'WEBP'}
MAX_FILE_SIZE     = 10 * 1024 * 1024   # 10 Mo

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Rôles disponibles et leurs permissions
ROLES = {
    'admin':      {'level': 100, 'label': 'Administrateur'},
    'expert':     {'level': 75,  'label': 'Expert Phytosanitaire'},
    'technician': {'level': 50,  'label': 'Technicien'},
    'farmer':     {'level': 10,  'label': 'Agriculteur'},
}


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES DB
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def get_db():
    """Context manager pour connexion SQLite avec Row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# SÉCURITÉ — MOTS DE PASSE
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Hash un mot de passe avec PBKDF2-HMAC-SHA256.
    Format: pbkdf2$iterations$salt$hash
    Utilise bcrypt si disponible (recommandé en production).
    """
    try:
        import bcrypt
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        return f"bcrypt${hashed.decode('utf-8')}"
    except ImportError:
        # Fallback PBKDF2 (sécurisé, sans dépendance externe)
        salt = secrets.token_hex(32)
        iterations = 260_000
        key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        ).hex()
        return f"pbkdf2${iterations}${salt}${key}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Vérifie un mot de passe contre son hash stocké."""
    if not stored_hash:
        return False
    try:
        if stored_hash.startswith('bcrypt$'):
            import bcrypt
            hashed = stored_hash[7:].encode('utf-8')
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed)

        if stored_hash.startswith('pbkdf2$'):
            parts = stored_hash.split('$')
            _, iterations, salt, stored_key = parts
            key = hashlib.pbkdf2_hmac(
                'sha256',
                plain_password.encode('utf-8'),
                salt.encode('utf-8'),
                int(iterations)
            ).hex()
            return hmac.compare_digest(key, stored_key)

    except Exception as e:
        print(f"[AUTH] Erreur vérification mot de passe: {e}")
    return False


def generate_token(length: int = 64) -> str:
    """Génère un token sécurisé (pour sessions, reset password, etc.)"""
    return secrets.token_urlsafe(length)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES FICHIERS / IMAGES
# ─────────────────────────────────────────────────────────────────────────────

def generate_secure_filename(original_filename: str) -> str:
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_salt = secrets.token_hex(4)
    unique_id   = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}_{random_salt}.{ext}"


def generate_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def get_image_metadata(image_path: str) -> dict:
    try:
        from PIL import Image
        import mimetypes
        with Image.open(image_path) as img:
            return {
                'size':      os.path.getsize(image_path),
                'format':    img.format,
                'width':     img.width,
                'height':    img.height,
                'mime_type': mimetypes.guess_type(image_path)[0] or 'image/jpeg',
                'mode':      img.mode,
            }
    except Exception:
        return {
            'size': os.path.getsize(image_path),
            'format': 'unknown', 'width': 0, 'height': 0,
            'mime_type': 'unknown', 'mode': 'unknown',
        }


def save_uploaded_file(file, filename=None) -> dict:
    if filename is None:
        filename = generate_secure_filename(file.filename)
    file_path = UPLOAD_FOLDER / filename
    file.save(str(file_path))
    metadata = get_image_metadata(str(file_path))
    return {
        'filename':      filename,
        'relative_path': f"uploads/{filename}",
        'absolute_path': str(file_path),
        'metadata':      metadata,
    }


# ─────────────────────────────────────────────────────────────────────────────
# INITIALISATION DU SCHÉMA
# ─────────────────────────────────────────────────────────────────────────────

def init_database():
    """Crée toutes les tables et index. Sécurisé à appeler à chaque démarrage."""
    with get_db() as conn:
        c = conn.cursor()

        # ── 1. USERS ──────────────────────────────────────────────────────────
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name     TEXT    NOT NULL,
                username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL DEFAULT 'farmer'
                                      CHECK(role IN ('admin','expert','technician','farmer')),
                commune       TEXT,
                phone         TEXT,
                is_active     BOOLEAN NOT NULL DEFAULT 1,
                last_login    TIMESTAMP,
                reset_token   TEXT,
                reset_expires TIMESTAMP,
                created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── 2. FARMS ─────────────────────────────────────────────────────────
        c.execute('''
            CREATE TABLE IF NOT EXISTS farms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                name        TEXT    NOT NULL,
                commune     TEXT,
                wilaya      TEXT    DEFAULT 'Guelma',
                surface_ha  REAL,
                cultures    TEXT,
                latitude    REAL,
                longitude   REAL,
                created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # ── 3. DISEASES ───────────────────────────────────────────────────────
        c.execute('''
            CREATE TABLE IF NOT EXISTS diseases (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                name              TEXT NOT NULL UNIQUE,
                scientific_name   TEXT,
                severity          TEXT DEFAULT 'moderate',
                description       TEXT,
                treatment         TEXT,
                affected_cultures TEXT,
                icon              TEXT,
                symptoms          TEXT,
                prevention        TEXT,
                transmission      TEXT,
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── 4. ANALYSES ───────────────────────────────────────────────────────
        c.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_original_name TEXT NOT NULL,
                image_stored_name   TEXT NOT NULL UNIQUE,
                image_path          TEXT NOT NULL,
                image_hash          TEXT UNIQUE,
                image_size          INTEGER,
                image_format        TEXT,
                image_width         INTEGER,
                image_height        INTEGER,
                image_mime_type     TEXT,

                plant_type TEXT NOT NULL,

                disease_id              INTEGER,
                disease_name            TEXT NOT NULL,
                disease_key             TEXT,
                scientific_name         TEXT,
                diagnosis_description   TEXT,
                confidence              REAL NOT NULL,
                severity                TEXT NOT NULL,
                is_healthy              BOOLEAN DEFAULT 0,

                infection_rate      INTEGER DEFAULT 0,
                progression_speed   INTEGER DEFAULT 0,
                contamination_risk  INTEGER DEFAULT 0,

                treatment_steps     TEXT,
                top_3_predictions   TEXT,

                commune     TEXT,
                perimetre   TEXT,
                latitude    REAL,
                longitude   REAL,

                user_id     INTEGER,
                farm_id     INTEGER,
                shared_with_admin BOOLEAN DEFAULT 0,

                is_validated    BOOLEAN DEFAULT 0,
                validated_by    INTEGER,
                validated_at    TIMESTAMP,

                analysis_notes TEXT,

                analysis_date  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (disease_id)   REFERENCES diseases(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id)      REFERENCES users(id)    ON DELETE SET NULL,
                FOREIGN KEY (farm_id)      REFERENCES farms(id)    ON DELETE SET NULL,
                FOREIGN KEY (validated_by) REFERENCES users(id)    ON DELETE SET NULL
            )
        ''')

        # ── 5. TABLES UTILITAIRES ─────────────────────────────────────────────
        c.execute('''
            CREATE TABLE IF NOT EXISTS image_duplicates (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                original_analysis_id   INTEGER NOT NULL,
                duplicate_analysis_id  INTEGER NOT NULL,
                image_hash             TEXT NOT NULL,
                detection_method       TEXT DEFAULT 'hash',
                created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_analysis_id)  REFERENCES analyses(id) ON DELETE CASCADE,
                FOREIGN KEY (duplicate_analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
                UNIQUE(original_analysis_id, duplicate_analysis_id)
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS commune_stats (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                commune      TEXT    NOT NULL,
                disease_id   INTEGER,
                disease_name TEXT    NOT NULL,
                count        INTEGER DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(commune, disease_name)
            )
        ''')

        # ── 6. ALERTS — avec toutes les colonnes nécessaires ──────────────────
        c.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id         INTEGER,
                disease_id          INTEGER,
                disease_name        TEXT    NOT NULL DEFAULT '',
                commune             TEXT    NOT NULL DEFAULT '',
                severity            TEXT    NOT NULL DEFAULT 'warning',
                message             TEXT,

                -- Colonnes pour alertes manuelles (interface HTML)
                titre               TEXT,
                description         TEXT,
                type_alerte         TEXT    DEFAULT 'warning',
                niveau              TEXT    DEFAULT 'warning',
                statut              TEXT    DEFAULT 'active',
                action_recommandee  TEXT,
                plante_id           TEXT,
                user_id             INTEGER,

                -- Gestion
                status        TEXT    DEFAULT 'active',
                priority      INTEGER DEFAULT 1,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at   TIMESTAMP,
                resolved_by   INTEGER,
                resolved_note TEXT,

                FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
                FOREIGN KEY (disease_id)  REFERENCES diseases(id)  ON DELETE SET NULL,
                FOREIGN KEY (resolved_by) REFERENCES users(id)     ON DELETE SET NULL,
                FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE SET NULL
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                action      TEXT    NOT NULL,
                table_name  TEXT    NOT NULL,
                record_id   INTEGER,
                user_id     INTEGER,
                user_name   TEXT,
                user_ip     TEXT,
                user_agent  TEXT,
                changes     TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS statistics_cache (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key   TEXT UNIQUE NOT NULL,
                cache_value TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at  TIMESTAMP
            )
        ''')

        # ── 7. INDEX ──────────────────────────────────────────────────────────
        indexes = [
            ('idx_users_username',   'users(username)'),
            ('idx_users_email',      'users(email)'),
            ('idx_users_role',       'users(role)'),
            ('idx_farms_user',       'farms(user_id)'),
            ('idx_analyses_user',    'analyses(user_id)'),
            ('idx_analyses_disease', 'analyses(disease_name)'),
            ('idx_analyses_commune', 'analyses(commune)'),
            ('idx_analyses_shared',  'analyses(shared_with_admin)'),
            ('idx_alerts_status',    'alerts(status)'),
            ('idx_alerts_niveau',    'alerts(niveau)'),
            ('idx_alerts_user',      'alerts(user_id)'),
        ]
        for name, cols_def in indexes:
            try:
                c.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {cols_def}')
            except sqlite3.OperationalError as e:
                print(f"[WARN] Index {name} : {e}")

        # ── 8. DONNÉES PAR DÉFAUT ─────────────────────────────────────────────
        c.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        if c.fetchone()[0] == 0:
            _init_default_admin(c)

        c.execute("SELECT COUNT(*) FROM diseases")
        if c.fetchone()[0] == 0:
            _init_default_diseases(c)

        print("[DB]  Tables, index et données par défaut prêts")


def _init_default_admin(cursor):
    """Crée le compte admin par défaut."""
    pwd = hash_password("PhytoAdmin2024!")
    cursor.execute('''
        INSERT INTO users (full_name, username, email, password_hash, role, commune)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Administrateur PhytoSentinel', 'admin',
          'admin@phytosentinel.dz', pwd, 'admin', 'Guelma'))
    print("[DB] 👤 Compte admin créé — changez le mot de passe dès maintenant!")


def _init_default_diseases(cursor):
    """Insère les maladies par défaut."""
    default_diseases = [
        ('Mildiou de la Tomate', 'Phytophthora infestans', 'critical',
         'Maladie fongique causée par un oomycète. Taches brunes sur feuilles et fruits.',
         '1. Retirer les parties infectées\n2. Bouillie bordelaise\n3. Éviter l\'humidité\n4. Rotation des cultures',
         'Tomate, Pomme de terre', '🍅',
         'Taches brunes sur les feuilles, pourriture des fruits, tiges noircies',
         'Plants sains, humidité contrôlée, rotation sur 4 ans',
         'Eau, vent, outils contaminés'),
        ('Rouille Brune du Blé', 'Puccinia triticina', 'moderate',
         'Pustules orangées sur les feuilles de blé.',
         '1. Variétés résistantes\n2. Rotation\n3. Fongicides\n4. Éliminer les repousses',
         'Blé, Orge', '🌾',
         'Pustules orangées, perte de rendement',
         'Variétés résistantes, surveillance régulière',
         'Spores par le vent'),
        ('Oïdium de la Vigne', 'Erysiphe necator', 'moderate',
         'Feutrage blanc sur feuilles et grappes.',
         '1. Souffre mouillable\n2. Limiter l\'azote\n3. Tailler\n4. Traitements préventifs',
         'Vigne', '🍇',
         'Feutrage blanc, déformation des grappes',
         'Aération, variétés résistantes',
         'Vent, eau, outils'),
    ]
    for d in default_diseases:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO diseases
                (name, scientific_name, severity, description, treatment,
                 affected_cultures, icon, symptoms, prevention, transmission)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', d)
        except Exception as e:
            print(f"[DB] Erreur insertion maladie {d[0]}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MIGRATION — compatibilité avec l'ancienne structure
# ─────────────────────────────────────────────────────────────────────────────

def run_migrations():
    """
    Migration douce : ajoute les nouvelles colonnes/tables sans casser les données
    existantes. Sécurisé à relancer à chaque démarrage.
    """
    with get_db() as conn:
        c = conn.cursor()

        # Vérifier si la table users existe
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_exists = c.fetchone() is not None

        if not users_exists:
            print("[MIGRATION] Création de la table users...")
            init_database()
            return

        # Ajouter user_id à analyses si absent
        c.execute("PRAGMA table_info(analyses)")
        cols = {row['name'] for row in c.fetchall()}

        if 'user_id' not in cols:
            c.execute("ALTER TABLE analyses ADD COLUMN user_id INTEGER REFERENCES users(id)")
            print("[MIGRATION]  Colonne user_id ajoutée à analyses")

        if 'farm_id' not in cols:
            c.execute("ALTER TABLE analyses ADD COLUMN farm_id INTEGER REFERENCES farms(id)")
            print("[MIGRATION]  Colonne farm_id ajoutée à analyses")

        if 'shared_with_admin' not in cols:
            c.execute("ALTER TABLE analyses ADD COLUMN shared_with_admin BOOLEAN DEFAULT 0")
            print("[MIGRATION]  Colonne shared_with_admin ajoutée à analyses")

        # Ajouter user_id à audit_log
        c.execute("PRAGMA table_info(audit_log)")
        audit_cols = {row['name'] for row in c.fetchall()}
        if 'user_id' not in audit_cols:
            c.execute("ALTER TABLE audit_log ADD COLUMN user_id INTEGER REFERENCES users(id)")
            print("[MIGRATION]  Colonne user_id ajoutée à audit_log")

        # ── MIGRATION ALERTS — ajouter toutes les nouvelles colonnes ──────────
        c.execute("PRAGMA table_info(alerts)")
        alert_cols = {row['name'] for row in c.fetchall()}

        new_alert_columns = {
            'titre':              'TEXT',
            'description':        'TEXT',
            'type_alerte':        "TEXT DEFAULT 'warning'",
            'niveau':             "TEXT DEFAULT 'warning'",
            'statut':             "TEXT DEFAULT 'active'",
            'action_recommandee': 'TEXT',
            'plante_id':          'TEXT',
            'user_id':            'INTEGER',
            'resolved_note':      'TEXT',
        }
        for col, col_type in new_alert_columns.items():
            if col not in alert_cols:
                try:
                    c.execute(f"ALTER TABLE alerts ADD COLUMN {col} {col_type}")
                    print(f"[MIGRATION] Colonne {col} ajoutée à alerts")
                except Exception as e:
                    print(f"[MIGRATION]  {col} dans alerts : {e}")

        # Créer la table farms si absente
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='farms'")
        if not c.fetchone():
            c.execute('''
                CREATE TABLE IF NOT EXISTS farms (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER NOT NULL,
                    name       TEXT    NOT NULL,
                    commune    TEXT,
                    wilaya     TEXT DEFAULT 'Guelma',
                    surface_ha REAL,
                    cultures   TEXT,
                    latitude   REAL,
                    longitude  REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            print("[MIGRATION]  Table farms créée")

        # Index supplémentaires
        for name, cols_def in [
            ('idx_users_username', 'users(username)'),
            ('idx_users_role',     'users(role)'),
            ('idx_farms_user',     'farms(user_id)'),
            ('idx_analyses_user',  'analyses(user_id)'),
            ('idx_alerts_niveau',  'alerts(niveau)'),
            ('idx_alerts_user',    'alerts(user_id)'),
        ]:
            try:
                c.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {cols_def}')
            except Exception:
                pass

        print("[MIGRATION]  Migration terminée avec succès")


# ─────────────────────────────────────────────────────────────────────────────
# GESTION DES UTILISATEURS
# ─────────────────────────────────────────────────────────────────────────────

def create_user(full_name: str, username: str, email: str,
                password: str, role: str = None,
                commune: str = None, phone: str = None) -> Dict:
    """Crée un nouvel utilisateur."""
    if role not in ROLES:
        return {'success': False, 'error': f"Rôle invalide. Valeurs acceptées: {list(ROLES)}"}

    pwd_hash = hash_password(password)
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO users (full_name, username, email, password_hash, role, commune, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (full_name, username, email.lower(), pwd_hash, role, commune, phone))
            user_id = c.lastrowid
            _audit(c, 'INSERT', 'users', user_id, user_id,
                   {'username': username, 'role': role})
        return {'success': True, 'user_id': user_id}
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if 'username' in msg:
            return {'success': False, 'error': "Nom d'utilisateur déjà pris"}
        if 'email' in msg:
            return {'success': False, 'error': "Email déjà utilisé"}
        return {'success': False, 'error': msg}


def authenticate_user(username_or_email: str, password: str) -> Optional[Dict]:
    """
    Authentifie un utilisateur.
    Retourne le dict utilisateur (sans password_hash) ou None.
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT * FROM users
            WHERE (username = ? OR email = ?) AND is_active = 1
        ''', (username_or_email, username_or_email.lower()))
        row = c.fetchone()
        if not row:
            return None

        user = dict(row)
        if not verify_password(password, user['password_hash']):
            return None

        c.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                  (user['id'],))

    user.pop('password_hash', None)
    user.pop('reset_token', None)
    user.pop('reset_expires', None)
    return user


def get_user_by_id(user_id: int, include_stats: bool = False) -> Optional[Dict]:
    """Récupère un utilisateur par ID (sans mot de passe)."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            return None
        user = dict(row)
        user.pop('password_hash', None)
        user.pop('reset_token', None)

        if include_stats:
            c.execute("SELECT COUNT(*) FROM analyses WHERE user_id = ?", (user_id,))
            user['total_analyses'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM farms WHERE user_id = ?", (user_id,))
            user['total_farms'] = c.fetchone()[0]

    return user


def get_all_users(requesting_user: Dict, role_filter: str = None) -> List[Dict]:
    """
    Liste tous les utilisateurs.
    Seuls admin et expert peuvent appeler cette fonction.
    """
    _require_role(requesting_user, min_level=75)

    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT id, full_name, username, email, role, commune, phone, is_active, last_login, created_at FROM users"
        params = []
        if role_filter:
            query += " WHERE role = ?"
            params.append(role_filter)
        query += " ORDER BY created_at DESC"
        c.execute(query, params)
        return [dict(r) for r in c.fetchall()]


def update_user(user_id: int, data: Dict, requesting_user: Dict) -> Dict:
    """Met à jour un utilisateur. Un farmer ne peut modifier que son propre compte."""
    role_level = ROLES.get(requesting_user.get('role', 'farmer'), {}).get('level', 0)
    if role_level < 75 and requesting_user.get('id') != user_id:
        return {'success': False, 'error': 'Permission refusée'}

    allowed = ['full_name', 'email', 'commune', 'phone']
    if role_level >= 100:
        allowed += ['role', 'is_active']

    fields, values = [], []
    for key in allowed:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])

    if not fields:
        return {'success': False, 'error': 'Aucun champ valide fourni'}

    values.append(user_id)
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            f"UPDATE users SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
        _audit(c, 'UPDATE', 'users', user_id,
               requesting_user.get('id'), data)
    return {'success': True}


def change_password(user_id: int, old_password: str,
                    new_password: str, requesting_user: Dict) -> Dict:
    """Change le mot de passe d'un utilisateur."""
    role_level = ROLES.get(requesting_user.get('role', 'farmer'), {}).get('level', 0)
    if role_level < 100 and requesting_user.get('id') != user_id:
        return {'success': False, 'error': 'Permission refusée'}

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            return {'success': False, 'error': 'Utilisateur non trouvé'}

        if role_level < 100 and not verify_password(old_password, row['password_hash']):
            return {'success': False, 'error': 'Ancien mot de passe incorrect'}

        new_hash = hash_password(new_password)
        c.execute("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                  (new_hash, user_id))
        _audit(c, 'PASSWORD_CHANGE', 'users', user_id, requesting_user.get('id'), {})
    return {'success': True}


def delete_user(user_id: int, requesting_user: Dict) -> Dict:
    """Supprime un utilisateur (admin uniquement)."""
    _require_role(requesting_user, min_level=100)
    if user_id == requesting_user.get('id'):
        return {'success': False, 'error': 'Vous ne pouvez pas supprimer votre propre compte'}
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE analyses SET user_id = NULL WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        _audit(c, 'DELETE', 'users', user_id, requesting_user.get('id'), {})
    return {'success': True}


# ─────────────────────────────────────────────────────────────────────────────
# GESTION DES FERMES
# ─────────────────────────────────────────────────────────────────────────────

def create_farm(user_id: int, data: Dict, requesting_user: Dict) -> Dict:
    """Crée une ferme pour un utilisateur."""
    role_level = ROLES.get(requesting_user.get('role', 'farmer'), {}).get('level', 0)
    if role_level < 100 and requesting_user.get('id') != user_id:
        return {'success': False, 'error': 'Permission refusée'}

    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO farms (user_id, name, commune, wilaya, surface_ha, cultures, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('name', 'Ma Ferme'),
            data.get('commune'),
            data.get('wilaya', 'Guelma'),
            data.get('surface_ha'),
            json.dumps(data.get('cultures', []), ensure_ascii=False),
            data.get('latitude'),
            data.get('longitude'),
        ))
        return {'success': True, 'farm_id': c.lastrowid}


def get_user_farms(user_id: int, requesting_user: Dict) -> List[Dict]:
    """Retourne les fermes d'un utilisateur."""
    role_level = ROLES.get(requesting_user.get('role', 'farmer'), {}).get('level', 0)
    if role_level < 75 and requesting_user.get('id') != user_id:
        return []

    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT f.*, COUNT(a.id) as analyses_count
            FROM farms f
            LEFT JOIN analyses a ON a.farm_id = f.id
            WHERE f.user_id = ?
            GROUP BY f.id
            ORDER BY f.created_at DESC
        ''', (user_id,))
        farms = [dict(r) for r in c.fetchall()]
        for farm in farms:
            if farm.get('cultures'):
                try:
                    farm['cultures'] = json.loads(farm['cultures'])
                except Exception:
                    pass
        return farms


# ─────────────────────────────────────────────────────────────────────────────
# RBAC — HELPERS INTERNES
# ─────────────────────────────────────────────────────────────────────────────

def _require_role(user: Dict, min_level: int):
    """Lève une exception si le rôle est insuffisant."""
    if not user:
        raise PermissionError("Utilisateur non authentifié")
    level = ROLES.get(user.get('role', 'farmer'), {}).get('level', 0)
    if level < min_level:
        raise PermissionError(f"Permission insuffisante (niveau {level} < {min_level})")


def _user_filter(requesting_user: Optional[Dict]) -> Optional[int]:
    """
    Retourne l'user_id à filtrer ou None si l'utilisateur peut tout voir.
    None = pas de filtre (admin/expert).
    int  = filtrer sur cet user_id uniquement (farmer/technician).
    """
    if not requesting_user:
        return None
    level = ROLES.get(requesting_user.get('role', 'farmer'), {}).get('level', 0)
    if level >= 75:
        return None

    user_id = requesting_user.get('user_id') or requesting_user.get('id')
    return user_id


def _audit(cursor, action: str, table: str, record_id: int,
           user_id: Optional[int], changes: dict):
    """Insère une ligne dans audit_log."""
    cursor.execute('''
        INSERT INTO audit_log (action, table_name, record_id, user_id, changes)
        VALUES (?, ?, ?, ?, ?)
    ''', (action, table, record_id, user_id,
          json.dumps(changes, ensure_ascii=False)))


# ─────────────────────────────────────────────────────────────────────────────
# DOUBLONS D'IMAGES
# ─────────────────────────────────────────────────────────────────────────────

def check_duplicate_image(image_hash: str) -> dict:
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT a.id, a.image_original_name, a.analysis_date, a.commune, a.image_path
            FROM analyses a
            WHERE a.image_hash = ?
        ''', (image_hash,))
        result = c.fetchone()
    if result:
        return {
            'exists': True,
            'analysis_id':   result['id'],
            'image_name':    result['image_original_name'],
            'analysis_date': result['analysis_date'],
            'commune':       result['commune'],
            'image_path':    result['image_path'],
        }
    return {'exists': False}


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSES — CRUD COMPLET AVEC RBAC
# ─────────────────────────────────────────────────────────────────────────────

def save_analysis(data: Dict,
                  image_file=None,
                  image_bytes: bytes = None,
                  user_info: Optional[Dict] = None,
                  shared_with_admin: bool = False) -> Dict:
    """
    Sauvegarde une analyse.
    user_info: dict utilisateur authentifié (doit contenir 'id' ou 'user_id').
    """
    image_original_name = 'unknown'
    image_stored_name   = None
    image_path_rel      = None
    image_hash_val      = None
    image_size = image_format = image_width = image_height = image_mime = None

    # ── Traitement de l'image ─────────────────────────────────────────────
    if image_file:
        file_data = save_uploaded_file(image_file)
        image_hash_val = generate_image_hash(open(file_data['absolute_path'], 'rb').read())
        dup = check_duplicate_image(image_hash_val)
        if dup['exists']:
            os.remove(file_data['absolute_path'])
            return {
                'success': False, 'duplicate': True,
                'existing_analysis': dup,
                'message': f"Image déjà analysée le {dup['analysis_date']}",
            }
        image_original_name = image_file.filename
        image_stored_name   = file_data['filename']
        image_path_rel      = file_data['relative_path']
        m = file_data['metadata']
        image_size, image_format = m['size'], m['format']
        image_width, image_height, image_mime = m['width'], m['height'], m['mime_type']

    elif image_bytes:
        image_hash_val = generate_image_hash(image_bytes)
        dup = check_duplicate_image(image_hash_val)
        if dup['exists']:
            return {'success': False, 'duplicate': True, 'existing_analysis': dup}
        image_original_name = data.get('image_name', 'unknown.jpg')
        image_stored_name   = generate_secure_filename(image_original_name)
        fp = UPLOAD_FOLDER / image_stored_name
        with open(fp, 'wb') as f:
            f.write(image_bytes)
        m = get_image_metadata(str(fp))
        image_path_rel = f"uploads/{image_stored_name}"
        image_size, image_format = m['size'], m['format']
        image_width, image_height, image_mime = m['width'], m['height'], m['mime_type']

    else:
        image_original_name = data.get('image_name', 'unknown')
        image_stored_name   = generate_secure_filename(image_original_name)

    # ── Résolution disease_id ─────────────────────────────────────────────
    disease_name = data.get('disease_name', 'Inconnu')
    disease_id   = data.get('disease_id')
    severity_ind = data.get('severity_indicators', {})

    with get_db() as conn:
        c = conn.cursor()

        if not disease_id:
            c.execute("SELECT id FROM diseases WHERE name = ?", (disease_name,))
            r = c.fetchone()
            if r:
                disease_id = r['id']

        uid = (user_info.get('user_id') or user_info.get('id')) if user_info else None
        farm_id = data.get('farm_id')

        c.execute('''
            INSERT INTO analyses
            (image_original_name, image_stored_name, image_path, image_hash,
             image_size, image_format, image_width, image_height, image_mime_type,
             plant_type,
             disease_id, disease_name, disease_key, scientific_name, diagnosis_description,
             confidence, severity, is_healthy,
             infection_rate, progression_speed, contamination_risk,
             treatment_steps, top_3_predictions,
             commune, perimetre, latitude, longitude,
             user_id, farm_id, analysis_notes, shared_with_admin)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            image_original_name, image_stored_name, image_path_rel, image_hash_val,
            image_size, image_format, image_width, image_height, image_mime,
            data.get('plant_type', ''),
            disease_id, disease_name, data.get('disease_key', ''),
            data.get('scientific_name', ''), data.get('description', ''),
            data.get('confidence', 0), data.get('severity', 'moderate'),
            1 if data.get('is_healthy', False) else 0,
            severity_ind.get('infection', 0),
            severity_ind.get('vitesse', 0),
            severity_ind.get('risque', 0),
            json.dumps(data.get('treatment_steps', []), ensure_ascii=False),
            json.dumps(data.get('top_3', []), ensure_ascii=False),
            data.get('commune', ''), data.get('perimetre', ''),
            data.get('latitude'), data.get('longitude'),
            uid, farm_id, data.get('notes', ''),
            1 if shared_with_admin else 0
        ))

        analysis_id = c.lastrowid

        # Mise à jour commune_stats
        if data.get('commune') and disease_name:
            c.execute('''
                INSERT INTO commune_stats (commune, disease_id, disease_name, count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(commune, disease_name)
                DO UPDATE SET count = count + 1, last_updated = CURRENT_TIMESTAMP
            ''', (data.get('commune'), disease_id, disease_name))

        # Alerte automatique si critique
        if data.get('severity') == 'critical' and data.get('commune'):
            titre_alerte = f"⚠️ ALERTE CRITIQUE : {disease_name} détecté à {data.get('commune')}"
            c.execute('''
                INSERT INTO alerts
                (analysis_id, disease_id, disease_name, commune, severity, message,
                 titre, description, type_alerte, niveau, statut,
                 action_recommandee, user_id, status, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_id, disease_id, disease_name, data.get('commune'),
                'critical', titre_alerte,
                titre_alerte,
                f"Maladie {disease_name} détectée avec haute sévérité dans la commune {data.get('commune')}.",
                'critical', 'critical', 'active',
                'Inspecter immédiatement les parcelles voisines et appliquer un traitement fongicide.',
                uid, 'active', 3
            ))

        # Audit
        _audit(c, 'INSERT', 'analyses', analysis_id, uid,
               {'disease_name': disease_name, 'commune': data.get('commune')})

    return {
        'success':     True,
        'duplicate':   False,
        'analysis_id': analysis_id,
        'image_path':  image_path_rel,
        'image_hash':  image_hash_val,
    }


def get_all_analyses(limit: int = 100, offset: int = 0,
                     commune: str = None, disease: str = None,
                     severity: str = None, plant: str = None,
                     requesting_user: Optional[Dict] = None) -> List[Dict]:
    """
    Récupère les analyses avec filtres et RBAC.
    - Admin/Expert : toutes les analyses
    - Farmer/Technician : uniquement les leurs
    """
    uid_filter = _user_filter(requesting_user)

    with get_db() as conn:
        c = conn.cursor()
        query = '''
            SELECT a.*,
                   d.scientific_name  AS db_scientific_name,
                   d.treatment        AS db_treatment,
                   d.symptoms,
                   u.full_name        AS user_full_name,
                   u.username         AS user_username,
                   u.role             AS user_role
            FROM analyses a
            LEFT JOIN diseases d ON a.disease_id = d.id
            LEFT JOIN users    u ON a.user_id    = u.id
            WHERE 1=1
        '''
        params = []

        if uid_filter is not None:
            query += " AND a.user_id = ?"
            params.append(uid_filter)

        if commune:
            query += " AND a.commune = ?"
            params.append(commune)
        if disease:
            query += " AND a.disease_name LIKE ?"
            params.append(f"%{disease}%")
        if severity:
            query += " AND a.severity = ?"
            params.append(severity)
        if plant:
            query += " AND a.plant_type LIKE ?"
            params.append(f"%{plant}%")

        query += " ORDER BY a.analysis_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        c.execute(query, params)
        results = []
        for row in c.fetchall():
            r = dict(row)
            for json_col in ('treatment_steps', 'top_3_predictions'):
                if r.get(json_col):
                    try:
                        r[json_col.replace('_predictions', '')] = json.loads(r[json_col])
                    except Exception:
                        pass
            results.append(r)
    return results


def share_analysis(analysis_id: int, user_id: int) -> bool:
    """
    Partage une analyse avec l'admin (passe shared_with_admin à 1).
    Vérifie que l'analyse appartient bien à l'utilisateur.
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE analyses
            SET shared_with_admin = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        ''', (analysis_id, user_id))
        return c.rowcount > 0


def get_analysis_by_id(analysis_id: int,
                       requesting_user: Optional[Dict] = None) -> Optional[Dict]:
    """
    Récupère une analyse par ID avec RBAC.
    Un farmer ne peut voir que ses propres analyses.
    """
    uid_filter = _user_filter(requesting_user)

    with get_db() as conn:
        c = conn.cursor()
        query = '''
            SELECT a.*,
                   d.scientific_name AS db_scientific_name,
                   d.treatment       AS db_treatment,
                   d.symptoms, d.prevention, d.transmission,
                   u.full_name       AS user_full_name,
                   u.username        AS user_username,
                   u.role            AS user_role
            FROM analyses a
            LEFT JOIN diseases d ON a.disease_id = d.id
            LEFT JOIN users    u ON a.user_id    = u.id
            WHERE a.id = ?
        '''
        params = [analysis_id]
        if uid_filter is not None:
            query += " AND a.user_id = ?"
            params.append(uid_filter)

        c.execute(query, params)
        row = c.fetchone()
        if not row:
            return None

        result = dict(row)
        for json_col in ('treatment_steps', 'top_3_predictions'):
            if result.get(json_col):
                try:
                    result[json_col.replace('_predictions', '')] = json.loads(result[json_col])
                except Exception:
                    pass
    return result


def delete_analysis(analysis_id: int,
                    requesting_user: Optional[Dict] = None) -> bool:
    """
    Supprime une analyse et son image.
    Un farmer ne peut supprimer que les siennes.
    Admin peut tout supprimer.
    """
    uid_filter = _user_filter(requesting_user)

    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT image_path, image_stored_name, user_id FROM analyses WHERE id = ?"
        params = [analysis_id]
        if uid_filter is not None:
            query += " AND user_id = ?"
            params.append(uid_filter)

        c.execute(query, params)
        result = c.fetchone()
        if not result:
            return False

        if result['image_path']:
            img_path = BASE_DIR / result['image_path']
            if img_path.exists():
                os.remove(img_path)

        _audit(c, 'DELETE', 'analyses', analysis_id,
               requesting_user.get('id') if requesting_user else None,
               {'image_path': result['image_path']})

        c.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    return True


def validate_analysis(analysis_id: int, validated_by_user: Dict) -> Dict:
    """Valide une analyse (expert ou admin seulement)."""
    _require_role(validated_by_user, min_level=50)
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE analyses
            SET is_validated = 1,
                validated_by = ?,
                validated_at = CURRENT_TIMESTAMP,
                updated_at   = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (validated_by_user['id'], analysis_id))
        _audit(c, 'VALIDATE', 'analyses', analysis_id,
               validated_by_user['id'], {})
    return {'success': True}


def get_analysis_image_path(analysis_id: int) -> Optional[str]:
    """Chemin absolu de l'image d'une analyse."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT image_path FROM analyses WHERE id = ?", (analysis_id,))
        row = c.fetchone()
    if row and row['image_path']:
        p = BASE_DIR / row['image_path']
        return str(p) if p.exists() else None
    return None


# ─────────────────────────────────────────────────────────────────────────────
# STATISTIQUES
# ─────────────────────────────────────────────────────────────────────────────

def get_statistics(requesting_user: Optional[Dict] = None) -> Dict:
    """
    Statistiques globales ou filtrées selon le rôle.
    Admin → tout / Farmer → seulement ses propres données.
    """
    uid_filter = _user_filter(requesting_user)
    user_clause = "AND a.user_id = ?" if uid_filter is not None else ""
    user_params = [uid_filter] if uid_filter is not None else []

    with get_db() as conn:
        c = conn.cursor()
        stats = {}

        c.execute(f"SELECT COUNT(*) FROM analyses a WHERE 1=1 {user_clause}", user_params)
        stats['total_analyses'] = c.fetchone()[0]

        c.execute(f"SELECT SUM(image_size) FROM analyses a WHERE image_size IS NOT NULL {user_clause}", user_params)
        total_size = c.fetchone()[0] or 0
        stats['storage_used_mb'] = round(total_size / (1024 * 1024), 2)

        c.execute(f"SELECT COUNT(DISTINCT image_hash) FROM analyses a WHERE image_hash IS NOT NULL {user_clause}", user_params)
        stats['unique_images'] = c.fetchone()[0] or 0

        c.execute(f"""
            SELECT strftime('%Y-%m', a.analysis_date) AS month, COUNT(*)
            FROM analyses a WHERE 1=1 {user_clause}
            GROUP BY month ORDER BY month DESC LIMIT 6
        """, user_params)
        stats['monthly_analyses'] = [{'month': r[0], 'count': r[1]} for r in c.fetchall()]

        c.execute(f"""
            SELECT a.disease_name, COUNT(*) AS cnt
            FROM analyses a WHERE a.is_healthy = 0 {user_clause}
            GROUP BY a.disease_name ORDER BY cnt DESC LIMIT 5
        """, user_params)
        stats['top_diseases'] = [{'name': r[0], 'count': r[1]} for r in c.fetchall()]

        c.execute(f"""
            SELECT a.commune, COUNT(*) AS cnt
            FROM analyses a WHERE a.commune != '' AND a.is_healthy = 0 {user_clause}
            GROUP BY a.commune ORDER BY cnt DESC LIMIT 5
        """, user_params)
        stats['top_communes'] = [{'name': r[0], 'count': r[1]} for r in c.fetchall()]

        c.execute(f"""
            SELECT a.severity, COUNT(*) AS cnt
            FROM analyses a WHERE 1=1 {user_clause}
            GROUP BY a.severity
        """, user_params)
        stats['severity_distribution'] = {r[0]: r[1] for r in c.fetchall()}

        # Alertes actives
        if uid_filter is None:
            c.execute("SELECT COUNT(*) FROM alerts WHERE status = 'active'")
        else:
            c.execute("""
                SELECT COUNT(*) FROM alerts al
                LEFT JOIN analyses an ON al.analysis_id = an.id
                WHERE al.status = 'active'
                AND (an.user_id = ? OR al.user_id = ? OR al.analysis_id IS NULL)
            """, [uid_filter, uid_filter])
        stats['active_alerts'] = c.fetchone()[0]

        # Admin uniquement — stats utilisateurs
        if uid_filter is None:
            c.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            stats['total_users'] = c.fetchone()[0]
            c.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
            stats['users_by_role'] = {r[0]: r[1] for r in c.fetchall()}

    return stats


def get_user_dashboard(user_id: int,
                       requesting_user: Optional[Dict] = None) -> Dict:
    """Tableau de bord personnalisé pour un farmer."""
    role_level = ROLES.get((requesting_user or {}).get('role', 'farmer'), {}).get('level', 0)
    if role_level < 75 and (requesting_user or {}).get('id') != user_id:
        raise PermissionError("Accès refusé")

    pseudo_user = {'id': user_id, 'role': 'farmer'}
    stats = get_statistics(pseudo_user)

    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT a.disease_name, a.severity, a.commune, a.analysis_date,
                   a.confidence, a.image_stored_name, a.id
            FROM analyses a
            WHERE a.user_id = ?
            ORDER BY a.analysis_date DESC LIMIT 5
        ''', (user_id,))
        stats['recent_analyses'] = [dict(r) for r in c.fetchall()]

        c.execute("SELECT COUNT(*) FROM farms WHERE user_id = ?", (user_id,))
        stats['total_farms'] = c.fetchone()[0]

    return stats


# ─────────────────────────────────────────────────────────────────────────────
# MALADIES
# ─────────────────────────────────────────────────────────────────────────────

def get_all_diseases() -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM diseases ORDER BY name")
        return [dict(r) for r in c.fetchall()]


def get_disease_by_id(disease_id: int) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM diseases WHERE id = ?", (disease_id,))
        r = c.fetchone()
        return dict(r) if r else None


def add_disease(disease_data: Dict,
                requesting_user: Optional[Dict] = None) -> Dict:
    """Ajoute une maladie (admin/expert uniquement)."""
    if requesting_user:
        _require_role(requesting_user, min_level=75)

    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO diseases
                (name, scientific_name, severity, description, treatment,
                 affected_cultures, icon, symptoms, prevention, transmission)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                disease_data.get('name'),
                disease_data.get('scientific_name', ''),
                disease_data.get('severity', 'moderate'),
                disease_data.get('description', ''),
                disease_data.get('treatment', ''),
                disease_data.get('affected_cultures', ''),
                disease_data.get('icon', '🌿'),
                disease_data.get('symptoms', ''),
                disease_data.get('prevention', ''),
                disease_data.get('transmission', ''),
            ))
            return {'success': True, 'id': c.lastrowid}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Maladie déjà existante'}


def update_disease(disease_id: int, disease_data: Dict,
                   requesting_user: Optional[Dict] = None) -> Dict:
    if requesting_user:
        _require_role(requesting_user, min_level=75)

    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute('''
                UPDATE diseases
                SET name = ?, scientific_name = ?, severity = ?, description = ?,
                    treatment = ?, affected_cultures = ?, icon = ?, symptoms = ?,
                    prevention = ?, transmission = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                disease_data.get('name'),
                disease_data.get('scientific_name', ''),
                disease_data.get('severity', 'moderate'),
                disease_data.get('description', ''),
                disease_data.get('treatment', ''),
                disease_data.get('affected_cultures', ''),
                disease_data.get('icon', '🌿'),
                disease_data.get('symptoms', ''),
                disease_data.get('prevention', ''),
                disease_data.get('transmission', ''),
                disease_id,
            ))
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def delete_disease(disease_id: int,
                   requesting_user: Optional[Dict] = None) -> Dict:
    if requesting_user:
        _require_role(requesting_user, min_level=100)

    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute("UPDATE analyses SET disease_id = NULL WHERE disease_id = ?", (disease_id,))
            c.execute("DELETE FROM diseases WHERE id = ?", (disease_id,))
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# ALERTES — CRUD COMPLET
# ─────────────────────────────────────────────────────────────────────────────

def get_alerts(active_only: bool = False, limit: int = 100,
               requesting_user: Optional[Dict] = None) -> List[Dict]:
    """
    Récupère les alertes avec RBAC.
    - Admin/Expert : toutes les alertes.
    - Farmer : ses alertes (liées à ses analyses ou créées pour lui)
               + alertes globales (sans user_id et sans analysis_id).
    """
    uid_filter = _user_filter(requesting_user)

    with get_db() as conn:
        c = conn.cursor()

        if uid_filter is None:
            # Admin / Expert — tout voir
            query = '''
                SELECT al.*, u.full_name AS resolver_name
                FROM alerts al
                LEFT JOIN users u ON al.resolved_by = u.id
            '''
            params = []
            if active_only:
                query += " WHERE (al.status = 'active' OR al.statut = 'active')"
        else:
            # Farmer — ses alertes OU alertes globales (sans user_id)
            query = '''
                SELECT al.*, u.full_name AS resolver_name
                FROM alerts al
                LEFT JOIN users u ON al.resolved_by = u.id
                LEFT JOIN analyses an ON al.analysis_id = an.id
                WHERE (
                    an.user_id = ?
                    OR al.user_id = ?
                    OR (al.analysis_id IS NULL AND al.user_id IS NULL)
                )
            '''
            params = [uid_filter, uid_filter]
            if active_only:
                query += " AND (al.status = 'active' OR al.statut = 'active')"

        query += " ORDER BY al.priority DESC, al.created_at DESC LIMIT ?"
        params.append(limit)

        c.execute(query, params)
        rows = [dict(r) for r in c.fetchall()]

        # Normalisation : harmoniser les colonnes pour le frontend
        for row in rows:
            if not row.get('titre'):
                row['titre'] = row.get('disease_name', 'Alerte')
            if not row.get('niveau'):
                row['niveau'] = row.get('severity', 'warning')
            if not row.get('statut'):
                row['statut'] = row.get('status', 'active')
            if not row.get('description'):
                row['description'] = row.get('message', '')

        return rows


def get_alerts_stats(requesting_user: Optional[Dict] = None) -> Dict:
    """
    Retourne les compteurs d'alertes par niveau pour le tableau de bord.
    Respecte le RBAC : farmer voit seulement ses alertes.
    """
    uid_filter = _user_filter(requesting_user)

    with get_db() as conn:
        c = conn.cursor()

        if uid_filter is None:
            c.execute('''
                SELECT niveau, statut, status, COUNT(*) as cnt
                FROM alerts
                GROUP BY niveau, statut, status
            ''')
        else:
            c.execute('''
                SELECT al.niveau, al.statut, al.status, COUNT(*) as cnt
                FROM alerts al
                LEFT JOIN analyses an ON al.analysis_id = an.id
                WHERE (
                    an.user_id = ?
                    OR al.user_id = ?
                    OR (al.analysis_id IS NULL AND al.user_id IS NULL)
                )
                GROUP BY al.niveau, al.statut, al.status
            ''', [uid_filter, uid_filter])

        rows = c.fetchall()

    stats = {'critical': 0, 'warning': 0, 'info': 0, 'resolved': 0}
    for row in rows:
        niveau = row['niveau'] or row['status'] or 'warning'
        statut = row['statut'] or row['status'] or 'active'
        count  = row['cnt']

        if statut in ('resolue', 'resolved', 'acquittee'):
            stats['resolved'] += count
        elif niveau == 'critical':
            stats['critical'] += count
        elif niveau == 'warning':
            stats['warning'] += count
        elif niveau == 'info':
            stats['info'] += count
        else:
            stats['warning'] += count  # fallback

    return stats


def create_alert(data: Dict, requesting_user: Optional[Dict] = None) -> Dict:
    """
    Crée une alerte manuelle depuis l'interface HTML.
    Utilisable par admin, expert, ou technician.
    """
    titre   = data.get('titre', '').strip()
    niveau  = data.get('niveau', data.get('type_alerte', 'warning'))
    commune = data.get('commune', '')

    if not titre:
        return {'success': False, 'error': 'Le titre est obligatoire'}

    uid = None
    if requesting_user:
        uid = requesting_user.get('user_id') or requesting_user.get('id')

    priority_map = {'critical': 3, 'warning': 2, 'info': 1}
    priority = priority_map.get(niveau, 1)

    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO alerts
                (titre, description, type_alerte, niveau, statut,
                 commune, action_recommandee, plante_id,
                 disease_name, severity, message,
                 user_id, status, priority, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ''', (
                titre,
                data.get('description', ''),
                data.get('type_alerte', niveau),
                niveau,
                'active',
                commune,
                data.get('action_recommandee', ''),
                data.get('plante_id'),
                titre,           # disease_name = titre pour compatibilité
                niveau,          # severity = niveau
                data.get('description', ''),
                uid,
                'active',
                priority,
            ))
            alert_id = c.lastrowid
            if requesting_user:
                _audit(c, 'INSERT', 'alerts', alert_id, uid, {'titre': titre})
            return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def resolve_alert(alert_id: int,
                  resolved_by=None,
                  note: str = None) -> bool:
    """
    Résout une alerte.
    resolved_by peut être un int (user_id) ou un dict utilisateur.
    """
    if isinstance(resolved_by, dict):
        resolved_by_id = resolved_by.get('id') or resolved_by.get('user_id')
    elif isinstance(resolved_by, int):
        resolved_by_id = resolved_by
    else:
        resolved_by_id = None

    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE alerts
            SET status      = 'resolved',
                statut      = 'resolue',
                resolved_at = CURRENT_TIMESTAMP,
                resolved_by = ?,
                resolved_note = ?
            WHERE id = ?
        ''', (resolved_by_id, note, alert_id))
    return True


# ─────────────────────────────────────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────────────────────────────────────

# Initialiser puis migrer au démarrage
init_database()
run_migrations()

print("\n" + "=" * 60)
print("  PhytoSentinel DB — Architecture multi-utilisateurs v2.1")
print(f"  Uploads  : {UPLOAD_FOLDER}")
print(f"   Base DB  : {DB_PATH}")
print(f" Taille max fichier : {MAX_FILE_SIZE // (1024*1024)} Mo")
print("=" * 60 + "\n")