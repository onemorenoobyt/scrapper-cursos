# Contenido de main.py (VERSIÓN RESILIENTE FINAL)
import pandas as pd
import sqlite3
import database
import sys
from datetime import datetime
from scrapers import (
    afsformacion_scraper,
    auraformacion_scraper,
    cep_scraper,
    focan_scraper,
    grupolincea_scraper,
    icse_scraper,
    inpsi_scraper,
    insforca_scraper,
    microsistemas_scraper,
    formacionline_scraper
)

def main():
    """Función principal del programa de scraping."""
    scrape_start_time = datetime.now() # Guardamos la hora de inicio
    print(f"--- INICIANDO PROCESO DE SCRAPING a las {scrape_start_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    database.setup_database()
    
    todos_los_cursos = []
    
    scrapers_disponibles = {
        "afs": afsformacion_scraper,
        "aura": auraformacion_scraper,
        "cep": cep_scraper,
        "focan": focan_scraper,
        "lincea": grupolincea_scraper,
        "icse": icse_scraper,
        "inpsi": inpsi_scraper,
        "insforca": insforca_scraper,
        "microsistemas": microsistemas_scraper,
        "formacionline": formacionline_scraper
    }
    
    scraper_a_ejecutar_nombre = None
    if len(sys.argv) > 1:
        scraper_a_ejecutar_nombre = sys.argv[1]

    if scraper_a_ejecutar_nombre:
        print(f"--- MODO DEPURACIÓN: Ejecutando únicamente el scraper '{scraper_a_ejecutar_nombre}' ---")
        scraper_module = scrapers_disponibles.get(scraper_a_ejecutar_nombre)
        if scraper_module:
            scrapers_a_ejecutar = [scraper_module]
        else:
            print(f"---! ERROR: El scraper '{scraper_a_ejecutar_nombre}' no existe. Scrapers disponibles: {list(scrapers_disponibles.keys())} !---")
            return
    else:
        print("--- MODO NORMAL: Ejecutando todos los scrapers ---")
        scrapers_a_ejecutar = list(scrapers_disponibles.values())
    
    successful_centers = set()

    for scraper_module in scrapers_a_ejecutar:
        cursos_del_scraper = []
        try:
            print(f"\n>>> Ejecutando: {scraper_module.__name__}")
            cursos_del_scraper = scraper_module.scrape()
            todos_los_cursos.extend(cursos_del_scraper)
            
            # Si el scraper finaliza y ha encontrado al menos un curso, lo consideramos un éxito.
            if cursos_del_scraper:
                # El nombre del centro se obtiene del primer curso encontrado
                center_name = cursos_del_scraper[0]['centro']
                successful_centers.add(center_name)
        except Exception as e:
            print(f"---! ERROR CRÍTICO en el scraper {scraper_module.__name__}: {e} !---")

    print(f"\nProceso de scraping finalizado. Total de cursos nuevos/actualizados: {len(todos_los_cursos)}")
    
    if todos_los_cursos:
        print("Insertando y actualizando datos en la base de datos...")
        for curso in todos_los_cursos:
            database.insert_curso(curso)
        print("Datos insertados correctamente.")
    
    # --- LÓGICA DE PURGA INTELIGENTE ---
    # Solo se purgan los cursos de los centros que han sido scrapeados con éxito.
    # Si un scraper falla, sus datos antiguos se conservan.
    if not scraper_a_ejecutar_nombre: # Solo purgar en modo normal, no en depuración
        print("\nIniciando purga de cursos antiguos de los centros scrapeados con éxito...")
        database.purge_old_courses_by_center(successful_centers, scrape_start_time)
    
    print("\nExportando resultados a CSV...")
    conn = sqlite3.connect(database.DB_NAME)
    df = pd.read_sql_query("SELECT * FROM cursos ORDER BY fecha_inicio DESC", conn)
    conn.close()

    if not df.empty:
        df.to_csv("cursos_actualizados.csv", index=False)
        print("Exportación finalizada. Revisa el fichero 'cursos_actualizados.csv'")
    else:
        print("No se encontraron cursos para exportar a CSV.")

    print("--- PROCESO COMPLETADO ---")

if __name__ == '__main__':
    main()