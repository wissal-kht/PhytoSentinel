"""
PhytoSentinel — Moteur de Génération d'Alertes (Système Expert)
Génère des alertes intelligentes basées sur des règles métier.
PAS de machine learning — logique basée sur des seuils agronomiques.
"""

from database import query


# ============================================================
# RÈGLES MÉTIER — SEUILS GLOBAUX
# ============================================================

SEUIL_HUMIDITE_CRITIQUE  = 90   # %  → alerte critique immédiate
SEUIL_HUMIDITE_WARNING   = 80   # %  → avertissement
SEUIL_TEMP_GEL           = 2    # °C → risque de gel
SEUIL_TEMP_CANICULE      = 38   # °C → stress thermique sévère
SEUIL_VENT_FORT          = 50   # km/h → transport de spores

# Niveau de risque (0-100) → niveau d'alerte
RISQUE_CRITIQUE = 75
RISQUE_WARNING  = 50
RISQUE_INFO     = 25


def generate_alerts(weather: dict) -> int:
    """
    Point d'entrée principal du moteur.
    Analyse la météo, compare aux profils des plantes et génère les alertes.
    
    Args:
        weather: dict avec temperature, humidity, wind_speed
    
    Returns:
        Nombre d'alertes créées
    """
    temp     = weather.get("temperature", 20)
    humidity = weather.get("humidity", 60)
    wind     = weather.get("wind_speed", 10)

    created = 0

    # 1. Alertes météo globales (indépendantes des plantes)
    created += _check_global_weather(temp, humidity, wind)

    # 2. Alertes par plante (règles spécifiques)
    plantes = query("SELECT * FROM plantes WHERE actif = 1")
    for plante in plantes:
        created += _check_plant_risk(plante, temp, humidity, wind)

    print(f"[Alertes] ✅ {created} nouvelle(s) alerte(s) générée(s)")
    return created


# ============================================================
# RÈGLES GLOBALES
# ============================================================

def _check_global_weather(temp: float, humidity: float, wind: float) -> int:
    """Vérifie les conditions météo globalement dangereuses."""
    created = 0

    # Règle 1: Humidité critique (toutes cultures confondues)
    if humidity >= SEUIL_HUMIDITE_CRITIQUE:
        if not _alert_exists("humidity_critical"):
            _create_alert(
                titre="Humidité Critique — Toutes Cultures",
                description=f"Humidité atmosphérique de {humidity}% — Niveau extrêmement favorable au développement de champignons et moisissures sur l'ensemble des cultures.",
                type_alerte="critical",
                niveau="critical",
                commune="Guelma (Wilaya)",
                temperature=temp, humidity=humidity, wind_speed=wind,
                risque=95,
                action="Traitement fongicide préventif immédiat sur toutes les parcelles sensibles. Réduire l'irrigation foliaire.",
                tag="humidity_critical"
            )
            created += 1

    elif humidity >= SEUIL_HUMIDITE_WARNING:
        if not _alert_exists("humidity_warning"):
            _create_alert(
                titre="Humidité Élevée — Surveillance Renforcée",
                description=f"Humidité de {humidity}% — Conditions propices aux maladies fongiques. Vigilance recommandée.",
                type_alerte="weather",
                niveau="warning",
                commune="Guelma (Wilaya)",
                temperature=temp, humidity=humidity, wind_speed=wind,
                risque=65,
                action="Surveiller les premiers symptômes sur les feuilles. Éviter les irrigations en soirée.",
                tag="humidity_warning"
            )
            created += 1

    # Règle 2: Vent fort (transport de spores)
    if wind >= SEUIL_VENT_FORT:
        if not _alert_exists("wind_strong"):
            _create_alert(
                titre="Vent Fort — Risque de Propagation",
                description=f"Vent à {wind} km/h — Conditions favorables au transport de spores fongiques entre parcelles.",
                type_alerte="weather",
                niveau="warning",
                commune="Guelma (Wilaya)",
                temperature=temp, humidity=humidity, wind_speed=wind,
                risque=60,
                action="Éviter les traitements par pulvérisation. Surveiller la propagation inter-parcellaire.",
                tag="wind_strong"
            )
            created += 1

    # Règle 3: Risque de gel
    if temp <= SEUIL_TEMP_GEL:
        if not _alert_exists("frost_risk"):
            _create_alert(
                titre="Risque de Gel — Protection Immédiate",
                description=f"Température de {temp}°C — Risque de gel sur les cultures sensibles et les jeunes pousses.",
                type_alerte="critical",
                niveau="critical",
                commune="Guelma (Wilaya)",
                temperature=temp, humidity=humidity, wind_speed=wind,
                risque=90,
                action="Mettre en place les protections anti-gel. Arrosage antigel sur fraisiers et vignes. Surveiller les serres.",
                tag="frost_risk"
            )
            created += 1

    # Règle 4: Canicule
    if temp >= SEUIL_TEMP_CANICULE:
        if not _alert_exists("heat_stress"):
            _create_alert(
                titre="Stress Thermique Sévère — Canicule",
                description=f"Température de {temp}°C — Stress hydrique et thermique sur l'ensemble des cultures. Réduction de la photosynthèse.",
                type_alerte="weather",
                niveau="warning",
                commune="Guelma (Wilaya)",
                temperature=temp, humidity=humidity, wind_speed=wind,
                risque=70,
                action="Irrigation en début de matinée uniquement. Installer des ombrières sur cultures fragiles. Surveiller le flétrissement.",
                tag="heat_stress"
            )
            created += 1

    return created


# ============================================================
# RÈGLES PAR PLANTE
# ============================================================

def _check_plant_risk(plante: dict, temp: float, humidity: float, wind: float) -> int:
    """
    Applique les règles de risque spécifiques à une plante.
    Calcule un score de risque 0-100 et génère l'alerte appropriée.
    """
    nom          = plante["nom"]
    t_min        = plante["temperature_min"]
    t_max        = plante["temperature_max"]
    h_max        = plante["humidity_max"]
    maladie      = plante["maladie_principale"]
    pathogene    = plante["pathogene"]
    traitement   = plante["traitement_recommande"]
    plante_id    = plante["id"]

    # --- Calcul du score de risque ---
    risque = 0

    # Humidité au-dessus du seuil → +40 points de risque
    if humidity > h_max:
        depassement = humidity - h_max
        risque += min(40, int(depassement * 2))

    # Température dans la zone de danger optimale pour la maladie
    if t_min <= temp <= t_max:
        # Zone idéale pour la plante = aussi idéale pour le pathogène
        risque += 35
    elif (t_min - 5) <= temp <= (t_max + 5):
        # Zone légèrement hors optimum
        risque += 15

    # Vent favorise la dispersion des spores
    if wind >= 30:
        risque += 15
    elif wind >= 15:
        risque += 8

    # Plafond à 100
    risque = min(risque, 100)

    # --- Décision selon le score ---
    if risque < RISQUE_INFO:
        # Conditions normales → alerte info si pas déjà présente aujourd'hui
        return 0  # On évite de spammer les alertes "tout va bien"

    tag = f"plant_{plante_id}_risk"
    if _alert_exists(tag):
        return 0  # Alerte déjà active pour cette plante

    if risque >= RISQUE_CRITIQUE:
        niveau      = "critical"
        type_alerte = "critical"
        badge       = "CRITIQUE"
        action = (
            f"Appliquer {traitement} immédiatement. "
            f"Inspecter toutes les parcelles de {nom.lower()} sous 24h. "
            f"Signaler les foyers confirmés à la DSA."
        )
    elif risque >= RISQUE_WARNING:
        niveau      = "warning"
        type_alerte = "risk"
        badge       = "AVERTISSEMENT"
        action = (
            f"Traitement préventif avec {traitement.split('—')[0].strip()} recommandé. "
            f"Inspecter les feuilles basses et les zones humides."
        )
    else:
        niveau      = "info"
        type_alerte = "inspection"
        badge       = "SURVEILLANCE"
        action = (
            f"Inspection visuelle conseillée. "
            f"Traitement préventif léger envisageable avec {traitement.split('—')[0].strip()}."
        )

    description = (
        f"Température {temp}°C (optimal {t_min}-{t_max}°C), Humidité {humidity}% "
        f"(seuil: {h_max}%). Score de risque: {risque}%. "
        f"Pathogène ciblé: {pathogene}."
    )

    _create_alert(
        titre=f"{maladie} — {nom} (Risque {risque}%)",
        description=description,
        type_alerte=type_alerte,
        niveau=niveau,
        plante_id=plante_id,
        commune="Guelma (Wilaya)",
        temperature=temp, humidity=humidity, wind_speed=wind,
        risque=risque,
        action=action,
        tag=tag
    )
    return 1


# ============================================================
# HELPERS INTERNES
# ============================================================

def _alert_exists(tag: str) -> bool:
    """
    Vérifie si une alerte avec ce tag est déjà active aujourd'hui.
    Évite la duplication lors des rafraîchissements répétés.
    """
    row = query(
        """SELECT id FROM alertes
           WHERE generee_par = %s
             AND statut = 'active'
             AND DATE(created_at) = CURDATE()
           LIMIT 1""",
        (tag,),
        fetch="one"
    )
    return row is not None


def _create_alert(titre, description, type_alerte, niveau, commune="Guelma",
                  temperature=None, humidity=None, wind_speed=None,
                  risque=0, action=None, tag="auto", plante_id=None):
    """Insère une alerte en base de données."""
    query(
        """INSERT INTO alertes
           (titre, description, type_alerte, niveau, plante_id, commune,
            temperature, humidity, wind_speed, risque_pourcent,
            statut, source, action_recommandee, generee_par)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active','auto',%s,%s)""",
        (titre, description, type_alerte, niveau, plante_id, commune,
         temperature, humidity, wind_speed, risque, action, tag),
        fetch="none"
    )
