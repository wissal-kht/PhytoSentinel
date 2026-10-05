"""
PhytoSentinel — Backend Flask
Détection des maladies des plantes via modèles .h5 pré-entraînés
Avec base de données SQLite optimisée (version production)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
from PIL import Image
import io, os, json, uuid

from pathlib import Path
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta

# ── Import Keras via tensorflow.keras (compatible TF2 natif) ─────────────────
# Les modèles DenseNet ont été entraînés avec tensorflow.keras,
# on utilise donc l'import natif (pas tf_keras legacy).
import tensorflow as tf
from tensorflow.keras.models import load_model

app = Flask(__name__)
CORS(app)

# ── Compte admin hardcodé (temporaire, en attendant la page Admin) ────────────
HARDCODED_ADMIN = {
    'username': 'admin',
    'password': 'PhytoAdmin2024!',
    'user': {
        'id': 0,
        'full_name': 'Administrateur PhytoSentinel',
        'username': 'admin',
        'email': 'admin@phytosentinel.dz',
        'role': 'admin',
        'commune': 'Guelma',
        'is_active': True,
    }
}

SECRET_KEY = os.environ.get('PHYTO_SECRET_KEY', 'phytosentinel-dev-secret-2024')

def make_token(user_id, role):
    """Génère un JWT valide 24h avec user_id ET role."""
    payload = {
        'user_id': user_id,
        'role':    role,
        'exp':     datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> dict | None:
    """Décode un JWT. Retourne le payload ou None si invalide/expiré."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except Exception:
        return None


def get_current_user() -> dict | None:
    """Extrait et valide le token Bearer de la requête courante."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    return decode_token(auth[7:])

# Configuration
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / 'uploads'
MODELS_DIR = BASE_DIR / 'models'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Mapping : clé → fichier modèle ──────────────────────────────────────────
MODEL_FILES = {
    'apple'      : 'apple_model.h5',
    'cherry'     : 'cherry_model.h5',
    'corn'       : 'corn_model.h5',
    'grape'      : 'grape_model.h5',
    'peach'      : 'peach_model.h5',
    'pepper'     : 'pepper_model.h5',
    'potato'     : 'potato_model.h5',
    'strawberry' : 'strawberry_model.h5',
    'tomato'     : 'tomato_model.h5',
}

# ── Labels par modèle ────────────────────────────────────────────────────────
# Ordre confirmé depuis train_ds.class_names de chaque notebook
# (ordre alphabétique PlantVillage = ordre réel de chaque modèle DenseNet)
LABELS = {
    'apple':      ['Apple Scab', 'Black Rot', 'Cedar Apple Rust', 'Healthy'],
    'cherry':     ['Healthy', 'Powdery Mildew'],
    'corn':       ['Common Rust', 'Gray Leaf Spot', 'Healthy', 'Northern Leaf Blight'],
    'grape':      ['Black Rot', 'Esca', 'Healthy', 'Leaf Blight'],
    'peach':      ['Bacterial Spot', 'Healthy'],
    'pepper':     ['Bacterial Spot', 'Healthy'],
    'potato':     ['Early Blight', 'Healthy', 'Late Blight'],
    'strawberry': ['Healthy', 'Leaf Scorch'],
    'tomato':     ['Bacterial Spot', 'Early Blight', 'Healthy', 'Late Blight'],
}

# ── Base de connaissances (disease_information.py) ───────────────────────────
_disease_info_path = os.path.join(os.path.dirname(__file__), 'disease_information.py')

import importlib.util
spec = importlib.util.spec_from_file_location("disease_information", _disease_info_path)
disease_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(disease_mod)
plant_disease_dict = disease_mod.plant_disease_dict

# ── Cache des modèles ────────────────────────────────────────────────────────
_loaded_models = {}

def get_model(plant_key):
    """Charge le modèle via tensorflow.keras"""
    if plant_key not in _loaded_models:
        path = os.path.join(MODELS_DIR, MODEL_FILES[plant_key])
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Modèle introuvable : {path}\n"
                f"Placez les fichiers .h5 dans le dossier 'models/'"
            )
        print(f"[INFO] Chargement du modèle '{plant_key}' depuis {path} ...")
        _loaded_models[plant_key] = load_model(path, compile=False)
        print(f"[INFO] Modèle '{plant_key}' chargé avec succès.")
    return _loaded_models[plant_key]

def preprocess_image(image_bytes):
    """
    ⚠️ IMPORTANT : Les modèles DenseNet contiennent déjà une couche
    Resizing + Rescaling interne (entraînés avec image brute 0-255).
    On envoie donc l'image en valeurs brutes [0, 255] SANS diviser par 255.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((256, 256), Image.Resampling.LANCZOS)
    arr = np.array(img, dtype=np.float32)          # ✅ PAS de / 255.0
    return np.expand_dims(arr, axis=0)              # shape : (1, 256, 256, 3)

def get_disease_info(plant_key, label):
    """Récupère les infos de la maladie depuis disease_information.py"""
    is_healthy = label == 'Healthy'

    if is_healthy:
        info = plant_disease_dict.get('Healthy', {})
        return {
            'disease_name'       : 'Plante Saine',
            'scientific_name'    : '',
            'description'        : info.get('Description', '').replace('*', ''),
            'severity'           : 'low',
            'severity_indicators': info.get('severity_indicators', {'infection': 0, 'vitesse': 0, 'risque': 0}),
            'treatment_steps'    : [],
            'is_healthy'         : True,
        }

    plant_key_cap = plant_key.capitalize()
    plant_data = plant_disease_dict.get(plant_key_cap, {})
    info = plant_data.get(label, {})

    if not info:
        return {
            'disease_name'       : label,
            'scientific_name'    : '',
            'description'        : 'Maladie détectée par le modèle IA.',
            'severity'           : 'moderate',
            'severity_indicators': {'infection': 50, 'vitesse': 40, 'risque': 45},
            'treatment_steps'    : ['Consulter un agronome pour un traitement adapté.'],
            'is_healthy'         : False,
        }

    return {
        'disease_name'       : label,
        'scientific_name'    : info.get('scientific_name', ''),
        'description'        : info.get('Description', '').replace('*', ''),
        'severity'           : info.get('severity', 'moderate'),
        'severity_indicators': info.get('severity_indicators', {'infection': 50, 'vitesse': 40, 'risque': 45}),
        'treatment_steps'    : info.get('treatment_steps', []),
        'is_healthy'         : False,
    }

def generate_secure_filename(original_filename):
    """Génère un nom de fichier sécurisé et unique"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_salt = secrets.token_hex(4)
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}_{random_salt}.{ext}"

def generate_image_hash(image_bytes):
    """Génère un hash SHA256 pour l'image"""
    return hashlib.sha256(image_bytes).hexdigest()

def get_image_metadata(image_path):
    """Récupère les métadonnées d'une image"""
    try:
        with Image.open(image_path) as img:
            return {
                'size': os.path.getsize(image_path),
                'format': img.format,
                'width': img.width,
                'height': img.height,
                'mode': img.mode
            }
    except Exception:
        return {'size': 0, 'format': 'unknown', 'width': 0, 'height': 0, 'mode': 'unknown'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Importer la base de données
import database as db

# ── Routes API ─────────────────────────────────────────────────────────────

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """Endpoint principal pour l'analyse d'image avec sauvegarde automatique"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié. Veuillez vous reconnecter.'}), 401

    # 1. Vérifier l'image
    if 'image' not in request.files:
        return jsonify({'error': 'Aucune image reçue'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Fichier vide'}), 400

    # 2. Vérifier la plante choisie
    plant_key = request.form.get('plant', '').lower()
    if plant_key not in MODEL_FILES:
        return jsonify({'error': f"Plante non reconnue : '{plant_key}'"}), 400

    # 3. Sauvegarder l'image avec nom sécurisé
    original_filename = file.filename
    secure_filename = generate_secure_filename(original_filename)
    image_path = UPLOAD_FOLDER / secure_filename

    # Lire les bytes pour le hash
    image_bytes = file.read()
    image_hash = generate_image_hash(image_bytes)

    # Vérifier les doublons
    duplicate = db.check_duplicate_image(image_hash)
    if duplicate['exists']:
        return jsonify({
            'error': 'Cette image a déjà été analysée',
            'duplicate': True,
            'existing_analysis_id': duplicate['analysis_id'],
            'existing_date': duplicate['analysis_date']
        }), 409

    # Sauvegarder le fichier
    with open(image_path, 'wb') as f:
        f.write(image_bytes)

    # Récupérer les métadonnées
    metadata = get_image_metadata(str(image_path))

    # 4. Prétraitement et prédiction
    try:
        img_array = preprocess_image(image_bytes)
    except Exception as e:
        return jsonify({'error': f'Image invalide : {str(e)}'}), 400

    try:
        model = get_model(plant_key)
        preds = model.predict(img_array, verbose=0)[0]
        labels = LABELS[plant_key]

        top_idx = int(np.argmax(preds))
        top_label = labels[top_idx]
        confidence = float(preds[top_idx])

        top3_idx = np.argsort(preds)[::-1][:3]
        top3 = [
            {'disease_key': labels[i], 'confidence': float(preds[i])}
            for i in top3_idx
        ]

    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
      import traceback
      traceback.print_exc()   # ← هذا يطبع الخطأ الكامل في الـ terminal
      return jsonify({'error': f'Erreur lors de la prédiction : {str(e)}'}), 500
    # 5. Infos depuis disease_information.py
    disease_info = get_disease_info(plant_key, top_label)

    top3_enriched = []
    for item in top3:
        lbl  = item['disease_key']
        info = get_disease_info(plant_key, lbl)
        top3_enriched.append({
            'disease_name': info['disease_name'],
            'confidence'  : item['confidence'],
        })

    # 6. Sauvegarder dans la base de données
    commune     = request.form.get('commune', '')
    perimetre   = request.form.get('perimetre', '')
    description = request.form.get('description', '')

    analysis_data = {
        'image_name'        : original_filename,
        'image_stored_name' : secure_filename,
        'image_path'        : f"uploads/{secure_filename}",
        'image_hash'        : image_hash,
        'image_size'        : metadata['size'],
        'image_format'      : metadata['format'],
        'image_width'       : metadata['width'],
        'image_height'      : metadata['height'],
        'plant_type'        : plant_key,
        'disease_name'      : disease_info.get('disease_name', ''),
        'disease_key'       : top_label,
        'scientific_name'   : disease_info.get('scientific_name', ''),
        'description'       : disease_info.get('description', ''),
        'confidence'        : confidence,
        'severity'          : disease_info.get('severity', 'moderate'),
        'is_healthy'        : disease_info.get('is_healthy', False),
        'severity_indicators': disease_info.get('severity_indicators', {}),
        'treatment_steps'   : disease_info.get('treatment_steps', []),
        'top_3'             : top3_enriched,
        'commune'           : commune,
        'perimetre'         : perimetre,
        'notes'             : description
    }

    result = db.save_analysis(analysis_data, image_bytes=image_bytes,
                              user_info=current_user, shared_with_admin=False)

    if not result['success']:
        if result.get('duplicate'):
            os.remove(image_path)
        return jsonify({'error': result.get('message', 'Erreur lors de la sauvegarde')}), 409

    # 7. Réponse
    response_data = {
        **disease_info,
        'confidence'  : confidence,
        'plant'       : plant_key.capitalize(),
        'top_3'       : top3_enriched,
        'location'    : {'commune': commune} if commune else {},
        'analysis_id' : result['analysis_id'],
        'image_hash'  : image_hash,
        'saved_to_db' : True
    }

    return jsonify(response_data)

# ==================== ROUTES ANALYSES ====================

@app.route('/api/analyses', methods=['GET'])
def get_analyses():
    """
    Récupère les analyses filtrées selon le rôle du token JWT.
    - Farmer/Technician : uniquement leurs propres analyses.
    - Admin/Expert      : toutes les analyses.
    - Sans token valide : 401.
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Token manquant ou invalide'}), 401

    limit    = request.args.get('limit',    100,  type=int)
    offset   = request.args.get('offset',   0,    type=int)
    commune  = request.args.get('commune',  None)
    disease  = request.args.get('disease',  None)
    severity = request.args.get('severity', None)
    plant    = request.args.get('plant',    None)

    analyses = db.get_all_analyses(
        limit, offset, commune, disease, severity, plant,
        requesting_user=current_user
    )
    return jsonify({'analyses': analyses, 'total': len(analyses)})


@app.route('/api/analyses/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """
    Récupère une analyse par ID.
    Un farmer ne peut accéder qu'à ses propres analyses (RBAC DB).
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Token manquant ou invalide'}), 401

    analysis = db.get_analysis_by_id(analysis_id, requesting_user=current_user)
    if analysis:
        return jsonify(analysis)
    return jsonify({'error': 'Analyse non trouvée ou accès refusé'}), 404


@app.route('/api/analyses/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """
    Supprime une analyse.
    Un farmer ne peut supprimer que ses propres analyses.
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Token manquant ou invalide'}), 401

    analysis = db.get_analysis_by_id(analysis_id, requesting_user=current_user)
    if not analysis:
        return jsonify({'error': 'Analyse non trouvée ou accès refusé'}), 404

    image_path = analysis.get('image_path')
    if image_path:
        full_path = BASE_DIR / image_path
        if full_path.exists():
            os.remove(full_path)

    db.delete_analysis(analysis_id)
    return jsonify({'success': True, 'message': 'Analyse supprimée avec succès'})


@app.route('/api/analyses/<int:analysis_id>/share', methods=['POST'])
def share_analysis(analysis_id):
    """Partage une analyse avec l'administrateur."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401

    analysis = db.get_analysis_by_id(analysis_id, requesting_user=current_user)
    if not analysis:
        return jsonify({'error': 'Analyse non trouvée ou accès refusé'}), 404

    if db.share_analysis(analysis_id, current_user['user_id']):
        return jsonify({'success': True, 'message': "Analyse partagée avec l'administrateur"})
    return jsonify({'error': 'Échec du partage'}), 500

# ==================== ROUTE DE SAVE MANUELLE ====================

@app.route('/api/save-analysis', methods=['POST'])
def save_analysis_manual():
    """Sauvegarde manuelle d'une analyse (pour le frontend)"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401

    try:
        data = request.json

        analysis_data = {
            'plant_type'        : data.get('plant_type', ''),
            'disease_name'      : data.get('disease_name', ''),
            'scientific_name'   : data.get('scientific_name', ''),
            'description'       : data.get('description', ''),
            'confidence'        : data.get('confidence', 0),
            'severity'          : data.get('severity', 'moderate'),
            'is_healthy'        : data.get('is_healthy', False),
            'severity_indicators': data.get('severity_indicators', {}),
            'treatment_steps'   : data.get('treatment_steps', []),
            'commune'           : data.get('commune', ''),
            'perimetre'         : data.get('perimetre', ''),
            'notes'             : data.get('description', '')
        }

        result = db.save_analysis(analysis_data, user_info=current_user)

        if result['success']:
            return jsonify({
                'success': True,
                'analysis_id': result['analysis_id'],
                'message': 'Analyse sauvegardée avec succès'
            })
        else:
            return jsonify({'error': result.get('message', 'Erreur lors de la sauvegarde')}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES POUR LES MALADIES ====================

@app.route('/api/diseases', methods=['GET'])
def get_diseases():
    """Récupère toutes les maladies avec statistiques"""
    try:
        diseases = db.get_all_diseases()
        return jsonify({'diseases': diseases})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diseases/<int:disease_id>', methods=['GET'])
def get_disease(disease_id):
    """Récupère une maladie par son ID"""
    try:
        disease = db.get_disease_by_id(disease_id)
        if disease:
            return jsonify(disease)
        return jsonify({'error': 'Maladie non trouvée'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diseases', methods=['POST'])
def add_disease():
    """Ajoute une nouvelle maladie"""
    try:
        data = request.json
        result = db.add_disease(data)
        if result['success']:
            return jsonify(result), 201
        return jsonify({'error': result['error']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diseases/<int:disease_id>', methods=['PUT'])
def update_disease(disease_id):
    """Met à jour une maladie existante"""
    try:
        data = request.json
        result = db.update_disease(disease_id, data)
        if result['success']:
            return jsonify(result)
        return jsonify({'error': result['error']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diseases/<int:disease_id>', methods=['DELETE'])
def delete_disease(disease_id):
    """Supprime une maladie"""
    try:
        result = db.delete_disease(disease_id)
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'error': result['error']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES POUR LES ALERTES ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    limit  = request.args.get('limit', 100, type=int)
    niveau = request.args.get('niveau', None)
    statut = request.args.get('statut', None)
    search = request.args.get('search', None)
    try:
        alerts = db.get_alerts(active_only=active_only, limit=limit)
        # تطبيق الفلاتر يدوياً
        if niveau:
            alerts = [a for a in alerts if a.get('niveau') == niveau]
        if statut:
            alerts = [a for a in alerts
                      if a.get('statut') == statut or a.get('status') == statut]
        if search:
            s = search.lower()
            alerts = [a for a in alerts
                      if s in (a.get('titre') or '').lower()
                      or s in (a.get('description') or '').lower()
                      or s in (a.get('commune') or '').lower()]
        return jsonify({'alerts': alerts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/count', methods=['GET'])
def get_alerts_count():
    """Récupère le nombre d'alertes actives"""
    try:
        alerts = db.get_alerts(active_only=True)
        return jsonify({'count': len(alerts)})
    except Exception as e:
        return jsonify({'error': str(e), 'count': 0}), 500
    
@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
def get_alert_detail(alert_id):
    """Récupère le détail d'une alerte par ID."""
    try:
        alerts = db.get_alerts(active_only=False, limit=10000)
        alert = next((a for a in alerts if a['id'] == alert_id), None)
        if alert:
            return jsonify(alert)
        return jsonify({'error': 'Alerte non trouvée'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Résout une alerte"""
    try:
        data = request.json or {}
        db.resolve_alert(alert_id, data.get('resolved_by'), data.get('note'))
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/stats', methods=['GET'])
def get_alerts_stats():
    """Retourne les statistiques des alertes par niveau."""
    try:
        all_alerts = db.get_alerts(active_only=False, limit=10000)
        stats = {
            'critical': sum(1 for a in all_alerts if a.get('niveau') == 'critical' and a.get('statut') == 'active'),
            'warning':  sum(1 for a in all_alerts if a.get('niveau') == 'warning'  and a.get('statut') == 'active'),
            'info':     sum(1 for a in all_alerts if a.get('niveau') == 'info'     and a.get('statut') == 'active'),
            'resolved': sum(1 for a in all_alerts if a.get('statut') in ('resolue', 'acquittee')),
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'critical': 0, 'warning': 0, 'info': 0, 'resolved': 0, 'error': str(e)}), 500
@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Crée une alerte manuelle."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    data = request.json or {}
    try:
        result = db.create_alert(data)
        if result.get('success'):
            return jsonify({'success': True, 'alert_id': result.get('alert_id')}), 201
        return jsonify({'error': result.get('error', 'Erreur')}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTE SYSTÈME EXPERT MÉTÉO ====================

@app.route('/api/expert/weather-alerts', methods=['POST'])
def get_expert_weather_alerts():
    # المصادقة اختيارية — الروت يعمل بدون token أيضاً
    data = request.json or {}
    weather = data.get('weather', {})
    farmer_cultures = data.get('cultures', [])

    if not weather:
        return jsonify({'error': 'Données météo manquantes'}), 400

    try:
        from expert_alerts import run_expert_system, get_risk_level
        alerts = run_expert_system(weather, farmer_cultures=farmer_cultures)
        risk = get_risk_level(weather)
        return jsonify({
            'success': True,
            'alerts': alerts,
            'risk_level': risk,
            'total': len(alerts)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500






@app.route('/api/plants', methods=['GET'])
def get_plants():
    """Retourne la liste des plantes supportées."""
    plants = [
        {'id': k, 'nom': k.capitalize(), 'maladie_principale': LABELS[k][0]}
        for k in MODEL_FILES.keys()
    ]
    return jsonify(plants)






# ==================== ROUTES POUR LES STATISTIQUES ====================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Récupère les statistiques globales"""
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/communes', methods=['GET'])
def get_communes():
    """Récupère la liste des communes avec leurs statistiques"""
    import sqlite3
    try:
        conn = sqlite3.connect(db.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT commune, COUNT(*) as total_cases,
                   COUNT(DISTINCT disease_name) as diseases_count
            FROM analyses
            WHERE commune != '' AND is_healthy = 0
            GROUP BY commune
            ORDER BY total_cases DESC
        ''')

        communes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({'communes': communes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES POUR LES IMAGES ====================

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Sert les images uploadées"""
    return send_from_directory(str(UPLOAD_FOLDER), filename)

# ==================== ROUTES D'EXPORT ====================

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Exporte les analyses au format CSV"""
    import csv
    from flask import Response

    try:
        analyses = db.get_all_analyses(limit=10000)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(['ID', 'Image Originale', 'Image Stockée', 'Hash Image', 'Plante',
                         'Maladie', 'Confiance (%)', 'Sévérité', 'Commune', 'Périmètre',
                         'Date', 'Description', 'Largeur Image', 'Hauteur Image'])

        for a in analyses:
            writer.writerow([
                a['id'],
                a.get('image_original_name', ''),
                a.get('image_stored_name', ''),
                a.get('image_hash', ''),
                a.get('plant_type', ''),
                a.get('disease_name', ''),
                round(a.get('confidence', 0) * 100, 2),
                a.get('severity', ''),
                a.get('commune', ''),
                a.get('perimetre', ''),
                a.get('analysis_date', ''),
                (a.get('analysis_notes') or a.get('description', ''))[:100],
                a.get('image_width', 0),
                a.get('image_height', 0)
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=analyses_export.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTE DE SANTE ====================

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé"""
    try:
        models_present, models_missing = [], []
        for key, filename in MODEL_FILES.items():
            path = os.path.join(MODELS_DIR, filename)
            (models_present if os.path.exists(path) else models_missing).append(key)

        analyses_count = len(db.get_all_analyses(limit=10000))
        stats = db.get_statistics()

        return jsonify({
            'status'          : 'ok',
            'tensorflow'      : tf.__version__,
            'keras_backend'   : 'tensorflow.keras (natif)',
            'models_present'  : models_present,
            'models_missing'  : models_missing,
            'analyses_count'  : analyses_count,
            'unique_images'   : stats.get('unique_images', 0),
            'storage_used_mb' : stats.get('storage_used_mb', 0),
            'database'        : 'SQLite - OK'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ==================== ROUTES POUR LA CARTE SANITAIRE ====================

# Coordonnées relatives (% du conteneur) pour les communes de la wilaya de Guelma
COMMUNE_POSITIONS = {
    # ── Principales communes (orthographe officielle) ──────────────────────────
    "Guelma":               {"top": 42, "left": 44},
    "Guelma-Centre":        {"top": 42, "left": 44},
    "Belkheir":             {"top": 36, "left": 55},
    "Bouchegouf":           {"top": 20, "left": 50},
    "Bouhamdane":           {"top": 48, "left": 36},
    "Oued Zenati":          {"top": 30, "left": 60},
    "Hammam Debagh":        {"top": 24, "left": 68},
    "Héliopolis":           {"top": 55, "left": 27},
    "Bouati Mahmoud":       {"top": 62, "left": 48},
    "El Fedjoudj":          {"top": 35, "left": 32},
    "Medjez Amar":          {"top": 52, "left": 60},
    "Ain Makhlouf":         {"top": 28, "left": 40},
    "Ain Larbi":            {"top": 60, "left": 38},
    "Oued Fragha":          {"top": 45, "left": 65},
    "Khezaras":             {"top": 38, "left": 70},
    "Tamlouka":             {"top": 18, "left": 62},
    "Sellaoua Announa":     {"top": 55, "left": 52},
    "Bordj Sabath":         {"top": 65, "left": 55},
    "Ain Sandel":           {"top": 70, "left": 40},
    "Djebala":              {"top": 25, "left": 55},
    "Bouhachana":           {"top": 50, "left": 42},
    "Guelaat Bou Sba":      {"top": 58, "left": 44},
    "Houari Boumediene":    {"top": 34, "left": 46},
    "Ain Ben Beida":        {"top": 44, "left": 30},
    "Dahouara":             {"top": 30, "left": 48},
    "Ben Djarah":           {"top": 58, "left": 60},
    "Ras El Agba":          {"top": 22, "left": 35},
    "Nechmaya":             {"top": 68, "left": 35},
    "Bou Hachana":          {"top": 50, "left": 42},
    "Hammam N'Bails":       {"top": 40, "left": 25},
    "Roknia":               {"top": 32, "left": 38},
    "Hammam N Bails":       {"top": 40, "left": 25},
    "Djeballah Khemissi":   {"top": 26, "left": 44},
    "Oued Cheham":          {"top": 64, "left": 30},
    "Ain Helib":            {"top": 72, "left": 50},
    "Salah Bouchaour":      {"top": 46, "left": 56},
    "Heliopolis":           {"top": 55, "left": 27},  # sans accent
    # ── Variantes avec tirets (saisies fréquentes dans les formulaires) ────────
    "belkheir":             {"top": 36, "left": 55},
    "oued-zenati":          {"top": 30, "left": 60},
    "medjez-amar":          {"top": 52, "left": 60},
    "bouhamdane":           {"top": 48, "left": 36},
    "bouchegouf":           {"top": 20, "left": 50},
    "heliopolis":           {"top": 55, "left": 27},
    "hammam-debagh":        {"top": 24, "left": 68},
    "bouati-mahmoud":       {"top": 62, "left": 48},
    "el-fedjoudj":          {"top": 35, "left": 32},
    "ain-makhlouf":         {"top": 28, "left": 40},
    "ain-larbi":            {"top": 60, "left": 38},
    "oued-fragha":          {"top": 45, "left": 65},
    "sellaoua-announa":     {"top": 55, "left": 52},
    "bordj-sabath":         {"top": 65, "left": 55},
    "ain-sandel":           {"top": 70, "left": 40},
    "guelaat-bou-sba":      {"top": 58, "left": 44},
    "houari-boumediene":    {"top": 34, "left": 46},
    "ain-ben-beida":        {"top": 44, "left": 30},
}

def get_commune_color(total_cases):
    """Retourne la classe CSS de couleur selon le nombre de cas"""
    if total_cases > 50:
        return "red"
    elif total_cases > 20:
        return "amber"
    else:
        return "green"

def get_dot_size(total_cases):
    """Retourne la taille en px du point selon le nombre de cas"""
    if total_cases > 80:
        return 22
    elif total_cases > 50:
        return 18
    elif total_cases > 30:
        return 16
    elif total_cases > 15:
        return 14
    else:
        return 12

def _normalize(name):
    """Lowercase, strip, replace hyphens/underscores with space."""
    return name.lower().strip().replace('-', ' ').replace('_', ' ')

COMMUNE_POSITIONS_NORMALIZED = {
    _normalize(k): v for k, v in COMMUNE_POSITIONS.items()
}

def get_commune_position(commune_name):
    """Trouve la position d'une commune quelle que soit sa casse ou ses séparateurs."""
    key = _normalize(commune_name)
    if key in COMMUNE_POSITIONS_NORMALIZED:
        return COMMUNE_POSITIONS_NORMALIZED[key]
    for norm_key, pos in COMMUNE_POSITIONS_NORMALIZED.items():
        if key in norm_key or norm_key in key:
            return pos
    return None

_FALLBACK_POSITIONS = [
    {"top": 40, "left": 50}, {"top": 50, "left": 55}, {"top": 35, "left": 45},
    {"top": 55, "left": 40}, {"top": 45, "left": 60}, {"top": 30, "left": 52},
    {"top": 60, "left": 50}, {"top": 38, "left": 38}, {"top": 52, "left": 48},
    {"top": 42, "left": 58}, {"top": 28, "left": 44}, {"top": 65, "left": 45},
]
_fallback_index = [0]

def get_fallback_position():
    pos = _FALLBACK_POSITIONS[_fallback_index[0] % len(_FALLBACK_POSITIONS)]
    _fallback_index[0] += 1
    return pos

@app.route('/api/carte/map-data', methods=['GET'])
def get_carte_map_data():
    """
    Retourne toutes les données nécessaires pour la carte sanitaire :
    - Points par commune (position, couleur, nombre de cas, maladie principale)
    - Classement des communes les plus touchées
    - Total de cas, évolution
    """
    import sqlite3
    try:
        conn = sqlite3.connect(db.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                commune,
                COUNT(*) as total_cases,
                COUNT(DISTINCT disease_name) as diseases_count,
                MAX(analysis_date) as last_case_date,
                GROUP_CONCAT(DISTINCT disease_name) as disease_list
            FROM analyses
            WHERE commune != '' AND commune IS NOT NULL AND is_healthy = 0
            GROUP BY commune
            ORDER BY total_cases DESC
        ''')
        commune_rows = [dict(r) for r in cursor.fetchall()]

        cursor.execute('''
            SELECT commune, disease_name, COUNT(*) as cnt
            FROM analyses
            WHERE commune != '' AND commune IS NOT NULL AND is_healthy = 0
            GROUP BY commune, disease_name
            ORDER BY commune, cnt DESC
        ''')
        commune_diseases = {}
        for row in cursor.fetchall():
            c = row['commune']
            if c not in commune_diseases:
                commune_diseases[c] = row['disease_name']

        cursor.execute("""
            SELECT COUNT(*) FROM analyses
            WHERE is_healthy = 0
            AND analysis_date >= datetime('now', '-7 days')
        """)
        cases_this_week = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT COUNT(*) FROM analyses
            WHERE is_healthy = 0
            AND analysis_date >= datetime('now', '-14 days')
            AND analysis_date < datetime('now', '-7 days')
        """)
        cases_last_week = cursor.fetchone()[0] or 1

        cursor.execute("SELECT COUNT(*) FROM analyses WHERE is_healthy = 0")
        total_cases = cursor.fetchone()[0] or 0

        conn.close()

        _fallback_index[0] = 0

        map_dots = []
        for row in commune_rows:
            commune_name = row['commune']
            pos = get_commune_position(commune_name)
            if not pos:
                pos = get_fallback_position()

            map_dots.append({
                "commune"        : commune_name,
                "total_cases"    : row['total_cases'],
                "diseases_count" : row['diseases_count'],
                "main_disease"   : commune_diseases.get(commune_name, "Maladie inconnue"),
                "last_case_date" : row['last_case_date'],
                "color"          : get_commune_color(row['total_cases']),
                "size"           : get_dot_size(row['total_cases']),
                "top"            : pos["top"],
                "left"           : pos["left"],
            })

        variation = round(((cases_this_week - cases_last_week) / cases_last_week) * 100) \
            if cases_last_week > 0 else 0

        return jsonify({
            "map_dots"         : map_dots,
            "top_communes"     : commune_rows[:10],
            "total_cases"      : total_cases,
            "weekly_variation" : variation,
            "commune_diseases" : commune_diseases,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/carte/analyses', methods=['GET'])
def get_carte_analyses():
    """
    Retourne les dernières analyses avec images pour l'affichage
    dans le panneau latéral de la carte.
    """
    limit    = request.args.get('limit', 20, type=int)
    commune  = request.args.get('commune', None)
    severity = request.args.get('severity', None)

    try:
        analyses = db.get_all_analyses(limit=limit, offset=0, commune=commune, severity=severity)

        enriched = []
        for a in analyses:
            image_url = None
            if a.get('image_stored_name'):
                image_url = f"/uploads/{a['image_stored_name']}"
            elif a.get('image_path'):
                image_url = f"/{a['image_path']}"

            enriched.append({
                "id"                 : a.get("id"),
                "plant_type"         : a.get("plant_type"),
                "disease_name"       : a.get("disease_name"),
                "scientific_name"    : a.get("scientific_name"),
                "confidence"         : a.get("confidence"),
                "severity"           : a.get("severity"),
                "commune"            : a.get("commune"),
                "perimetre"          : a.get("perimetre"),
                "analysis_date"      : a.get("analysis_date"),
                "is_healthy"         : a.get("is_healthy"),
                "image_url"          : image_url,
                "image_original_name": a.get("image_original_name"),
                "infection_rate"     : a.get("infection_rate"),
                "progression_speed"  : a.get("progression_speed"),
                "contamination_risk" : a.get("contamination_risk"),
            })

        return jsonify({"analyses": enriched, "total": len(enriched)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== ROUTES PROFIL UTILISATEUR ====================

import re as _re

def _val_email(e):
    return bool(_re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e))

def _val_username(u):
    return bool(_re.fullmatch(r"[A-Za-z0-9_]{3,30}", u))

def _val_phone(p):
    if not p:
        return True
    return bool(_re.fullmatch(r"[\d\s\+\-]{8,20}", p))


@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Retourne le profil complet de l'utilisateur connecté."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401

    user_id = current_user.get('user_id')
    if not user_id:
        return jsonify({'error': 'Token invalide : user_id manquant'}), 401

    try:
        import sqlite3 as _sqlite3
        with _sqlite3.connect(str(db.DB_PATH)) as conn:
            conn.row_factory = _sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, full_name, username, email,
                       role, commune, phone, is_active, last_login, created_at
                FROM users WHERE id = ?
            """, (user_id,))
            row = cur.fetchone()

        if not row:
            return jsonify({'error': 'Utilisateur introuvable'}), 404

        with _sqlite3.connect(str(db.DB_PATH)) as conn:
            conn.row_factory = _sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM analyses WHERE user_id = ?",
                (user_id,)
            )
            cnt_row = cur.fetchone()
            analyses_count = cnt_row['cnt'] if cnt_row else 0

        return jsonify({
            'success': True,
            'user': {
                'id'             : row['id'],
                'full_name'      : row['full_name'],
                'username'       : row['username'],
                'email'          : row['email'],
                'role'           : row['role'],
                'commune'        : row['commune'] or '',
                'phone'          : row['phone'] or '',
                'is_active'      : bool(row['is_active']),
                'last_login'     : row['last_login'],
                'created_at'     : row['created_at'],
                'analyses_count' : analyses_count,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile', methods=['PUT'])
def update_profile():
    """Met à jour le profil de l'utilisateur connecté (infos ou mot de passe)."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401

    user_id = current_user.get('user_id')
    if not user_id:
        return jsonify({'error': 'Token invalide : user_id manquant'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Corps JSON manquant ou malformé'}), 400

    updates = {}
    errors  = []

    if 'full_name' in data:
        v = (data['full_name'] or '').strip()
        if not v:
            errors.append("Le nom complet ne peut pas être vide.")
        elif len(v) > 100:
            errors.append("Le nom complet ne doit pas dépasser 100 caractères.")
        else:
            updates['full_name'] = v

    if 'username' in data:
        v = (data['username'] or '').strip()
        if not _val_username(v):
            errors.append("Nom d'utilisateur invalide (3–30 caractères alphanumériques ou underscores).")
        elif v.lower() == 'admin':
            errors.append("Le nom d'utilisateur 'admin' est réservé.")
        else:
            updates['username'] = v

    if 'email' in data:
        v = (data['email'] or '').strip().lower()
        if not _val_email(v):
            errors.append("L'adresse e-mail est invalide.")
        else:
            updates['email'] = v

    if 'phone' in data:
        v = (data['phone'] or '').strip()
        if not _val_phone(v):
            errors.append("Le numéro de téléphone est invalide.")
        else:
            updates['phone'] = v

    if 'commune' in data:
        v = (data['commune'] or '').strip()
        if len(v) > 100:
            errors.append("Le nom de commune ne doit pas dépasser 100 caractères.")
        else:
            updates['commune'] = v

    current_password = data.get('current_password', '')
    new_password     = data.get('new_password', '')
    change_password  = bool(current_password or new_password)

    if change_password:
        if not current_password:
            errors.append("Le mot de passe actuel est requis.")
        elif not new_password:
            errors.append("Le nouveau mot de passe ne peut pas être vide.")
        elif len(new_password) < 8:
            errors.append("Le nouveau mot de passe doit contenir au moins 8 caractères.")

    if errors:
        return jsonify({'error': '; '.join(errors)}), 400

    if not updates and not change_password:
        return jsonify({'error': 'Aucune donnée à mettre à jour.'}), 400

    try:
        import sqlite3 as _sqlite3
        with _sqlite3.connect(str(db.DB_PATH)) as conn:
            conn.row_factory = _sqlite3.Row
            cur = conn.cursor()

            cur.execute(
                "SELECT id, username, email, password_hash FROM users WHERE id = ?",
                (user_id,)
            )
            existing = cur.fetchone()
            if not existing:
                return jsonify({'error': 'Utilisateur introuvable'}), 404

            if 'username' in updates:
                cur.execute(
                    "SELECT id FROM users WHERE username = ? AND id != ?",
                    (updates['username'], user_id)
                )
                if cur.fetchone():
                    return jsonify({'error': "Ce nom d'utilisateur est déjà utilisé."}), 409

            if 'email' in updates:
                cur.execute(
                    "SELECT id FROM users WHERE email = ? AND id != ?",
                    (updates['email'], user_id)
                )
                if cur.fetchone():
                    return jsonify({'error': "Cette adresse e-mail est déjà utilisée."}), 409

            if change_password:
                current_hash = hashlib.sha256(current_password.encode('utf-8')).hexdigest()
                if current_hash != existing['password_hash']:
                    return jsonify({'error': 'Le mot de passe actuel est incorrect.'}), 400
                updates['password_hash'] = hashlib.sha256(new_password.encode('utf-8')).hexdigest()

            updates['updated_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            set_clause = ', '.join(f"{col} = ?" for col in updates)
            values     = list(updates.values()) + [user_id]
            cur.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            conn.commit()

        with _sqlite3.connect(str(db.DB_PATH)) as conn:
            conn.row_factory = _sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, full_name, username, email,
                       role, commune, phone, is_active, last_login, created_at
                FROM users WHERE id = ?
            """, (user_id,))
            row = cur.fetchone()

        only_pwd = change_password and not (set(updates.keys()) - {'password_hash', 'updated_at'})
        msg = 'Mot de passe mis à jour.' if only_pwd else 'Profil mis à jour avec succès.'

        return jsonify({
            'success': True,
            'message': msg,
            'user': {
                'id'         : row['id'],
                'full_name'  : row['full_name'],
                'username'   : row['username'],
                'email'      : row['email'],
                'role'       : row['role'],
                'commune'    : row['commune'] or '',
                'phone'      : row['phone'] or '',
                'is_active'  : bool(row['is_active']),
                'last_login' : row['last_login'],
                'created_at' : row['created_at'],
            }
        })
    except Exception as e:
        return jsonify({'error': f'Erreur serveur : {str(e)}'}), 500


# ==================== ROUTES ADMIN — GESTION UTILISATEURS ====================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Retourne tous les utilisateurs (admin uniquement)."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    if current_user.get('role') != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
    try:
        users = db.get_all_users(requesting_user=current_user)
        with __import__('sqlite3').connect(str(db.DB_PATH)) as conn:
            conn.row_factory = __import__('sqlite3').Row
            cur = conn.cursor()
            cur.execute("""
                SELECT user_id, COUNT(*) as cnt
                FROM analyses
                WHERE user_id IS NOT NULL
                GROUP BY user_id
            """)
            counts = {row['user_id']: row['cnt'] for row in cur.fetchall()}
        for u in users:
            u['analyses_count'] = counts.get(u['id'], 0)
        return jsonify({'users': users, 'total': len(users)})
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_route(user_id):
    """Met à jour un utilisateur (rôle, statut actif)."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    data = request.json
    if not data:
        return jsonify({'error': 'Corps JSON manquant'}), 400
    try:
        result = db.update_user(user_id, data, requesting_user=current_user)
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'error': result.get('error', 'Échec')}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    """Supprime un utilisateur (admin uniquement)."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    try:
        result = db.delete_user(user_id, requesting_user=current_user)
        if result['success']:
            return jsonify({'success': True, 'message': 'Utilisateur supprimé'})
        return jsonify({'error': result.get('error', 'Échec')}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/create-user', methods=['POST'])
def admin_create_user():
    """Crée un utilisateur avec un rôle quelconque (admin uniquement)."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    if current_user.get('role') != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
    data = request.json
    if not data:
        return jsonify({'error': 'Corps JSON manquant'}), 400
    role = data.get('role', 'farmer')
    if role not in db.ROLES:
        return jsonify({'error': f"Rôle invalide : {role}"}), 400
    result = db.create_user(
        full_name=data.get('full_name', ''),
        username=data.get('username', ''),
        email=data.get('email', ''),
        password=data.get('password', ''),
        role=role,
        commune=data.get('commune', ''),
        phone=data.get('phone', ''),
    )
    if result['success']:
        return jsonify({'success': True, 'user_id': result['user_id']})
    return jsonify({'success': False, 'error': result.get('error', 'Erreur')}), 400


@app.route('/api/admin/analyses', methods=['GET'])
def get_admin_analyses():
    """Retourne uniquement les analyses partagées avec l'admin."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    if current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin requis'}), 403
    limit  = request.args.get('limit', 500, type=int)
    offset = request.args.get('offset', 0, type=int)
    try:
        analyses = db.get_all_analyses(limit=limit, offset=offset, requesting_user=current_user)
        shared = [a for a in analyses if a.get('shared_with_admin')]
        return jsonify({'analyses': shared, 'total': len(shared)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Corps JSON manquant'}), 400
    if (data.get('username') or '').strip().lower() == 'admin':
        return jsonify({'success': False, 'error': "Le nom d'utilisateur 'admin' est réservé"}), 400
    result = db.create_user(
        full_name=data.get('full_name'),
        username=data.get('username'),
        email=data.get('email'),
        password=data.get('password'),
        role='farmer',
        commune=data.get('commune')
    )
    if result['success']:
        return jsonify({'success': True, 'user_id': result['user_id']})
    return jsonify({'success': False, 'error': result['error']}), 400


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'Corps JSON manquant'}), 400

    username_or_email = (data.get('username_or_email') or '').strip()
    password = data.get('password', '')

    if not username_or_email or not password:
        return jsonify({'success': False, 'error': 'Identifiants manquants'}), 400

    # ── 1. Vérification admin hardcodé (temporaire) ───────────────────────────
    if (username_or_email.lower() == HARDCODED_ADMIN['username'] and
            password == HARDCODED_ADMIN['password']):
        user = HARDCODED_ADMIN['user']
        token = make_token(user['id'], user['role'])
        return jsonify({'success': True, 'user': user, 'token': token})

    # ── 2. Authentification via base de données ────────────────────────────────
    user = db.authenticate_user(username_or_email, password)
    if user:
        token = make_token(user['id'], user.get('role', 'farmer'))
        return jsonify({'success': True, 'user': user, 'token': token})
    return jsonify({'success': False, 'error': 'Identifiants invalides'}), 401


@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Vérifie la validité du token JWT (appelé par auth.js en arrière-plan)."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'valid': False}), 401
    token = auth_header[7:]
    try:
        import jwt as _jwt
        _jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({'valid': True})
    except Exception:
        return jsonify({'valid': False}), 401

# ==================== ROUTE RACINE ====================

@app.route('/', methods=['GET'])
def root():
    """Route racine"""
    return jsonify({
        'name'     : 'PhytoSentinel API',
        'version'  : '1.0.0',
        'status'   : 'running',
        'endpoints': [
            '/upload-image',
            '/api/analyses',
            '/api/analyses/<id>',
            '/api/analyses/<id>/share',
            '/api/save-analysis',
            '/api/diseases',
            '/api/diseases/<id>',
            '/api/alerts',
            '/api/alerts/count',
            '/api/alerts/<id>/resolve',
            '/api/expert/weather-alerts',
            '/api/statistics',
            '/api/communes',
            '/api/export/csv',
            '/api/carte/map-data',
            '/api/carte/analyses',
            '/api/profile',
            '/api/users',
            '/api/users/<id>',
            '/api/admin/create-user',
            '/api/admin/analyses',
            '/api/auth/register',
            '/api/auth/login',
            '/api/auth/verify',
            '/health',
            
        ]
    })

# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("  PhytoSentinel Backend — Flask + TensorFlow (Version Production)")
    print(f"  TensorFlow version: {tf.__version__}")
    print("  Keras: tensorflow.keras (natif)")
    print("  Base de données: SQLite optimisée")
    print(f"  Dossier uploads: {UPLOAD_FOLDER}")
    print("  Accès API: http://localhost:5000")
    print("  Santé: http://localhost:5000/health")
    print("=" * 60)

    missing = [f for f in MODEL_FILES.values()
               if not os.path.exists(os.path.join(MODELS_DIR, f))]
    if missing:
        print(f"\n Modèles manquants dans '{MODELS_DIR}/':")
        for m in missing:
            print(f"   - {m}")
    else:
        print(f"\n Tous les modèles sont présents dans '{MODELS_DIR}/'")

    print(f"\n Base de données: {db.DB_PATH}")
    print("\n Démarrage du serveur...\n")

    app.run(debug=False, host='0.0.0.0', port=5000)