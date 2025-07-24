# Contenido de database.py (VERSIÓN CON PURGA INTELIGENTE)
import sqlite3
from datetime import datetime

DB_NAME = "cursos_sepe.db"

def setup_database():
    """Crea la tabla de cursos si no existe, con una clave única compuesta."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        centro_formacion TEXT,
        nombre_curso TEXT,
        url_curso TEXT,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        horario TEXT,
        horas INTEGER,
        last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(centro_formacion, nombre_curso)
    )
    """)
    conn.commit()
    conn.close()

def insert_curso(curso_data):
    """Inserta o actualiza un curso en la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Actualizamos la marca de tiempo en cada inserción/actualización
    curso_data['last_scraped'] = datetime.now()
    cursor.execute("""
    INSERT INTO cursos (centro_formacion, nombre_curso, url_curso, fecha_inicio, fecha_fin, horario, horas, last_scraped)
    VALUES (:centro, :nombre, :url, :inicio, :fin, :horario, :horas, :last_scraped)
    ON CONFLICT(centro_formacion, nombre_curso) DO UPDATE SET
        url_curso=excluded.url_curso,
        fecha_inicio=excluded.fecha_inicio,
        fecha_fin=excluded.fecha_fin,
        horario=excluded.horario,
        horas=excluded.horas,
        last_scraped=excluded.last_scraped
    """, curso_data)
    conn.commit()
    conn.close()

def purge_old_courses_by_center(successful_centers, scrape_start_time):
    """
    Elimina cursos antiguos SOLO de los centros que fueron scrapeados con éxito.
    Un curso se considera 'antiguo' si su 'last_scraped' es anterior al inicio de esta ejecución.
    """
    if not successful_centers:
        print("--- PURGA OMITIDA: Ningún scraper tuvo éxito. ---")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    time_threshold = scrape_start_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Creamos una cadena de placeholders (?, ?, ?) para la consulta SQL
    placeholders = ', '.join('?' for center in successful_centers)
    query = f"DELETE FROM cursos WHERE centro_formacion IN ({placeholders}) AND last_scraped < ?"
    
    # Los parámetros deben ser una tupla o lista
    params = list(successful_centers)
    params.append(time_threshold)
    
    cursor.execute(query, params)
    
    deleted_rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted_rows > 0:
        print(f"--- PURGA COMPLETADA: Se han eliminado {deleted_rows} cursos antiguos de los centros exitosos. ---")
    else:
        print("--- PURGA COMPLETADA: No se encontraron cursos antiguos para eliminar. ---")