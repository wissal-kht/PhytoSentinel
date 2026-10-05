"""
PhytoSentinel — Backend Flask Principal
API REST pour le système d'alertes agricoles DSA Guelma
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from database import query
from weather_service import fetch_weather, get_latest_weather
from alert_engine import generate_alerts

app = Flask(__name__)
CORS(app)  # Autorise les requêtes depuis le frontend HTML

# ============================================================
# ROUTE: Santé du service
# ============================================================

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "PhytoSentinel Alertes", "timestamp": datetime.now().isoformat()})


# ============================================================
# ROUTES: Météo
# ============================================================

@app.route("/api/weather")
def get_weather():
    """Retourne les dernières données météo depuis la BDD."""
    data = get_latest_weather()
    if not data:
        return jsonify({"error": "Aucune donnée météo disponible"}), 404
    # Convertir les champs datetime en string
    if data.get("fetched_at"):
        data["fetched_at"] = data["fetched_at"].isoformat()
    return jsonify(data)


@app.route("/api/weather/refresh", methods=["POST"])
def refresh_weather():
    """Force une mise à jour des données météo depuis OpenWeatherMap."""
    data = fetch_weather()
    return jsonify({"success": True, "data": data})


# ============================================================
# ROUTES: Alertes
# ============================================================

@app.route("/api/alerts")
def get_alerts():
    """
    Retourne la liste des alertes avec filtres optionnels.
    Query params: niveau, statut, plante_id, search
    """
    niveau    = request.args.get("niveau")
    statut    = request.args.get("statut", "active")  # Par défaut: alertes actives
    plante_id = request.args.get("plante_id")
    search    = request.args.get("search", "").strip()

    # Construction dynamique de la requête
    conditions = []
    params = []

    if statut and statut != "all":
        conditions.append("a.statut = %s")
        params.append(statut)

    if niveau and niveau != "all":
        conditions.append("a.niveau = %s")
        params.append(niveau)

    if plante_id:
        conditions.append("a.plante_id = %s")
        params.append(plante_id)

    if search:
        conditions.append("(a.titre LIKE %s OR a.description LIKE %s OR a.commune LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
        SELECT 
            a.*,
            p.nom AS plante_nom,
            p.maladie_principale
        FROM alertes a
        LEFT JOIN plantes p ON a.plante_id = p.id
        {where}
        ORDER BY 
            FIELD(a.niveau, 'critical', 'warning', 'info', 'success'),
            a.created_at DESC
        LIMIT 100
    """

    alerts = query(sql, tuple(params) if params else None)

    # Sérialiser les datetimes
    for a in alerts:
        for field in ["created_at", "updated_at"]:
            if a.get(field):
                a[field] = a[field].isoformat()

    return jsonify(alerts)


@app.route("/api/alerts/<int:alert_id>")
def get_alert_detail(alert_id):
    """Retourne le détail d'une alerte avec les infos de la plante."""
    alert = query(
        """SELECT a.*, p.nom AS plante_nom, p.nom_scientifique, 
                  p.maladie_principale, p.pathogene, p.traitement_recommande
           FROM alertes a
           LEFT JOIN plantes p ON a.plante_id = p.id
           WHERE a.id = %s""",
        (alert_id,), fetch="one"
    )
    if not alert:
        return jsonify({"error": "Alerte introuvable"}), 404

    for field in ["created_at", "updated_at"]:
        if alert.get(field):
            alert[field] = alert[field].isoformat()

    return jsonify(alert)


@app.route("/api/alerts", methods=["POST"])
def create_alert():
    """Crée une alerte manuellement."""
    data = request.get_json()

    # Validation minimale
    if not data.get("titre"):
        return jsonify({"error": "Le titre est obligatoire"}), 400

    # Récupérer les données météo actuelles pour enrichir l'alerte
    weather = get_latest_weather() or {}

    new_id = query(
        """INSERT INTO alertes
           (titre, description, type_alerte, niveau, plante_id, commune,
            temperature, humidity, wind_speed, risque_pourcent,
            statut, source, action_recommandee, generee_par)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active','manuel',%s,%s)""",
        (
            data.get("titre"),
            data.get("description", ""),
            data.get("type_alerte", "info"),
            data.get("niveau", "info"),
            data.get("plante_id") or None,
            data.get("commune", "Guelma"),
            weather.get("temperature"),
            weather.get("humidity"),
            weather.get("wind_speed"),
            data.get("risque_pourcent", 0),
            data.get("action_recommandee", ""),
            "Manuel — " + data.get("auteur", "Inspecteur DSA"),
        ),
        fetch="none"
    )
    return jsonify({"success": True, "id": new_id}), 201


@app.route("/api/alerts/<int:alert_id>/status", methods=["PATCH"])
def update_alert_status(alert_id):
    """Met à jour le statut d'une alerte (acquitter / résoudre)."""
    data   = request.get_json()
    statut = data.get("statut")

    if statut not in ("active", "acquittee", "resolue"):
        return jsonify({"error": "Statut invalide"}), 400

    query(
        "UPDATE alertes SET statut = %s WHERE id = %s",
        (statut, alert_id),
        fetch="none"
    )
    return jsonify({"success": True, "id": alert_id, "statut": statut})


@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
def delete_alert(alert_id):
    """Supprime une alerte (admin uniquement)."""
    query("DELETE FROM alertes WHERE id = %s", (alert_id,), fetch="none")
    return jsonify({"success": True})


# ============================================================
# ROUTE: Génération automatique
# ============================================================

@app.route("/api/alerts/generate", methods=["POST"])
def auto_generate():
    """
    Lance le moteur de génération d'alertes.
    Récupère la météo et applique toutes les règles métier.
    """
    weather = fetch_weather()
    count   = generate_alerts(weather)
    return jsonify({
        "success": True,
        "alerts_created": count,
        "weather_used": weather,
    })


# ============================================================
# ROUTE: Statistiques
# ============================================================

@app.route("/api/alerts/stats")
def get_stats():
    """Retourne les compteurs pour le tableau de bord."""
    stats = query("""
        SELECT
            SUM(niveau = 'critical' AND statut = 'active')  AS critical,
            SUM(niveau = 'warning'  AND statut = 'active')  AS warning,
            SUM(niveau = 'info'     AND statut = 'active')  AS info,
            SUM(statut = 'resolue')                          AS resolved,
            COUNT(*)                                         AS total
        FROM alertes
    """, fetch="one")

    # Convertir None en 0
    return jsonify({k: int(v or 0) for k, v in stats.items()})


# ============================================================
# ROUTE: Plantes (pour le formulaire)
# ============================================================

@app.route("/api/plants")
def get_plants():
    """Retourne la liste des plantes supportées."""
    plants = query("SELECT id, nom, maladie_principale FROM plantes WHERE actif = 1 ORDER BY nom")
    return jsonify(plants)


# ============================================================
# DÉMARRAGE
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print(" PhytoSentinel — Serveur Flask")
    print(" DSA Guelma — Système d'Alertes")
    print("=" * 50)
    # Lancer une génération initiale au démarrage
    try:
        weather = fetch_weather()
        generate_alerts(weather)
    except Exception as e:
        print(f"[Init] Avertissement: {e}")
    app.run(debug=True, host="0.0.0.0", port=5000)
