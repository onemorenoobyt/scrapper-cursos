# Contenido de database.py
import sqlite3
from datetime import datetime

DB_NAME = "cursos_sepe.db"

def setup_database():
    """Crea la tabla de cursos si no existe (sin la columna 'sede')."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        centro_formacion TEXT,
        nombre_curso TEXT,
        url_curso TEXT UNIQUE,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        horario TEXT,
        horas INTEGER,
        last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def insert_curso(curso_data):
    """Inserta o actualiza un curso en la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO cursos (centro_formacion, nombre_curso, url_curso, fecha_inicio, fecha_fin, horario, horas)
    VALUES (:centro, :nombre, :url, :inicio, :fin, :horario, :horas)
    ON CONFLICT(url_curso) DO UPDATE SET
        fecha_inicio=excluded.fecha_inicio,
        fecha_fin=excluded.fecha_fin,
        horario=excluded.horario,
        horas=excluded.horas,
        last_scraped=CURRENT_TIMESTAMP
    """, curso_data)
    conn.commit()
    conn.close()