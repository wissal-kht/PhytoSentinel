"""
PhytoSentinel — Connexion à la base de données MySQL
Utilise mysql-connector-python avec pool de connexions
"""

import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

# Configuration de la connexion
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "phytosentinel"),
    "charset":  "utf8mb4",
    "autocommit": True,
}

# Pool de connexions (évite d'ouvrir/fermer à chaque requête)
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="phyto_pool",
        pool_size=5,
        **DB_CONFIG
    )
    print("[DB] ✅ Pool de connexions MySQL initialisé")
except Exception as e:
    print(f"[DB] ❌ Erreur d'initialisation du pool: {e}")
    connection_pool = None


def get_connection():
    """Retourne une connexion depuis le pool."""
    if connection_pool:
        return connection_pool.get_connection()
    # Fallback: connexion directe
    return mysql.connector.connect(**DB_CONFIG)


def query(sql: str, params: tuple = None, fetch: str = "all"):
    """
    Exécute une requête SQL.
    
    Args:
        sql:    Requête SQL (utiliser %s comme placeholder)
        params: Tuple de paramètres
        fetch:  'all' | 'one' | 'none'
    
    Returns:
        Liste de dicts (fetch='all'), dict (fetch='one'), ou lastrowid (fetch='none')
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if fetch == "all":
            return cursor.fetchall()
        elif fetch == "one":
            return cursor.fetchone()
        else:
            return cursor.lastrowid
    except Exception as e:
        print(f"[DB] Erreur requête: {e}\nSQL: {sql}")
        raise
    finally:
        cursor.close()
        conn.close()
