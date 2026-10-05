# ════════════════════════════════════════════════════════════════════
# ROUTES ADMIN — À AJOUTER DANS app.py (avant le bloc if __name__)
# ════════════════════════════════════════════════════════════════════
# Collez ce bloc dans app.py, juste avant la dernière ligne :
#   if __name__ == '__main__':
# ════════════════════════════════════════════════════════════════════

# ── Helper : vérifie que le token appartient à un admin ─────────────
def require_admin():
    """
    Retourne le payload JWT si l'utilisateur est admin, sinon None.
    Gère aussi le compte admin hardcodé (id=0, role='admin').
    """
    user = get_current_user()
    if not user:
        return None
    if user.get('role') != 'admin':
        return None
    return user


# ── GET /api/users ──────────────────────────────────────────────────
@app.route('/api/users', methods=['GET'])
def list_users():
    """
    Retourne tous les utilisateurs (admin uniquement).
    Query params optionnels : role=farmer|admin|expert|technician
    """
    admin = require_admin()
    if not admin:
        return jsonify({'error': 'Accès réservé à l'administrateur'}), 403

    role_filter = request.args.get('role', None)
    try:
        users = db.get_all_users(requesting_user=admin, role_filter=role_filter)
        return jsonify({'users': users})
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── PUT /api/users/<id> ──────────────────────────────────────────────
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_route(user_id):
    """
    Met à jour un utilisateur (admin ou le farmer lui-même).
    Champs autorisés pour l'admin : full_name, email, commune, phone, role, is_active
    """
    current = get_current_user()
    if not current:
        return jsonify({'error': 'Non authentifié'}), 401

    data = request.json or {}
    try:
        result = db.update_user(user_id, data, requesting_user=current)
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'error': result['error']}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── DELETE /api/users/<id> ───────────────────────────────────────────
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    """Supprime un utilisateur (admin uniquement)."""
    admin = require_admin()
    if not admin:
        return jsonify({'error': 'Accès réservé à l'administrateur'}), 403

    try:
        result = db.delete_user(user_id, requesting_user=admin)
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'error': result['error']}), 400
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── POST /api/admin/create-user ──────────────────────────────────────
@app.route('/api/admin/create-user', methods=['POST'])
def admin_create_user():
    """
    Crée un compte avec n'importe quel rôle (admin, expert, technician, farmer).
    Réservé à l'administrateur.
    """
    admin = require_admin()
    if not admin:
        return jsonify({'error': 'Accès réservé à l'administrateur'}), 403

    data = request.json or {}
    role = data.get('role', 'farmer')

    if role not in db.ROLES:
        return jsonify({'success': False, 'error': f'Rôle invalide : {role}'}), 400

    # Bloquer la création d'un second compte "admin" hardcodé
    if (data.get('username', '') or '').strip().lower() == 'admin':
        return jsonify({'success': False, 'error': "Le nom 'admin' est réservé"}), 400

    result = db.create_user(
        full_name=data.get('full_name'),
        username=data.get('username'),
        email=data.get('email'),
        password=data.get('password'),
        role=role,
        commune=data.get('commune'),
        phone=data.get('phone'),
    )

    if result['success']:
        return jsonify({'success': True, 'user_id': result['user_id']}), 201
    return jsonify({'success': False, 'error': result['error']}), 400


# ── GET /api/analyses (mise à jour : enrichir avec le nom du farmer) ─
# NOTE : La route /api/analyses existante retourne déjà les données via
# db.get_all_analyses(). Pour ajouter le nom du farmer (farmer_name),
# il suffit de modifier get_all_analyses dans database.py pour joindre
# la table users. Voici le patch SQL à ajouter dans database.py :
#
#   Dans get_all_analyses(), remplacer :
#     SELECT a.*
#   par :
#     SELECT a.*, u.full_name AS farmer_name, u.username AS farmer_username
#     FROM analyses a
#     LEFT JOIN users u ON a.user_id = u.id
#
# Cette modification est rétrocompatible (les champs farmer_name et
# farmer_username s'ajoutent sans casser l'existant).