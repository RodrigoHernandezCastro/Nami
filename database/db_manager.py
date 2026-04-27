import sqlite3
import json
from contextlib import contextmanager
from typing import Optional, List, Tuple

DB_PATH = "datos_bot.db"

@contextmanager
def obtener_conexion():
    """Context manager para manejar conexiones de forma segura."""
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    except Exception as e:
        conexion.rollback()
        raise e
    finally:
        conexion.close()


def inicializar_db():
    """Crea todas las tablas necesarias si no existen."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        # Tabla: configuración por servidor (guild)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guilds_config (
                guild_id        INTEGER PRIMARY KEY,
                canal_anuncios  INTEGER,
                rol_mencion     INTEGER,
                premium         INTEGER DEFAULT 0,
                limite_streamers INTEGER DEFAULT 5,
                fecha_registro  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla: streamers monitoreados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streamers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id        INTEGER NOT NULL,
                nombre_streamer TEXT NOT NULL,
                mensaje_custom  TEXT DEFAULT '¡Ya está en vivo!',
                tipo_mencion    TEXT DEFAULT 'ninguno',
                rol_mencion_id  INTEGER,
                esta_online     INTEGER DEFAULT 0,
                ultima_revision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_agregado  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, nombre_streamer),
                FOREIGN KEY (guild_id) REFERENCES guilds_config(guild_id) ON DELETE CASCADE
            )
        ''')

        # Índices para acelerar consultas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_streamer_nombre ON streamers(nombre_streamer)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guild_id ON streamers(guild_id)')


# ============================================================
# FUNCIONES PARA GUILDS (SERVIDORES)
# ============================================================

def registrar_guild(guild_id: int, canal_anuncios: int = None):
    with obtener_conexion() as conn:
        if canal_anuncios is None:
            conn.execute('''
                INSERT OR IGNORE INTO guilds_config (guild_id) VALUES (?)
            ''', (guild_id,))
        else:
            conn.execute('''
                INSERT INTO guilds_config (guild_id, canal_anuncios)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET canal_anuncios = excluded.canal_anuncios
            ''', (guild_id, canal_anuncios))


def obtener_canal_anuncios(guild_id: int) -> Optional[int]:
    """Devuelve el canal configurado para anunciar streams."""
    with obtener_conexion() as conn:
        row = conn.execute(
            'SELECT canal_anuncios FROM guilds_config WHERE guild_id = ?',
            (guild_id,)
        ).fetchone()
        return row['canal_anuncios'] if row else None


def obtener_limite_streamers(guild_id: int) -> int:
    """Devuelve el límite de streamers para un servidor."""
    with obtener_conexion() as conn:
        row = conn.execute(
            'SELECT limite_streamers FROM guilds_config WHERE guild_id = ?',
            (guild_id,)
        ).fetchone()
        return row['limite_streamers'] if row else 5


def establecer_premium(guild_id: int, premium: bool, nuevo_limite: int = 20):
    """Marca un servidor como premium y actualiza su límite."""
    with obtener_conexion() as conn:
        conn.execute('''
            UPDATE guilds_config 
            SET premium = ?, limite_streamers = ?
            WHERE guild_id = ?
        ''', (int(premium), nuevo_limite, guild_id))

def contar_streamers_total() -> int:
    """Cuenta TODOS los streamers de TODOS los servidores."""
    with obtener_conexion() as conn:
        return conn.execute("SELECT COUNT(*) FROM streamers").fetchone()[0]


def eliminar_guild(guild_id: int) -> None:
    """Elimina un servidor y todos sus datos (cascade)."""
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM guilds_config WHERE guild_id = ?", (guild_id,))


def obtener_streamers_por_guild(guild_id: int):
    """Devuelve todos los streamers de un servidor específico."""
    with obtener_conexion() as conn:
        rows = conn.execute('''
            SELECT id, nombre_streamer, mensaje_custom, esta_online,
                   tipo_mencion, rol_mencion_id
            FROM streamers
            WHERE guild_id = ?
            ORDER BY nombre_streamer
        ''', (guild_id,)).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["rol_mencion_id"] = _deserializar_roles(d["rol_mencion_id"])
        result.append(d)
    return result

# ============================================================
# FUNCIONES PARA STREAMERS
# ============================================================

def agregar_streamer(guild_id: int, nombre_streamer: str, mensaje: str,
                     tipo_mencion: str = 'ninguno', rol_mencion_id = None) -> bool:
    # Serializar lista de roles a JSON; si es None o int legado, dejarlo como está
    if isinstance(rol_mencion_id, list):
        rol_mencion_id = json.dumps(rol_mencion_id)
    try:
        with obtener_conexion() as conn:
            conn.execute('''
                INSERT INTO streamers (guild_id, nombre_streamer, mensaje_custom, tipo_mencion, rol_mencion_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (guild_id, nombre_streamer.lower(), mensaje, tipo_mencion, rol_mencion_id))
        return True
    except sqlite3.IntegrityError:
        return False


def _deserializar_roles(valor):
    """Convierte el valor almacenado en DB a lista de IDs (o None)."""
    if valor is None:
        return None
    if isinstance(valor, int):
        return [valor]
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else [parsed]
    except (TypeError, ValueError):
        return None

def eliminar_streamer(guild_id: int, nombre_streamer: str) -> bool:
    """Quita un streamer del monitoreo."""
    with obtener_conexion() as conn:
        cursor = conn.execute('''
            DELETE FROM streamers 
            WHERE guild_id = ? AND nombre_streamer = ?
        ''', (guild_id, nombre_streamer.lower()))
        return cursor.rowcount > 0


def contar_streamers_guild(guild_id: int) -> int:
    """Cuenta cuántos streamers tiene un servidor."""
    with obtener_conexion() as conn:
        row = conn.execute(
            'SELECT COUNT(*) as total FROM streamers WHERE guild_id = ?',
            (guild_id,)
        ).fetchone()
        return row['total']


def listar_streamers_guild(guild_id: int) -> List[sqlite3.Row]:
    """Devuelve todos los streamers de un servidor."""
    with obtener_conexion() as conn:
        return conn.execute('''
            SELECT nombre_streamer, mensaje_custom, esta_online 
            FROM streamers WHERE guild_id = ?
        ''', (guild_id,)).fetchall()


def obtener_todos_streamers() -> List[dict]:
    with obtener_conexion() as conn:
        rows = conn.execute('''
            SELECT s.id, s.guild_id, s.nombre_streamer, s.mensaje_custom,
                   s.esta_online, s.tipo_mencion, s.rol_mencion_id,
                   g.canal_anuncios
            FROM streamers s
            JOIN guilds_config g ON s.guild_id = g.guild_id
            WHERE g.canal_anuncios IS NOT NULL
        ''').fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["rol_mencion_id"] = _deserializar_roles(d["rol_mencion_id"])
        result.append(d)
    return result


def actualizar_estado_stream(streamer_id: int, en_vivo: bool) -> None:
    with obtener_conexion() as conn:
        conn.execute('''
            UPDATE streamers 
            SET esta_online = ?, ultima_revision = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (1 if en_vivo else 0, streamer_id))