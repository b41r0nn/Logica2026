import sqlite3
from datetime import datetime


def _connect(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        conn.execute('PRAGMA busy_timeout=30000')
        conn.execute('PRAGMA journal_mode=WAL')
    except sqlite3.OperationalError:
        # Si la DB está bloqueada momentáneamente, continuamos con la conexión.
        pass
    return conn


def init_db(db_path):
    """Crea la tabla de logs si no existe."""
    with _connect(db_path) as conn:
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha     TEXT NOT NULL,
                    hora      TEXT NOT NULL,
                    modulo    TEXT NOT NULL,
                    archivo   TEXT NOT NULL,
                    tamano_kb REAL NOT NULL,
                    resultado TEXT NOT NULL,
                    detalle   TEXT
                )
            ''')
            conn.commit()
        except sqlite3.OperationalError as e:
            if 'locked' not in str(e).lower():
                raise


def registrar_log(db_path, modulo, archivo, tamano_bytes, resultado, detalle=None):
    """Inserta un registro en la tabla de logs."""
    now = datetime.now()
    with _connect(db_path) as conn:
        conn.execute(
            '''INSERT INTO logs (fecha, hora, modulo, archivo, tamano_kb, resultado, detalle)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                modulo,
                archivo,
                round(tamano_bytes / 1024, 2),
                resultado,
                detalle,
            )
        )
        conn.commit()


def obtener_logs(db_path, limit=200):
    """Retorna los últimos N logs para consulta interna."""
    with _connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT * FROM logs ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
